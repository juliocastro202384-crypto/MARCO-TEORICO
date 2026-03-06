# app.py — Constructor de Marco Teorico v5.8.0
# Parches: P-CRITICO, P-1, P-2, P-3, P-4, P-5

import io
import re
import json
import time
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

# ===================================================
# CONFIGURACION GLOBAL
# ===================================================
ANIO_ACTUAL    = datetime.now().year
ANIO_INICIO    = ANIO_ACTUAL - 5
RANGO          = f"{ANIO_INICIO}-{ANIO_ACTUAL}"

OPENALEX         = "https://api.openalex.org"
CROSSREF         = "https://api.crossref.org"
S2               = "https://api.semanticscholar.org/graph/v1"
CROSSREF_WORKERS = 8
S2_FIELDS = (
    "title,year,venue,abstract,url,authors,"
    "citationCount,referenceCount,externalIds,publicationTypes"
)

st.set_page_config(
    page_title="Constructor de Marco Teorico - Claude",
    page_icon=":classical_building:",
    layout="wide",
)

# ===================================================
# ESTILOS
# ===================================================
CSS = """
<style>
  html, body, [class*="css"] { font-family: Georgia, serif; }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f6f0 0%, #eef2f7 100%);
    border-right: 2px solid #2563eb;
  }
  [data-testid="stSidebar"] .stMarkdown h2 { color: #1e3a5f; font-size: 1.1rem; }
  [data-testid="stSidebar"] .stMarkdown h3 { color: #2563eb; font-size: 0.95rem; }
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
    color: white; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
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
    background: #fafafa; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 1.5rem; margin-top: 1rem;
  }
  .stButton > button {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: white; border: none; border-radius: 8px;
    padding: 0.6rem 1.2rem; font-weight: 600; width: 100%;
  }
  footer {
    color: #9ca3af; font-size: 0.8rem; text-align: center;
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===================================================
# CONSTANTES DE BUSQUEDA
# ===================================================
_GENERIC_TERMS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was",
    "were", "has", "have", "been", "will", "can", "may", "not", "but",
    "como", "para", "que", "los", "las", "del", "una", "por", "con",
    "sus", "son", "ser", "esta", "este",
}

# ===================================================
# FIX-1: _relevance_score() sin saturacion falsa
# ===================================================
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

# ===================================================
# FIX-2: is_header_like() sin falsos positivos
# ===================================================
def is_header_like(p: str) -> bool:
    lines = p.split("\n")
    if len(lines) > 2:
        return False
    first = lines[0].strip()
    if re.match(r"^#{1,4}\s", first):
        return True
    if first == first.upper() and first != first.lower() and len(first) <= 80:
        return True
    if re.match(r"^(\d{1,2}|[IVX]{1,4})[.)]\s+[A-Z]", first) and len(first) <= 80:
        return True
    if first.endswith(":") and len(first) <= 60 and "\n" not in first:
        return True
    return False

# ===================================================
# FUNCIONES DE VERIFICACION
# ===================================================
def is_valid_doi(doi: str) -> bool:
    if not doi:
        return False
    doi = doi.strip().lower()
    return doi.startswith("10.") and "/" in doi

@st.cache_data(ttl=3600, show_spinner=False)
def crossref_ok(doi: str) -> bool:
    try:
        url = f"{CROSSREF}/works/{doi.strip()}"
        r = requests.get(url, timeout=8, headers={"User-Agent": "MarcoTeoricoApp/5.8"})
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
        r = requests.get(f"{OPENALEX}/works", params=params, timeout=10,
                         headers={"User-Agent": "MarcoTeoricoApp/5.8"})
        if r.status_code != 200:
            return []
        data = r.json()
        results = []
        for w in data.get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            authors = [
                a["author"]["display_name"]
                for a in w.get("authorships", [])[:3]
                if a.get("author")
            ]
            venue = ""
            loc = w.get("primary_location") or {}
            src = loc.get("source") or {}
            venue = src.get("display_name", "")
            abstract = ""
            inv = w.get("abstract_inverted_index") or {}
            if inv:
                positions = []
                for word, pos_list in inv.items():
                    for pos in pos_list:
                        positions.append((pos, word))
                positions.sort(key=lambda x: x[0])
                abstract = " ".join(w for _, w in positions[:80])
            results.append({
                "id": f"OA_{len(results)+1}",
                "source": "OpenAlex",
                "title": w.get("title", ""),
                "year": w.get("publication_year"),
                "authors": authors,
                "venue": venue,
                "doi": doi,
                "abstract": abstract,
                "open_access": (w.get("open_access") or {}).get("is_oa", False),
                "verified_by": [],
                "quality_flags": {},
            })
        return results
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def s2_search(query: str, variables: str) -> List[Dict]:
    try:
        params = {
            "query": f"{query} {variables}",
            "limit": 8,
            "fields": S2_FIELDS,
        }
        r = requests.get(f"{S2}/paper/search", params=params, timeout=10)
        if r.status_code != 200:
            return []
        results = []
        for p in r.json().get("data", []):
            ext = p.get("externalIds") or {}
            doi = ext.get("DOI", "")
            authors = [a.get("name", "") for a in p.get("authors", [])[:3]]
            results.append({
                "id": f"S2_{len(results)+1}",
                "source": "SemanticScholar",
                "title": p.get("title", ""),
                "year": p.get("year"),
                "authors": authors,
                "venue": p.get("venue", ""),
                "doi": doi,
                "abstract": (p.get("abstract") or "")[:500],
                "open_access": False,
                "verified_by": [],
                "quality_flags": {},
            })
        return results
    except Exception:
        return []

# ===================================================
# FIX-3: verify_records_concurrent() thread-safe
# ===================================================
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
    done  = 0
    verified = []

    def _check(rec: Dict) -> Tuple[bool, Dict]:
        doi = rec.get("doi")
        ok  = bool(doi and is_valid_doi(doi) and crossref_ok(doi))
        rec["verified_by"]                   = ["Crossref"] if ok else []
        rec["quality_flags"]["has_doi"]      = bool(doi)
        rec["quality_flags"]["has_venue"]    = bool(rec.get("venue"))
        rec["quality_flags"]["has_year"]     = bool(rec.get("year"))
        rec["quality_flags"]["has_authors"]  = bool(rec.get("authors"))
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
        title_norm = norm(r.get("title") or "")
        if doi and doi in seen_doi:
            continue
        dup_title = any(fuzz.ratio(title_norm, t) > 88 for t in seen_title)
        if dup_title:
            continue
        if doi:
            seen_doi.add(doi)
        if title_norm:
            seen_title.add(title_norm)
        out.append(r)
    return out

# ===================================================
# FIX-5: generar_docx() robusto a numeracion romana
# ===================================================
def generar_docx(texto: str) -> io.BytesIO:
    doc = Document()
    doc.add_heading("Marco Teorico", 0)
    for linea in texto.split("\n"):
        stripped = linea.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,2}\s", stripped):
            level = 1 if stripped.startswith("## ") else 2
            doc.add_heading(re.sub(r"^#+\s+", "", stripped), level=level)
        elif re.match(r"^(I{{1,3}}|IV|V?I{{0,3}}|IX|X)\. \S", stripped, re.I):
            doc.add_heading(stripped, level=1)
        elif re.match(r"^\d{{1,2}}\. [A-Z]", stripped):
            doc.add_heading(stripped, level=2)
        else:
            doc.add_paragraph(stripped)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ===================================================
# SYSTEM PROMPT
# ===================================================
SYSTEM_PROMPT = f"""AGENTE: CONSTRUCTOR DE MARCO TEORICO v5.8
Eres un AGENTE ACADEMICO DE ALTO RIGOR especializado en construir MARCOS TEORICOS.

