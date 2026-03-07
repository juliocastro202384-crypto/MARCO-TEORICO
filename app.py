# app.py -- Constructor de Marco Teorico v6.0.0 (P-6: MODO B lenguaje doctoral)
# Sidebar reestructurado: 6 secciones + boton Recuperar separado

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

ANIO_ACTUAL = datetime.now().year
ANIO_INICIO = ANIO_ACTUAL - 5
RANGO = f"{ANIO_INICIO}-{ANIO_ACTUAL}"
OPENALEX = "https://api.openalex.org"
CROSSREF = "https://api.crossref.org"
S2 = "https://api.semanticscholar.org/graph/v1"
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
        [data-testid="stSidebar"] label { color: #374151; font-weight: 600; font-size: 0.85rem; }
        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #3b82f6 100%);
                color: white; padding: 2rem 2.5rem; border-radius: 12px;
                    margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(37,99,235,0.3);
                    }
                    .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
                    .main-header p { margin: 0.5rem 0 0; opacity: 0.9; font-size: 0.95rem; }
                    .badge-row { display: flex; gap: 8px; margin-top: 0.8rem; flex-wrap: wrap; }
                    .badge {
                        background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4);
                            color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
                            }
                            .info-box {
                                background: #eff6ff; border-left: 4px solid #2563eb;
                                    padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
                                    }
                                    .warning-box {
                                        background: #fffbeb; border-left: 4px solid #f59e0b;
                                            padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
                                            }
                                            .result-container {
                                                background: #fafafa; border: 1px solid #e5e7eb; border-radius: 10px;
                                                    padding: 1.5rem; margin-top: 1rem; white-space: pre-wrap;
                                                    }
                                                    .stButton > button {
                                                        background: linear-gradient(135deg, #1e3a5f, #2563eb);
                                                            color: white; border: none; border-radius: 8px;
                                                                padding: 0.6rem 1.2rem; font-weight: 600; width: 100%;
                                                                }
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
                    r = requests.get(f"{CROSSREF}/works/{doi.strip()}", timeout=8,
                                                              headers={"User-Agent": "MarcoTeoricoApp/6.0"})
                    return r.status_code == 200
except Exception:
        return False

@st.cache_data(ttl=3600, show_spinner=False)
def openalex_search(query: str, variables: str, year_from: int, max_results: int = 10) -> List[Dict]:
        try:
                    params = {
                                    "search": f"{query} {variables}",
                                    "filter": f"from_publication_date:{year_from}-01-01,is_paratext:false",
                                    "per-page": max_results,
                                    "select": "id,doi,title,publication_year,authorships,primary_location,open_access,abstract_inverted_index,primary_topic",
                    }
                    r = requests.get(f"{OPENALEX}/works", params=params, timeout=10,
                                     headers={"User-Agent": "MarcoTeoricoApp/6.0"})
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
                                        results.append({
                                                            "id": f"OA_{len(results)+1}", "source": "OpenAlex",
                                                            "title": w.get("title",""), "year": w.get("publication_year"),
                                                            "authors": authors, "venue": venue, "doi": doi,
                                                            "abstract": abstract,
                                                            "open_access": (w.get("open_access") or {}).get("is_oa", False),
                                                            "verified_by": [], "quality_flags": {}
                                        })
        return results
except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def s2_search(query: str, variables: str, max_results: int = 8) -> List[Dict]:
        try:
                    r = requests.get(f"{S2}/paper/search",
                                                              params={"query": f"{query} {variables}", "limit": max_results, "fields": S2_FIELDS},
                                                              timeout=10)
                    if r.status_code != 200:
                                    return []
                                results = []
                    for p in r.json().get("data", []):
                                    doi = (p.get("externalIds") or {}).get("DOI", "")
                                    authors = [a.get("name","") for a in p.get("authors",[])[:3]]
                                    results.append({
                                        "id": f"S2_{len(results)+1}", "source": "SemanticScholar",
                                        "title": p.get("title",""), "year": p.get("year"),
                                        "authors": authors, "venue": p.get("venue",""), "doi": doi,
                                        "abstract": (p.get("abstract") or "")[:500],
                                        "open_access": False, "verified_by": [], "quality_flags": {}
                                    })
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

# =================================================== P-6: SYSTEM_PROMPT con MODO B doctoral
SYSTEM_PROMPT = (
        "AGENTE: CONSTRUCTOR DE MARCO TEORICO v6.0 (P-6)\n"
        "Eres un AGENTE ACADEMICO DE ALTO RIGOR DOCTORAL.\n\n"

        "0. DECISION DE MODO\n"
        "- Gate global cumplido: Si/No\n"
        "- Modo activado: MODO A o MODO B\n\n"

        "I. GATE GLOBAL\n"
        "- FALTA suficiencia en 1 variable -> MODO A\n"
        "- TODAS cumplen -> MODO B\n\n"

        "II. SUFICIENCIA MINIMA\n"
        "VERIFICADA: Autor+Anio+Titulo+Revista. Min: 2 conceptual, 1 teorico, 2 empiricos.\n"
        "Scholar sin DOI -> NO verificada.\n\n"

        "III. MODO A (5 secciones)\n"
        "S1: DECISION DE MODO\nS2: VACIOS\nS3: SEMILLAS\nS4: CONSULTAS\nS5: PLANTILLA\n"
        "ULTIMA LINEA MODO A: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.\n"
        "PROHIBIDO MODO A: definiciones, sintesis, antecedentes narrativos.\n\n"

        "IV. MODO B - REDACCION DOCTORAL (14 secciones)\n"
        "Activa MODO B unicamente cuando el Gate Global esta cumplido.\n"
        "En MODO B redactas con LENGUAJE DOCTORAL: prosa densa, argumentacion epistemica,\n"
        "integracion teorica, precision conceptual, subordinacion logica de parrafos.\n\n"

        "ESTRUCTURA MODO B:\n"
        "S0: DECISION DE MODO - indica Gate cumplido y fuentes usadas\n"
    "S1: FICHA BIBLIOMETRICA - tabla sintetica de fuentes con autor, anio, tipo, verificacion\n"
        "S2: RUTA EPISTEMICA - justificacion del enfoque teorico-metodologico en prosa doctoral\n"
        "S3: INVENTARIO CONCEPTUAL - definiciones operacionales de VI/VD con debate teorico\n"
        "S4: CALIDAD DE EVIDENCIA - evaluacion critica del corpus: fortalezas, limitaciones, sesgos\n"
    "S5: INDICE PROPUESTO - estructura numerada del marco teorico con titulos de seccion\n"
        "S6: DESARROLLO DEL MARCO - redaccion academica completa, parrafos con citas APA 7,\n"
        "     uso de conectores epistemicos: 'desde la perspectiva de', 'en consonancia con',\n"
        "     'los hallazgos de X (anio) corroboran', 'esta evidencia converge con', etc.\n"
        "S7: FUNDAMENTO TEORICO - teorias, modelos y marcos conceptuales de base con autores clave\n"
        "S8: ANTECEDENTES EMPIRICOS - estudios previos ordenados cronologicamente con sintesis critica\n"
        "S9: OPERACIONALIZACION - definicion operacional de variables con dimensiones e indicadores\n"
        "S10: VACIOS Y CONTRIBUCION - brechas identificadas y aporte especifico del estudio\n"
        "S11: RIESGOS METODOLOGICOS - amenazas a validez interna/externa y estrategias de mitigacion\n"
        "S12: COBERTURA TEMATICA - mapa de cobertura: temas cubiertos vs pendientes\n"
        "S13: REFERENCIAS APA 7 - listado completo ordenado alfabeticamente, formato estricto APA 7\n"
        "S14: PENDIENTES - acciones recomendadas para fortalecer el marco\n\n"

        "V. NORMAS DE ESCRITURA DOCTORAL (MODO B)\n"
        "- Parrafos de minimo 5 oraciones con argumento central + evidencia + interpretacion\n"
        "- Citas narrativas: 'Segun Garcia et al. (2022)...' / parenteticas: '(Lopez, 2021)'\n"
        "- Conectores logicos: 'En este sentido', 'No obstante', 'Desde un enfoque critico',\n"
        "  'Esta perspectiva se articula con', 'Cabe subrayar que', 'En suma'\n"
        "- Vocabulario epistemico: constructo, dimension, indicador, variable latente,\n"
        "  convergencia teorica, validez ecologica, triangulacion metodologica\n"
        "- Cada seccion inicia con parrafo contextualizador y cierra con parrafo sintetizador\n"
        "- S6 (Desarrollo) debe tener minimo 800 palabras en prosa continua\n\n"

        "VI. REGLAS ABSOLUTAS\n"
        "PROHIBIDO inventar autores, anios, titulos, revistas, DOI.\n"
        "SOLO citar fuentes en <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.\n"
        "Sin metadatos completos: marcar [FUENTE CANDIDATA A VERIFICAR].\n\n"

        "VII. APA 7\n"
        "Citas narrativas y parenteticas. No inventar paginas.\n"
        "Referencias: Apellido, I. (Anio). Titulo en cursiva. Revista, vol(num), pp. https://doi.org/xxx\n"
        f"NOTA: Rango empirico: {RANGO}. Teorias clasicas: sin restriccion de anio."
)

# ===================================================
# SIDEBAR - 6 SECCIONES
# ===================================================
with st.sidebar:
        st.markdown("## Constructor de Marco Teorico")
    st.markdown("**v6.0.0 - P-6 - Modo B Doctoral**")
    st.markdown("---")

    st.markdown("### 1. Configuracion")
    try:
                _key_hint = "Cargada desde st.secrets" if "ANTHROPIC_API_KEY" in st.secrets else "sk-ant-api03-..."
except Exception:
        _key_hint = "sk-ant-api03-..."
    api_key = st.text_input("API Key Anthropic", type="password", placeholder=_key_hint)
    modelo = st.selectbox("Modelo", ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-3-5"])
    modo = st.selectbox("Modo de operacion", [
                "AUTOMATICO (Gate global decide)",
                "FORZAR MODO A - DIAGNOSTICO",
                "FORZAR MODO B - REDACCION"
    ])
    st.markdown("---")

    st.markdown("### 2. Datos del Estudio")
    titulo = st.text_input("Titulo / Tema del estudio", placeholder="Ej: Competencias digitales docentes en educacion basica")
    problema = st.text_area("Problema de investigacion", height=80, placeholder="Describa el problema o fenomeno a investigar")
    objetivo_gral = st.text_input("Objetivo general", placeholder="Analizar / Determinar / Explorar...")
    _ph_obj = "1. Identificar..." + "\n" + "2. Describir..." + "\n" + "3. Analizar..."
    obj_esp = st.text_area("Objetivos especificos (uno por linea)", height=90, placeholder=_ph_obj)
    preguntas = st.text_area("Preguntas de investigacion", height=70, placeholder="Cual es...? / Como...? / Que relacion...?")
    ruta = st.selectbox("Ruta metodologica", ["Cuantitativa", "Cualitativa", "Mixta", "Por determinar"])
    poblacion = st.text_input("Poblacion / Muestra / Contexto", placeholder="Ej: 120 docentes, nivel primaria, Mexico")
    st.markdown("---")

    st.markdown("### 3. Variables clave")
    st.caption("VI = independiente / VD = dependiente. En estudios cualitativos: categorias.")
    vi = st.text_area("Variable Independiente (VI) / Categoria principal", height=65, placeholder="Ej: Uso de tecnologia educativa")
    vd = st.text_area("Variable Dependiente (VD) / Categoria secundaria", height=65, placeholder="Ej: Rendimiento academico")
    otras_vars = st.text_input("Otras variables (moderadoras / intervinientes)", placeholder="Ej: Edad, genero, nivel socioeconomico...")
    st.markdown("---")

    st.markdown("### 4. Fuentes manuales (opcional)")
    st.caption("Metadatos: Autor, Anio, Titulo, Revista, DOI. Sin DOI = no verificada.")
    fuentes_pegadas = st.text_area("Fuentes pegadas manualmente", height=120, placeholder="Autor (Anio). Titulo. Revista. DOI / Extracto...")
    st.markdown("---")

    st.markdown("### 5. Recuperacion automatica")
    area = st.text_input("Area disciplinar", placeholder="Educacion, Psicologia, Administracion...")
    pais = st.text_input("Pais / Contexto geografico", placeholder="Mexico, Colombia, Espania...")
    anio_desde = st.slider("Desde el ano", min_value=ANIO_ACTUAL - 15, max_value=ANIO_ACTUAL - 1, value=ANIO_INICIO)
    max_fuentes = st.slider("Max. fuentes a recuperar", min_value=5, max_value=30, value=15, step=5)
    recuperar = st.button("Recuperar + Verificar fuentes")
    st.markdown("---")

    st.markdown("### 6. Parametros del documento")
    documento = st.selectbox("Tipo de documento", ["Tesis de maestria", "Tesis doctoral", "Articulo cientifico", "TFM", "Trabajo de pregrado"])
    norma = st.selectbox("Norma de citacion", ["APA 7", "APA 6", "MLA", "Chicago"])
    st.markdown("---")
    st.caption(f"Rango empirico: {RANGO} | Teorias clasicas: sin restriccion")
    generar = st.button("GENERAR MARCO TEORICO")

# Variables consolidadas
variables_cats = ""
if vi.strip():
        variables_cats += f"VI: {vi.strip()}"
if vd.strip():
        variables_cats += f" | VD: {vd.strip()}"
if otras_vars.strip():
        variables_cats += f" | Otras: {otras_vars.strip()}"

# Cabecera
st.markdown(
        '''<div class="main-header">
            <h1>Constructor de Marco Teorico</h1>
                <p>Rigor academico - Gate de evidencia - Modo B Doctoral - APA 7</p>
                    <div class="badge-row">
                            <span class="badge">Claude</span><span class="badge">OpenAlex</span>
                                    <span class="badge">SemanticScholar</span><span class="badge">Crossref</span>
                                            <span class="badge">v6.0.0</span><span class="badge">P-6</span>
                                                </div>
                                                    </div>''',
        unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
        st.markdown('<div class="info-box"><b>Gate global</b><br>2 modos: Diagnostico o Redaccion Doctoral Final.</div>', unsafe_allow_html=True)
with col2:
        st.markdown('<div class="info-box"><b>VI / VD separadas</b><br>Seccion 3 dedicada a variables clave.</div>', unsafe_allow_html=True)
with col3:
        st.markdown('<div class="info-box"><b>Modo B Doctoral</b><br>14 secciones con prosa academica densa.</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-box"><b>Flujo:</b> Llena secciones 1-4 → Recuperar fuentes (Sec. 5) → Generar Marco (Sec. 6).</div>', unsafe_allow_html=True)

if "fuentes_recuperadas" not in st.session_state:
        st.session_state["fuentes_recuperadas"] = []
if "fuentes_verificadas" not in st.session_state:
        st.session_state["fuentes_verificadas"] = []
if "fuentes_bloque_auto" not in st.session_state:
        st.session_state["fuentes_bloque_auto"] = ""

if recuperar:
        if not (titulo or vi or vd):
                    st.warning("Ingresa Titulo o Variables (secciones 2-3) para buscar fuentes.")
else:
        query = titulo or f"{vi} {vd}"
        with st.spinner("Buscando fuentes en OpenAlex y SemanticScholar..."):
                        pb = st.progress(0)
            max_oa = max(5, max_fuentes // 2)
            max_s2 = max(5, max_fuentes - max_oa)
            oa_r = openalex_search(query, variables_cats, anio_desde, max_oa)
            pb.progress(0.35)
            s2_r = s2_search(query, variables_cats, max_s2)
            pb.progress(0.6)
            all_raw = oa_r + s2_r
            all_dedup = dedup_records(all_raw)
            pb.progress(0.75)
            verified = verify_records_concurrent(all_dedup, progress_bar=pb)
            pb.progress(1.0)

        st.session_state["fuentes_recuperadas"] = all_dedup
        st.session_state["fuentes_verificadas"] = verified

        if all_dedup:
                        lineas = []
            for r in all_dedup[:max_fuentes]:
                                authors_str = "; ".join(r.get("authors") or [])
                v_tag = "VERIFICADA" if r in verified else "NO_VERIFICADA"
                lineas.append(
                                        f"[ID={r['id']}|Base={r['source']}|Autor={authors_str}|"
                                        f"Anio={r.get('year','')}|Titulo={r.get('title','')}|"
                                        f"Revista={r.get('venue','')}|DOI={r.get('doi') or 'sin-doi'}|"
                                        f"Verificacion={v_tag}|Extracto={r.get('abstract','')[:200]}]"
                )
            st.session_state["fuentes_bloque_auto"] = (
                                "\n<<<FUENTES_AUTOMATICAS>>>\n" + "\n".join(lineas) + "\n<<<FIN_FUENTES_AUTOMATICAS>>>"
            )
            st.success(f"Recuperadas: {len(all_dedup)} | Verificadas con DOI+Crossref: {len(verified)}")
            with st.expander(f"Ver {len(all_dedup)} fuentes recuperadas", expanded=False):
                for r in all_dedup[:max_fuentes]:
                                        v_icon = "VERIFICADA" if r in verified else "no verificada"
                                        authors_str = "; ".join(r.get("authors") or []) or "s/a"
                                        st.markdown(f"**{r.get('title','Sin titulo')}**")
                                        st.caption(f"{authors_str} ({r.get('year','?')}) | {r.get('venue','s/r')} | DOI: {r.get('doi') or '---'} | {v_icon}")
else:
            st.info("No se encontraron fuentes. Intenta con terminos diferentes.")

elif st.session_state["fuentes_recuperadas"]:
    total = len(st.session_state["fuentes_recuperadas"])
    verif = len(st.session_state["fuentes_verificadas"])
    st.info(f"Fuentes en sesion: {total} recuperadas, {verif} verificadas. Presiona 'Recuperar + Verificar' para actualizar.")

if generar:
        if not api_key:
                    st.error("Ingresa tu API Key en Seccion 1.")
elif not titulo and not variables_cats:
        st.error("Ingresa Titulo o Variables (Secciones 2 y 3).")
else:
        if "FORZAR MODO A" in modo:
                        modo_instruccion = "FORZAR MODO A - DIAGNOSTICO DOCUMENTAL"
elif "FORZAR MODO B" in modo:
            modo_instruccion = "FORZAR MODO B - REDACCION DOCTORAL FINAL"
else:
            modo_instruccion = "AUTOMATICO - ejecuta Gate global segun suficiencia real"

        fuentes_auto_bloque = st.session_state.get("fuentes_bloque_auto", "")
        fuentes_bloque = ""
        if fuentes_pegadas.strip():
                        fuentes_bloque = "\n<<<FUENTES_PEGADAS>>>\n" + fuentes_pegadas.strip() + "\n<<<FIN_FUENTES_PEGADAS>>>"

        mensaje_usuario = (
                        f"Genera el marco teorico con LENGUAJE DOCTORAL RIGUROSO:\n"
                        f"TITULO/TEMA: {titulo}\n"
                        f"PROBLEMA: {problema}\n"
                        f"OBJETIVO GENERAL: {objetivo_gral}\n"
                        f"OBJETIVOS ESPECIFICOS:\n{obj_esp}\n"
                        f"PREGUNTAS: {preguntas}\n"
                        f"VARIABLE INDEPENDIENTE (VI): {vi}\n"
                        f"VARIABLE DEPENDIENTE (VD): {vd}\n"
                        f"OTRAS VARIABLES: {otras_vars}\n"
                        f"VARIABLES/CATEGORIAS: {variables_cats}\n"
                        f"RUTA METODOLOGICA: {ruta}\n"
                        f"POBLACION: {poblacion}\n"
                        f"AREA: {area}\n"
                        f"PAIS: {pais}\n"
                        f"DOCUMENTO: {documento}\n"
                        f"NORMA: {norma}\n"
                        f"MODO: {modo_instruccion}\n"
                        f"{fuentes_auto_bloque}\n"
                        f"{fuentes_bloque}\n"
                        "INSTRUCCIONES:\n"
                        "1. Primera seccion: DECISION DE MODO con Gate Global explicitado.\n"
                        "2. Gate falla -> MODO A (5 secciones). PROHIBIDO: definiciones, sintesis, antecedentes.\n"
                        "   Ultima linea MODO A: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.\n"
                        "3. Gate pasa -> MODO B DOCTORAL (14 secciones S0-S14).\n"
                        "4. MODO B: prosa academica densa, conectores epistemicos, vocabulario doctoral.\n"
                        "5. S6 Desarrollo: minimo 800 palabras en prosa continua con citas APA 7.\n"
                        "6. Sin metadatos completos = [FUENTE CANDIDATA A VERIFICAR].\n"
                        "7. Referencias S13: formato APA 7 estricto, orden alfabetico."
        )

        try:
                        client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Ejecutando gate de evidencia y generando marco doctoral..."):
                                result_area = st.empty()
                full_response = ""
                escaped_response = ""
                with client.messages.stream(
                                        model=modelo,
                                        max_tokens=8000,
                                        system=SYSTEM_PROMPT,
                                        messages=[{"role": "user", "content": mensaje_usuario}],
                ) as stream:
                                        for text in stream.text_stream:
                                                                    full_response += text
                                                                    escaped_response += html.escape(text)
                                                            result_area.markdown(
                                                                                            f"<div class='result-container'>{escaped_response}</div>",
                                                                                            unsafe_allow_html=True,
                                                            )

            st.success("Marco teorico doctoral generado.")
            docx_buf = generar_docx(full_response)
            nombre_archivo = f"marco_doctoral_{titulo[:30].replace(' ', '_') if titulo else 'estudio'}.docx"
            st.download_button(
                                label="Descargar resultado (.docx)",
                                data=docx_buf,
                                file_name=nombre_archivo,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
except anthropic.AuthenticationError:
            st.error("API Key invalida. Verifica en console.anthropic.com")
except anthropic.RateLimitError:
            st.error("Limite de uso alcanzado. Intenta en unos minutos.")
except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(
        f'''<footer>Powered by Claude v6.0.0 | P-6 Modo B Doctoral | OpenAlex + S2 + Crossref | Rango: {RANGO} | Gate activo</footer>''',
        unsafe_allow_html=True,
)
