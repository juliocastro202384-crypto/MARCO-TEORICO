# app.py -- Constructor de Marco Teorico v5.8.0
# Parches: P-CRITICO, P-1, P-2, P-3, P-4, P-5

import io
import re
import html
import math
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st
import anthropic
from docx import Document
from rapidfuzz import fuzz

ANIO_ACTUAL    = datetime.now().year
ANIO_INICIO    = ANIO_ACTUAL - 5
RANGO          = f"{ANIO_INICIO}-{ANIO_ACTUAL}"

OPENALEX         = "https://api.openalex.org"
CROSSREF         = "https://api.crossref.org"
S2               = "https://api.semanticscholar.org/graph/v1"
CROSSREF_WORKERS = 8
S2_FIELDS = ("title,year,venue,abstract,url,authors,citationCount,externalIds,publicationTypes")

st.set_page_config(
    page_title="Constructor de Marco Teorico - Claude",
    page_icon=":classical_building:",
    layout="wide",
)

CSS = """
<style>
  html, body, [class*="css"] { font-family: Georgia, serif; }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f6f0 0%, #eef2f7 100%);
    border-right: 2px solid #2563eb;
  }
  .main-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #3b82f6 100%);
    color: white; padding: 2rem 2.5rem; border-radius: 12px;
    margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(37,99,235,0.3);
  }
  .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
  .badge-row { display: flex; gap: 8px; margin-top: 0.8rem; flex-wrap: wrap; }
  .badge {
    background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4);
    color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
  }
  .info-box { background: #eff6ff; border-left: 4px solid #2563eb; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .warning-box { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .result-container { background: #fafafa; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.5rem; margin-top: 1rem; }
  .stButton > button { background: linear-gradient(135deg, #1e3a5f, #2563eb); color: white; border: none; border-radius: 8px; padding: 0.6rem 1.2rem; font-weight: 600; width: 100%; }
  footer { color: #9ca3af; font-size: 0.8rem; text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

_GENERIC_TERMS = {"the","and","for","that","this","with","from","como","para","que","los","las","del","una","por"}

def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower().strip())

def _relevance_score(text: str, term: str) -> float:
    tn = norm(term)
    if not tn or tn in _GENERIC_TERMS or len(tn) < 5:
        return 0.0
    words = text.split()
    if not words:
        return 0.0
    hits = sum(1 for w in words if tn in w)
    if hits == 0:
        return 0.0
    tf = hits / len(words)
    length_penalty = min(len(words) / 50.0, 1.0)
    return min(tf * length_penalty * 10, 1.0)

def is_header_like(p: str) -> bool:
    parts = p.split("\n")
    if len(parts) > 2:
        return False
    first = parts[0].strip()
    if re.match(r"^#{1,4}\s", first):
        return True
    if first == first.upper() and first != first.lower() and len(first) <= 80:
        return True
    if re.match(r"^(\d{1,2}|[IVX]{1,4})[.)]\s+[A-Z]", first) and len(first) <= 80:
        return True
    if first.endswith(":") and len(first) <= 60:
        return True
    return False

def is_valid_doi(doi: str) -> bool:
    if not doi:
        return False
    d = doi.strip().lower()
    return d.startswith("10.") and "/" in d

@st.cache_data(ttl=3600, show_spinner=False)
def crossref_ok(doi: str) -> bool:
    try:
        r = requests.get(f"{CROSSREF}/works/{doi.strip()}", timeout=8, headers={"User-Agent": "MarcoTeoricoApp/5.8"})
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=3600, show_spinner=False)
def openalex_search(query: str, variables: str, year_from: int) -> List[Dict]:
    try:
        params = {
            "search": f"{query} {variables}",
            "filter": f"from_publication_date:{year_from}-01-01,is_paratext:false",
            "per-page": 10,
            "select": "id,doi,title,publication_year,authorships,primary_location,open_access,abstract_inverted_index,primary_topic",
        }
        r = requests.get(f"{OPENALEX}/works", params=params, timeout=10, headers={"User-Agent": "MarcoTeoricoApp/5.8"})
        if r.status_code != 200:
            return []
        results = []
        for w in r.json().get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            authors = [a["author"]["display_name"] for a in w.get("authorships", [])[:3] if a.get("author")]
            loc = w.get("primary_location") or {}
            venue = (loc.get("source") or {}).get("display_name", "")
            inv = w.get("abstract_inverted_index") or {}
            abstract = ""
            if inv:
                pos = sorted((p, wd) for wd, pl in inv.items() for p in pl)
                abstract = " ".join(wd for _, wd in pos[:80])
            results.append({"id": f"OA_{len(results)+1}", "source": "OpenAlex", "title": w.get("title",""),
                "year": w.get("publication_year"), "authors": authors, "venue": venue,
                "doi": doi, "abstract": abstract, "open_access": (w.get("open_access") or {}).get("is_oa", False),
                "verified_by": [], "quality_flags": {}})
        return results
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def s2_search(query: str, variables: str) -> List[Dict]:
    try:
        r = requests.get(f"{S2}/paper/search", params={"query": f"{query} {variables}", "limit": 8, "fields": S2_FIELDS}, timeout=10)
        if r.status_code != 200:
            return []
        results = []
        for p in r.json().get("data", []):
            doi = (p.get("externalIds") or {}).get("DOI", "")
            authors = [a.get("name","") for a in p.get("authors",[])[:3]]
            results.append({"id": f"S2_{len(results)+1}", "source": "SemanticScholar",
                "title": p.get("title",""), "year": p.get("year"), "authors": authors,
                "venue": p.get("venue",""), "doi": doi, "abstract": (p.get("abstract") or "")[:500],
                "open_access": False, "verified_by": [], "quality_flags": {}})
        return results
    except Exception:
        return []

def verify_records_concurrent(records: List[Dict], progress_bar=None) -> List[Dict]:
    doi_seen: set = set()
    unique_records: List[Dict] = []
    no_doi: List[Dict] = []
    for r in records:
        doi = (r.get("doi") or "").lower().strip()
        if doi and doi not in doi_seen:
            doi_seen.add(doi)
            unique_records.append(r)
        elif not doi:
            no_doi.append(r)
    all_to_check = unique_records + no_doi
    total = len(all_to_check)
    done = 0
    verified = []
    def _check(rec: Dict) -> Tuple[bool, Dict]:
        doi = rec.get("doi")
        ok = bool(doi and is_valid_doi(doi) and crossref_ok(doi))
        rec["verified_by"] = ["Crossref"] if ok else []
        rec["quality_flags"]["has_doi"] = bool(doi)
        rec["quality_flags"]["has_venue"] = bool(rec.get("venue"))
        rec["quality_flags"]["has_year"] = bool(rec.get("year"))
        rec["quality_flags"]["has_authors"] = bool(rec.get("authors"))
        rec["quality_flags"]["has_abstract"] = bool(rec.get("abstract"))
        return ok, rec
    with ThreadPoolExecutor(max_workers=CROSSREF_WORKERS) as pool:
        futures = {pool.submit(_check, rec): rec for rec in all_to_check}
        for future in as_completed(futures):
            done += 1
            if progress_bar:
                progress_bar.progress(min(done / max(total, 1), 1.0))
            try:
                ok, rec = future.result()
                if ok:
                    verified.append(rec)
            except Exception:
                pass
    return verified

def dedup_records(records: List[Dict]) -> List[Dict]:
    seen_doi: set = set()
    seen_title: set = set()
    out = []
    for r in records:
        doi = (r.get("doi") or "").lower().strip()
        tn = norm(r.get("title") or "")
        if doi and doi in seen_doi:
            continue
        if any(fuzz.ratio(tn, t) > 88 for t in seen_title):
            continue
        if doi:
            seen_doi.add(doi)
        if tn:
            seen_title.add(tn)
        out.append(r)
    return out

def generar_docx(texto: str) -> io.BytesIO:
    doc = Document()
    doc.add_heading("Marco Teorico", 0)
    for linea in texto.split("\n"):
        s = linea.strip()
        if not s:
            continue
        if re.match(r"^#{1,2}\s", s):
            doc.add_heading(re.sub(r"^#+\s+", "", s), level=1 if s.startswith("# ") else 2)
        elif re.match(r"^(I{1,3}|IV|V?I{0,3}|IX|X)\. \S", s, re.I):
            doc.add_heading(s, level=1)
        elif re.match(r"^\d{1,2}\. [A-Z]", s):
            doc.add_heading(s, level=2)
        else:
            doc.add_paragraph(s)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

SYSTEM_PROMPT = (
    "AGENTE: CONSTRUCTOR DE MARCO TEORICO v5.8\n"
    "Eres un AGENTE ACADEMICO DE ALTO RIGOR.\n\n"
    "0. DECISION DE MODO\n- Gate global cumplido: Si/No\n- Modo: MODO A o MODO B\n\n"
    "I. GATE GLOBAL\n- FALTA suficiencia en 1 variable -> MODO A\n- TODAS cumplen -> MODO B\n\n"
    "II. SUFICIENCIA MINIMA\n"
    "VERIFICADA: Autor+Anio+Titulo+Revista. Min: 2 conceptual, 1 teorico, 2 empiricos.\n"
    "Scholar sin DOI -> NO verificada.\n\n"
    "III. MODO A (5 secciones)\n"
    "S1: DECISION DE MODO\nS2: VACIOS\nS3: SEMILLAS\nS4: CONSULTAS\nS5: PLANTILLA\n"
    "ULTIMA LINEA MODO A: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.\n"
    "PROHIBIDO MODO A: definiciones, sintesis, antecedentes narrativos.\n\n"
    "IV. MODO B (14 secciones)\n"
    "0-Decision / 1-Ficha / 2-Ruta / 3-Inventario / 4-Calidad / 5-Indice\n"
    "6-Desarrollo / 7-Fundamento / 8-Antecedentes / 9-Operacionalizacion\n"
    "10-Vacios / 11-Riesgos / 12-Cobertura / 13-Referencias / 14-Pendientes\n\n"
    "V. REGLAS ABSOLUTAS\n"
    "PROHIBIDO inventar autores, anios, titulos, revistas, DOI.\n"
    "SOLO citar fuentes en <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.\n\n"
    "VI. APA 7 - Citas narrativas/parenteticas. No inventar paginas.\n"
    f"NOTA: Rango empirico: {RANGO}. Teorias clasicas: sin restriccion."
)

with st.sidebar:
    st.markdown("## Constructor de Marco Teorico")
    st.markdown("**v5.8.0 - Claude - OpenAlex + S2 + Crossref**")
    st.markdown("---")
    try:
        _key_hint = "Cargada desde st.secrets" if "ANTHROPIC_API_KEY" in st.secrets else "sk-ant-api03-..."
    except Exception:
        _key_hint = "sk-ant-api03-..."
    api_key = st.text_input("API Key Anthropic", type="password", placeholder=_key_hint)
    modo = st.selectbox("Modo de operacion",
        ["AUTOMATICO (Gate global decide)", "FORZAR MODO A - DIAGNOSTICO", "FORZAR MODO B - REDACCION"])
    st.markdown("---")
    st.markdown("### Datos del Estudio")
    titulo = st.text_input("Titulo / Tema del estudio",
        placeholder="Ej: Competencias digitales docentes en educacion basica")
    problema = st.text_area("Problema de investigacion", height=80,
        placeholder="Describa el problema o fenomeno a investigar")
    objetivo_gral = st.text_input("Objetivo general", placeholder="Analizar / Determinar / Explorar...")
    _ph_obj = "1. Identificar..." + "\n" + "2. Describir..." + "\n" + "3. Analizar..."
    obj_esp = st.text_area("OBJETIVOS ESPECIFICOS (uno por linea)", height=100, placeholder=_ph_obj)
    preguntas = st.text_area("Preguntas de investigacion", height=70,
        placeholder="Cual es...? / Como...? / Que relacion...?")
    variables_cats = st.text_area("Variables / Categorias", height=70,
        placeholder="Variable 1: ... / Categoria 1: ...")
    ruta = st.selectbox("Ruta metodologica",
        ["Cuantitativa", "Cualitativa", "Mixta", "Por determinar"])
    poblacion = st.text_input("Poblacion / Muestra / Contexto",
        placeholder="Ej: 120 docentes, nivel primaria, Mexico")
    st.markdown("---")
    st.markdown("### Fuentes")
    fuentes_pegadas = st.text_area("Fuentes pegadas manualmente", height=150,
        placeholder="Autor (Anio). Titulo. Revista. DOI / Extracto...")
    st.markdown("---")
    st.markdown("### Parametros")
    documento = st.selectbox("Tipo de documento",
        ["Tesis de maestria", "Tesis doctoral", "Articulo cientifico", "TFM", "Trabajo de pregrado"])
    norma = st.selectbox("Norma de citacion", ["APA 7", "APA 6", "MLA", "Chicago"])
    area = st.text_input("Area disciplinar", placeholder="Educacion, Psicologia, Administracion...")
    pais = st.text_input("Pais / Contexto geografico", placeholder="Mexico, Colombia, Espania...")
    st.markdown("---")
    buscar_fuentes = st.checkbox("Buscar fuentes automaticamente (OpenAlex + S2)", value=True)
    st.caption(f"Rango empirico: {RANGO} | Teorias clasicas: sin restriccion")

generar = st.button("GENERAR MARCO TEORICO")

st.markdown('''<div class="main-header"><h1>Constructor de Marco Teorico</h1>
<p>Rigor academico - Gate de evidencia - Rutas metodologicas - APA 7</p>
<div class="badge-row">
<span class="badge">Claude Opus</span><span class="badge">OpenAlex</span>
<span class="badge">SemanticScholar</span><span class="badge">v5.8.0</span>
</div></div>''', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="info-box"><b>Gate global</b><br>2 modos: Diagnostico o Redaccion Final.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="info-box"><b>Verificacion automatica</b><br>OpenAlex + S2 + Crossref.</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="info-box"><b>Paquete tecnico</b><br>Consultas para 4 bases listas.</div>', unsafe_allow_html=True)
st.markdown('<div class="warning-box"><b>Gate:</b> FALTA suficiencia -> MODO A. TODAS cumplen -> MODO B.</div>', unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic en el panel izquierdo.")
    elif not titulo and not variables_cats:
        st.error("Ingresa al menos el titulo/tema y las variables/categorias.")
    else:
        if "FORZAR MODO A" in modo:
            modo_instruccion = "FORZAR MODO A - DIAGNOSTICO DOCUMENTAL"
        elif "FORZAR MODO B" in modo:
            modo_instruccion = "FORZAR MODO B - REDACCION ACADEMICA FINAL"
        else:
            modo_instruccion = "AUTOMATICO - ejecuta Gate global segun suficiencia real"
        fuentes_auto_bloque = ""
        if buscar_fuentes and (titulo or variables_cats):
            with st.spinner("Buscando fuentes en OpenAlex y SemanticScholar..."):
                pb = st.progress(0)
                oa_r = openalex_search(titulo or variables_cats, variables_cats, ANIO_INICIO)
                pb.progress(0.4)
                s2_r = s2_search(titulo or variables_cats, variables_cats)
                pb.progress(0.7)
                all_raw = oa_r + s2_r
                all_dedup = dedup_records(all_raw)
                verified = verify_records_concurrent(all_dedup, progress_bar=pb)
                pb.progress(1.0)
                if all_dedup:
                    lineas = []
                    for r in all_dedup[:12]:
                        authors_str = "; ".join(r.get("authors") or [])
                        v_tag = "VERIFICADA" if r in verified else "NO_VERIFICADA"
                        lineas.append(f"[ID={r['id']}|Base={r['source']}|Autor={authors_str}|Anio={r.get('year','')}|Titulo={r.get('title','')}|Revista={r.get('venue','')}|DOI={r.get('doi') or 'sin-doi'}|Verificacion={v_tag}|Extracto={r.get('abstract','')[:200]}]")
                    fuentes_auto_bloque = "\n<<<FUENTES_AUTOMATICAS>>>\n" + "\n".join(lineas) + "\n<<<FIN_FUENTES_AUTOMATICAS>>>"
                    st.success(f"Fuentes: {len(all_dedup)} encontradas, {len(verified)} verificadas.")
        fuentes_bloque = ""
        if fuentes_pegadas.strip():
            fuentes_bloque = "\n<<<FUENTES_PEGADAS>>>\n" + fuentes_pegadas.strip() + "\n<<<FIN_FUENTES_PEGADAS>>>"
        mensaje_usuario = (
            f"Genera el marco teorico:\nTITULO: {titulo}\nPROBLEMA: {problema}\n"
            f"OBJETIVO GENERAL: {objetivo_gral}\nOBJETIVOS ESPECIFICOS:\n{obj_esp}\n"
            f"PREGUNTAS: {preguntas}\nVARIABLES: {variables_cats}\nRUTA: {ruta}\n"
            f"POBLACION: {poblacion}\nDOCUMENTO: {documento}\nNORMA: {norma}\n"
            f"AREA: {area}\nPAIS: {pais}\nMODO: {modo_instruccion}\n"
            f"{fuentes_auto_bloque}\n{fuentes_bloque}\n"
            "INSTRUCCIONES CRITICAS:\n1. Primera seccion: DECISION DE MODO.\n"
            "2. Gate Global ANTES de redactar.\n"
            "3. Gate falla -> MODO A (5 secciones). Ultima linea: REINYECTAR FUENTES_RECUPERADAS.\n"
            "4. MODO A: PROHIBIDO definiciones, sintesis, antecedentes narrativos.\n"
            "5. Gate pasa -> MODO B (14 secciones).\n"
            "6. Sin metadatos = [FUENTE CANDIDATA A VERIFICAR]."
        )
        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Ejecutando gate de evidencia..."):
                result_area = st.empty()
                full_response = ""
                escaped_response = ""
                with client.messages.stream(
                    model="claude-opus-4-5", max_tokens=8000, system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": mensaje_usuario}],
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        escaped_response += html.escape(text)
                        result_area.markdown(f"<div class='result-container'>{escaped_response}</div>", unsafe_allow_html=True)
            st.success("Analisis completado.")
            docx_buf = generar_docx(full_response)
            nombre_archivo = f"marco_teorico_{titulo[:30].replace(' ', '_') if titulo else 'estudio'}.docx"
            st.download_button(label="Descargar Resultado (.docx)", data=docx_buf,
                file_name=nombre_archivo, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except anthropic.AuthenticationError:
            st.error("API Key invalida. Verifica en console.anthropic.com")
        except anthropic.RateLimitError:
            st.error("Limite de uso alcanzado. Intenta en unos minutos.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(f'''<footer>Powered by Claude v5.8.0 | OpenAlex + S2 + Crossref | Rango: {RANGO} | Gate activo</footer>''', unsafe_allow_html=True)