====================================================
0. DECISION DE MODO - PRIMERA SECCION OBLIGATORIA
DECISION DE MODO
- Gate global cumplido: Si / No
- Modo activado: MODO A o MODO B
- Ruta metodologica identificada: ...
- Variables/categorias aptas: [lista]
- Variables/categorias NO aptas: [lista]
====================================================
I. GATE GLOBAL DE EVIDENCIA
- Si FALTA suficiencia en 1 variable -> MODO A (DIAGNOSTICO)
- Si TODAS cumplen -> MODO B (REDACCION FINAL)
No existen modos intermedios.
====================================================
II. SUFICIENCIA MINIMA POR VARIABLE/CATEGORIA
VERIFICADA requiere Autor+Anio+Titulo+Revista/Editorial:
- Definicion conceptual: minimo 2 fuentes verificadas
- Fundamento teorico/modelo: minimo 1 fuente verificada
- Antecedentes empiricos: minimo 2 fuentes verificadas (ideal 4-8)
Reglas duras:
- Google Scholar sin DOI -> NO CUENTA como verificada
- Latindex valida revistas, NO articulos
- Autor/anio sin metadatos -> [FUENTE CANDIDATA A VERIFICAR]
====================================================
III. MODO A - DIAGNOSTICO DOCUMENTAL (5 secciones exactas)
SECCION 1: DECISION DE MODO
SECCION 2: VACIOS POR VARIABLE/CATEGORIA
Tabla: Variable | Def.conceptual(min2) | Fund.teorico(min1) | Antec.empiricos(min2) | Estado
Estado: Completo / Insuficiente / No verificable
SECCION 3: SEMILLAS DETECTADAS
Clasifica citas como: Semilla teorica / empirica / institucional / contextual
SECCION 4: PAQUETE TECNICO DE CONSULTAS
<<<CONSULTAS_RECUPERACION>>>
OPENALEX:
  query_1: "..."
  query_2: "..."
  filters:
    from_publication_date: {ANIO_INICIO}-01-01
    is_paratext: false
    language: es|en
  fields: [id, doi, title, publication_year, authorships, primary_location, open_access, abstract_inverted_index, primary_topic, host_venue]
REDALYC:
  query_1: "..."
  query_2: "..."
LATINDEX:
  validar_por_revista: ["...", "..."]
  validar_por_issn: ["...", "..."]
GOOGLE_SCHOLAR:
  scholar_query_1: "..."
  scholar_query_2: "..."
<<<FIN_CONSULTAS_RECUPERACION>>>
SECCION 5: PLANTILLA DE REINYECCION
<<<FUENTES_RECUPERADAS>>>
[ID=OA1|Base=OpenAlex|Autor=...|Anio=...|Titulo=...|Revista=...|DOI=...|ISSN_L=...|OA=true/false|Extracto=...]
[ID=R1|Base=Redalyc|Autor=...|Anio=...|Titulo=...|Revista=...|DOI=...|ISSN_L=...|Extracto=...]
[ID=LX1|Base=Latindex|Revista=...|ISSN_L=...|Estatus=Catalogo 2.0/Directorio/No confirmado|Evidencia=...]
<<<FIN_FUENTES_RECUPERADAS>>>
LINEA FINAL OBLIGATORIA: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.
PROHIBIDO en MODO A: definiciones, sintesis critica, antecedentes narrativos, preguntas al usuario.
====================================================
IV. MODO B - REDACCION ACADEMICA FINAL (14 secciones)
0. Decision de modo
1. Ficha del estudio
2. Ruta metodologica identificada y justificada
3. Inventario de fuentes [ID|Base|Autor/Anio|Titulo|Revista|Verificacion|Validacion|Uso]
4. Evaluacion de calidad [ID|Pertinencia|Actualidad|Verificabilidad|Calidad editorial|Utilidad|Total|Clasificacion]
5. Indice del marco teorico
6. Desarrollo por variables/categorias [Delimitacion/Definiciones/Sintesis/Definicion integradora/Implicacion/Dimensiones/Evidencias]
7. Fundamento teorico general
8. Antecedentes empiricos [Matriz: Autor/anio|pais|objetivo|metodo|muestra|hallazgos|limitaciones|aporte] + Sintesis
9. Operacionalizacion o categorizacion
10. Vacios de investigacion
11. Riesgos de validez y limitaciones
12. Cobertura final
13. Referencias verificadas en APA 7
14. Fuentes pendientes y estrategias
Dividir en PARTE 1/N si la respuesta no cabe.
====================================================
V. RUTAS METODOLOGICAS
Coherencia: problema -> objetivos -> preguntas -> ruta -> marco -> diseno.
CUANTITATIVA: variables, definiciones conceptuales/operacionales, dimensiones, indicadores, hipotesis.
CUALITATIVA: categorias, significados, perspectivas interpretativas, subcategorias.
MIXTA: integra variables y categorias, combina evidencia cuanti/cuali.
====================================================
VI. REGLAS ABSOLUTAS
PROHIBIDO inventar: autores, anios, titulos, revistas, DOI, URL, hallazgos.
SOLO citar fuentes dentro de <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.
Cada parrafo MODO B: idea central + respaldo verificable + implicacion.
====================================================
VII. JERARQUIA DE FUENTES
OPENALEX: descubrimiento y metadatos principales.
REDALYC: literatura iberoamericana y acceso abierto.
LATINDEX: validacion editorial. NO sustituye metadatos del articulo.
GOOGLE SCHOLAR: solo localizacion. Sin DOI = NO verificada.
====================================================
VIII. ENTRADAS A IDENTIFICAR
Extrae: Titulo, Problema, Objetivo general, Objetivos especificos, Preguntas, Ruta, Contexto, Poblacion, Variables/Categorias, Producto.
Si faltan datos criticos: maximo 5 preguntas.
Si no responde: crear "Supuestos de trabajo" etiquetados.
====================================================
IX. CLASIFICACION DE VERIFICABILIDAD
VERIFICADA: autor + anio + titulo + revista/editorial.
PARCIALMENTE VERIFICABLE: identificable pero incompleta.
LOCALIZADA NO VERIFICADA: sin DOI o metadatos suficientes.
Solo VERIFICADAS sostienen la redaccion final.
====================================================
X. EVALUACION DE CALIDAD (solo MODO B, escala 1-5)
A. Pertinencia | B. Actualidad | C. Verificabilidad | D. Calidad editorial | E. Utilidad
23-25=ALTA PRIORIDAD | 18-22=UTIL | 13-17=COMPLEMENTARIA | 8-12=DEBIL | 5-7=NO RECOMENDADA
====================================================
XI. APA 7
Citas narrativas o parenteticas. No inventar paginas.
Separa: Verificadas / Pendientes / Localizadas no verificadas.
====================================================
XII. REGLA FINAL
Sin evidencia suficiente: NO redactar el marco teorico final.
Devolver diagnostico tecnico + consultas + plantilla de reinyeccion.
Ultima linea MODO A: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.
NOTA: Rango fuentes empiricas: {RANGO}. Teorias clasicas: sin restriccion de anio."""

# ===================================================
# SIDEBAR
# ===================================================
with st.sidebar:
    st.markdown("## Constructor de Marco Teorico")
    st.markdown("**v5.8.0 - Claude - OpenAlex + S2 + Crossref**")
    st.markdown("---")
    st.markdown("### Configuracion")

    # FIX-CRITICO: _key_hint sin crash por secrets ausentes
    try:
        _key_hint = (
            "Cargada desde st.secrets"
            if "ANTHROPIC_API_KEY" in st.secrets
            else "sk-ant-api03-..."
        )
    except Exception:
        _key_hint = "sk-ant-api03-..."

    api_key = st.text_input(
        "API Key Anthropic",
        type="password",
        placeholder=_key_hint,
    )

    modo = st.selectbox(
        "Modo de operacion",
        [
            "AUTOMATICO (Gate global decide)",
            "FORZAR MODO A - DIAGNOSTICO",
            "FORZAR MODO B - REDACCION",
        ],
        help="AUTOMATICO: el agente evalua y decide. FORZAR: anula la decision automatica.",
    )

    st.markdown("---")
    st.markdown("### Datos del Estudio")

    titulo = st.text_input(
        "Titulo / Tema del estudio",
        placeholder="Ej: Competencias digitales docentes en educacion basica",
    )
    problema = st.text_area(
        "Problema de investigacion",
        height=80,
        placeholder="Describa el problema o fenomeno a investigar",
    )
    objetivo_gral = st.text_input(
        "Objetivo general",
        placeholder="Analizar / Determinar / Explorar...",
    )
    obj_esp = st.text_area(
        "OBJETIVOS ESPECIFICOS (uno por linea)",
        height=100,
        placeholder="1. Identificar...
2. Describir...
3. Analizar...",
    )
    preguntas = st.text_area(
        "Preguntas de investigacion",
        height=70,
        placeholder="Cual es...? / Como...? / Que relacion...?",
    )
    variables_cats = st.text_area(
        "Variables / Categorias",
        height=70,
        placeholder="Variable 1: ... / Categoria 1: ...",
    )
    ruta = st.selectbox(
        "Ruta metodologica",
        ["Cuantitativa", "Cualitativa", "Mixta", "Por determinar"],
        help="Cuantitativa=variables | Cualitativa=categorias | Mixta=integracion",
    )
    poblacion = st.text_input(
        "Poblacion / Muestra / Contexto",
        placeholder="Ej: 120 docentes, nivel primaria, Mexico",
    )

    st.markdown("---")
    st.markdown("### Fuentes")
    st.caption(
        "Metadatos completos requeridos: autor, anio, titulo, revista, DOI. "
        "Sin metadatos = no verificada."
    )
    fuentes_pegadas = st.text_area(
        "Fuentes pegadas manualmente",
        height=150,
        placeholder="Autor (Anio). Titulo. Revista. DOI / Extracto...",
    )

    st.markdown("---")
    st.markdown("### Parametros")
    documento = st.selectbox(
        "Tipo de documento",
        ["Tesis de maestria", "Tesis doctoral", "Articulo cientifico", "TFM", "Trabajo de pregrado"],
    )
    norma = st.selectbox(
        "Norma de citacion",
        ["APA 7", "APA 6", "MLA", "Chicago"],
    )
    area = st.text_input(
        "Area disciplinar",
        placeholder="Educacion, Psicologia, Administracion...",
    )
    pais = st.text_input(
        "Pais / Contexto geografico",
        placeholder="Mexico, Colombia, Espania...",
    )

    st.markdown("---")
    buscar_fuentes = st.checkbox(
        "Buscar fuentes automaticamente (OpenAlex + S2)",
        value=True,
        help="Consulta OpenAlex y Semantic Scholar antes de enviar al agente.",
    )
    st.caption(f"Rango fuentes empiricas: {RANGO} | Teorias clasicas: sin restriccion")
    st.caption("OpenAlex - SemanticScholar - Crossref - Redalyc - Latindex")

generar = st.button("GENERAR MARCO TEORICO")

# ===================================================
# CABECERA PRINCIPAL
# ===================================================
st.markdown(
    """
    <div class="main-header">
      <h1>Constructor de Marco Teorico</h1>
      <p>Rigor academico - Gate de evidencia - Rutas metodologicas - APA 7</p>
      <div class="badge-row">
        <span class="badge">Claude Opus</span>
        <span class="badge">OpenAlex</span>
        <span class="badge">SemanticScholar</span>
        <span class="badge">Crossref</span>
        <span class="badge">v5.8.0</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="info-box"><b>Gate de evidencia global</b><br>'
        "Solo 2 modos: Diagnostico o Redaccion Final. Sin modo hibrido.</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="info-box"><b>Verificacion automatica</b><br>'
        "OpenAlex + SemanticScholar + Crossref para metadatos reales.</div>",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="info-box"><b>Paquete tecnico</b><br>'
        "Consultas para OpenAlex, Redalyc, Latindex y Scholar listas para ejecutar.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="warning-box"><b>Gate global:</b> Si FALTA suficiencia en al menos 1 variable '
    "-> MODO A. Solo si TODAS las variables cumplen -> MODO B. "
    "Sin modo hibrido ni redaccion parcial.</div>",
    unsafe_allow_html=True,
)

# ===================================================
# LOGICA PRINCIPAL
# ===================================================
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
            modo_instruccion = (
                "AUTOMATICO - ejecuta el Gate global y decide segun "
                "suficiencia real de fuentes provistas"
            )

        # Busqueda automatica de fuentes
        fuentes_auto_bloque = ""
        if buscar_fuentes and (titulo or variables_cats):
            with st.spinner("Buscando fuentes en OpenAlex y SemanticScholar..."):
                pb = st.progress(0)
                oa_results = openalex_search(titulo or variables_cats, variables_cats, ANIO_INICIO)
                pb.progress(0.4)
                s2_results = s2_search(titulo or variables_cats, variables_cats)
                pb.progress(0.7)
                all_raw = oa_results + s2_results
                all_dedup = dedup_records(all_raw)
                verified = verify_records_concurrent(all_dedup, progress_bar=pb)
                pb.progress(1.0)
                if verified or all_dedup:
                    lineas = []
                    for r in all_dedup[:12]:
                        authors_str = "; ".join(r.get("authors") or [])
                        v_tag = "VERIFICADA" if r in verified else "NO_VERIFICADA"
                        doi_str = r.get("doi") or "sin-doi"
                        lineas.append(
                            f"[ID={r['id']}|Base={r['source']}|"
                            f"Autor={authors_str}|Anio={r.get('year','')}|"
                            f"Titulo={r.get('title','')}|Revista={r.get('venue','')}|"
                            f"DOI={doi_str}|Verificacion={v_tag}|"
                            f"Extracto={r.get('abstract','')[:200]}]"
                        )
                    fuentes_auto_bloque = (
                        "\n<<<FUENTES_AUTOMATICAS>>>\n"
                        + "\n".join(lineas)
                        + "\n<<<FIN_FUENTES_AUTOMATICAS>>>"
                    )
                    st.success(f"Fuentes encontradas: {len(all_dedup)} totales, {len(verified)} verificadas con DOI+Crossref.")

        fuentes_bloque = ""
        if fuentes_pegadas.strip():
            fuentes_bloque = (
                "\n<<<FUENTES_PEGADAS>>>\n"
                + fuentes_pegadas.strip()
                + "\n<<<FIN_FUENTES_PEGADAS>>>"
            )

        mensaje_usuario = f"""Genera el marco teorico con la siguiente informacion:

TITULO/TEMA: {titulo}
PROBLEMA: {problema}
OBJETIVO GENERAL: {objetivo_gral}
OBJETIVOS ESPECIFICOS:
{obj_esp}
PREGUNTAS DE INVESTIGACION: {preguntas}
VARIABLES / CATEGORIAS: {variables_cats}
RUTA METODOLOGICA: {ruta}
POBLACION / MUESTRA / CONTEXTO: {poblacion}
TIPO DE DOCUMENTO: {documento}
NORMA DE CITACION: {norma}
AREA DISCIPLINAR: {area}
PAIS / CONTEXTO GEOGRAFICO: {pais}
MODO SOLICITADO: {modo_instruccion}
{fuentes_auto_bloque}
{fuentes_bloque}

INSTRUCCIONES CRITICAS:
1. La primera seccion SIEMPRE es DECISION DE MODO.
2. Ejecuta el Gate Global ANTES de redactar cualquier seccion narrativa.
3. Si el gate falla -> MODO A: exactamente 5 secciones. Ultima linea: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.
4. En MODO A: PROHIBIDO definiciones, sintesis critica, antecedentes narrativos.
5. Si el gate pasa -> MODO B: marco completo con 14 secciones.
6. Autores sin metadatos completos = [FUENTE CANDIDATA A VERIFICAR]."""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Ejecutando gate de evidencia y analizando suficiencia documental..."):
                result_area = st.empty()
                full_response = ""
                # FIX-4: Streaming O(n) - escapa solo el chunk nuevo
                escaped_response = ""
                with client.messages.stream(
                    model="claude-opus-4-5",
                    max_tokens=8000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": mensaje_usuario}],
                ) as stream:
                    for text in stream.text_stream:
                        full_response   += text
                        escaped_response += html.escape(text)
                        result_area.markdown(
                            f"<div class='result-container'>{escaped_response}</div>",
                            unsafe_allow_html=True,
                        )

            st.success("Analisis completado.")
            docx_buf = generar_docx(full_response)
            nombre_archivo = (
                f"marco_teorico_{titulo[:30].replace(' ', '_') if titulo else 'estudio'}.docx"
            )
            st.download_button(
                label="Descargar Resultado (.docx)",
                data=docx_buf,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        except anthropic.AuthenticationError:
            st.error("API Key invalida. Verifica en console.anthropic.com")
        except anthropic.RateLimitError:
            st.error("Limite de uso alcanzado. Intenta en unos minutos.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(
    f"""<footer>
    Powered by Claude - Anthropic - v5.8.0 &nbsp;|&nbsp;
    OpenAlex + SemanticScholar + Crossref &nbsp;|&nbsp;
    Rango empirico: {RANGO} &nbsp;|&nbsp;
    Teorias clasicas: sin restriccion &nbsp;|&nbsp;
    Gate global activo
    </footer>""",
    unsafe_allow_html=True,
)
