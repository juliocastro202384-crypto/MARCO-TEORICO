import streamlit as st
import anthropic
from docx import Document
import io
from datetime import datetime

ANIO_ACTUAL = datetime.now().year
ANIO_INICIO = ANIO_ACTUAL - 5
RANGO = f"{ANIO_INICIO}-{ANIO_ACTUAL}"

st.set_page_config(page_title="Constructor de Marco Teorico - Claude", page_icon="🏛️", layout="wide")

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
  .badge { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
  .info-box { background: #eff6ff; border-left: 4px solid #2563eb; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .warning-box { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .result-container { background: #fafafa; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.5rem; margin-top: 1rem; }
  .stButton > button { background: linear-gradient(135deg, #1e3a5f, #2563eb); color: white; border: none; border-radius: 8px; padding: 0.6rem 1.2rem; font-weight: 600; width: 100%; }
  footer { color: #9ca3af; font-size: 0.8rem; text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

SYSTEM_PROMPT = f"""TITULO DEL AGENTE: CONSTRUCTOR DE MARCO TEORICO v5.3

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
III. MODO A - DIAGNOSTICO DOCUMENTAL

ESTRUCTURA EXACTA:

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
[ID=OA1 | Base=OpenAlex | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | OA=true/false | PDF=... | URL=... | Extracto=...]
[ID=R1 | Base=Redalyc | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | PDF=... | URL=... | Extracto=...]
[ID=LX1 | Base=Latindex | Revista=... | ISSN_L=... | Estatus=Catalogo 2.0/Directorio/No confirmado | Evidencia=...]
<<<FIN_FUENTES_RECUPERADAS>>>

LINEA FINAL OBLIGATORIA: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.

PROHIBIDO en MODO A:
- Redactar desarrollo conceptual
- Escribir sintesis critica o antecedentes narrativos
- Extenderte en explicaciones largas
- Cerrar con preguntas al usuario
- Dividir en partes

====================================================
IV. MODO B - REDACCION ACADEMICA FINAL

ESTRUCTURA OBLIGATORIA (14 secciones):
0. Decision de modo
1. Ficha del estudio
2. Ruta metodologica identificada y justificada
3. Inventario de fuentes [Tabla: ID | Base | Autor/Anio | Titulo | Revista/Editorial | Verificacion | Validacion editorial | Uso permitido]
4. Evaluacion de calidad [Tabla: ID | Pertinencia | Actualidad | Verificabilidad | Calidad editorial | Utilidad metodologica | Total | Clasificacion]
5. Indice del marco teorico
6. Desarrollo por variables/categorias [Delimitacion / Definiciones / Sintesis critica / Definicion integradora / Implicacion / Dimensiones / Evidencias]
7. Fundamento teorico general
8. Antecedentes empiricos [Matriz: Autor/anio | pais | objetivo | metodo | muestra | hallazgos | limitaciones | aporte] + Sintesis integradora
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
LATINDEX: validacion editorial de revistas. NO sustituye metadatos del articulo.
GOOGLE SCHOLAR: solo localizacion. Sin DOI = NO verificada.

====================================================
VIII. ENTRADAS QUE DEBES IDENTIFICAR

Extrae: Titulo, Problema, Objetivo general, Objetivos especificos, Preguntas, Ruta, Contexto, Poblacion, Variables/Categorias, Producto.
Si faltan datos criticos: maximo 5 preguntas. Si no responde: "Supuestos de trabajo" etiquetados.

====================================================
IX. CLASIFICACION DE VERIFICABILIDAD

VERIFICADA: autor + anio + titulo + revista/editorial.
PARCIALMENTE VERIFICABLE: identificable pero incompleta.
LOCALIZADA NO VERIFICADA: sin DOI o metadatos suficientes.
Solo VERIFICADAS sostienen la redaccion final.

====================================================
X. EVALUACION DE CALIDAD (solo MODO B, escala 1-5)

A. Pertinencia | B. Actualidad | C. Verificabilidad | D. Calidad editorial | E. Utilidad metodologica
Total: 23-25=ALTA PRIORIDAD | 18-22=UTIL | 13-17=COMPLEMENTARIA | 8-12=DEBIL | 5-7=NO RECOMENDADA

====================================================
XI. APA 7

Citas narrativas o parenteticas. No inventar paginas.
Separa: Verificadas / Pendientes / Localizadas no verificadas.

====================================================
XII. REGLA FINAL

Sin evidencia suficiente: NO redactar el marco teorico final.
Devolver diagnostico tecnico + paquete de consultas + plantilla de reinyeccion.
Ultima linea MODO A: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.

NOTA: Rango fuentes empiricas recientes: {RANGO}. Teorias clasicas: sin restriccion de anio."""


def generar_docx(texto):
    doc = Document()
    doc.add_heading("Marco Teorico", 0)
    for linea in texto.split("\n"):
        if linea.strip():
            doc.add_paragraph(linea.strip())
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


with st.sidebar:
    st.markdown("## Constructor de Marco Teorico")
    st.markdown("**v5.3 - Claude - OpenAlex + Redalyc**")
    st.markdown("---")
    st.markdown("### Configuracion")
    api_key = st.text_input("API Key Anthropic", type="password", placeholder="sk-ant-api03-...")
    modo = st.selectbox(
        "Modo de operacion",
        ["AUTOMATICO (Gate global decide)", "FORZAR MODO A - DIAGNOSTICO", "FORZAR MODO B - REDACCION"],
        help="AUTOMATICO: el agente evalua fuentes y decide. FORZAR: anula la decision automatica."
    )
    st.markdown("---")
    st.markdown("### Datos del Estudio")
    titulo = st.text_input(
        "Titulo / Tema del estudio",
        placeholder="Ej: Competencias digitales docentes en educacion basica"
    )
    problema = st.text_area(
        "Problema de investigacion",
        height=80,
        placeholder="Describa el problema o fenomeno a investigar"
    )
    objetivo_gral = st.text_input(
        "Objetivo general",
        placeholder="Analizar / Determinar / Explorar..."
    )
    objetivos_esp = st.text_area(
        "OBJETIVOS ESPECIFICOS",
        height=100,
        placeholder="""1. Identificar...
2. Describir...
3. Analizar..."""
    )
    preguntas = st.text_area(
        "Preguntas de investigacion",
        height=70,
        placeholder="Cual es...? / Como...? / Que relacion...?"
    )
    variables_cats = st.text_area(
        "Variables / Categorias",
        height=70,
        placeholder="Variable 1: ... / Categoria 1: ..."
    )
    ruta = st.selectbox(
        "Ruta metodologica",
        ["Cuantitativa", "Cualitativa", "Mixta", "Por determinar"],
        help="Cuantitativa=variables | Cualitativa=categorias | Mixta=integracion"
    )
    poblacion = st.text_input(
        "Poblacion / Muestra / Contexto",
        placeholder="Ej: 120 docentes, nivel primaria, Mexico"
    )
    st.markdown("---")
    st.markdown("### Fuentes")
    st.caption(
        "Requiere metadatos completos: autor, anio, titulo, revista, DOI. "
        "Sin metadatos = no verificada."
    )
    fuentes_pegadas = st.text_area(
        "Fuentes pegadas manualmente",
        height=150,
        placeholder="Autor (Anio). Titulo. Revista. DOI / Extracto..."
    )
    st.markdown("---")
    st.markdown("### Parametros")
    documento = st.selectbox(
        "Tipo de documento",
        ["Tesis de maestria", "Tesis doctoral", "Articulo cientifico", "TFM", "Trabajo de pregrado"]
    )
    norma = st.selectbox("Norma de citacion", ["APA 7", "APA 6", "MLA", "Chicago"])
    area = st.text_input("Area disciplinar", placeholder="Educacion, Psicologia, Administracion...")
    pais = st.text_input("Pais / Contexto geografico", placeholder="Mexico, Colombia, Espania...")
    st.markdown("---")
    st.caption(f"Rango fuentes empiricas: {RANGO} | Teorias clasicas: sin restriccion")
    st.caption("OpenAlex - Redalyc - Latindex - Google Scholar")
    generar = st.button("GENERAR MARCO TEORICO")


st.markdown("""
<div class="main-header">
  <h1>Constructor de Marco Teorico</h1>
  <p>Rigor academico - Gate de evidencia - Rutas metodologicas - APA 7</p>
  <div class="badge-row">
    <span class="badge">Claude Opus</span>
    <span class="badge">OpenAlex</span>
    <span class="badge">Redalyc</span>
    <span class="badge">Latindex</span>
    <span class="badge">Google Scholar</span>
    <span class="badge">v5.3</span>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="info-box"><b>Gate de evidencia global</b><br>'
        'Solo 2 modos: Diagnostico o Redaccion Final. Sin modo hibrido.</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<div class="info-box"><b>Semillas detectadas</b><br>'
        'Citas del planteamiento clasificadas como semillas para busqueda, no como evidencia.</div>',
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        '<div class="info-box"><b>Paquete tecnico</b><br>'
        'Consultas exactas para OpenAlex, Redalyc, Latindex y Scholar listas para ejecutar.</div>',
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="warning-box">Gate global: Si FALTA suficiencia en al menos 1 variable -> MODO A. '
    'Solo si TODAS las variables cumplen -> MODO B. Sin modo hibrido ni redaccion parcial.</div>',
    unsafe_allow_html=True
)

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

        fuentes_bloque = ""
        if fuentes_pegadas.strip():
            fuentes_bloque = f"""
<<<FUENTES_PEGADAS>>>
{fuentes_pegadas.strip()}
<<<FIN_FUENTES_PEGADAS>>>"""

        mensaje_usuario = f"""Genera el marco teorico con la siguiente informacion:

TITULO/TEMA: {titulo}
PROBLEMA: {problema}
OBJETIVO GENERAL: {objetivo_gral}
OBJETIVOS ESPECIFICOS:
{objetivos_esp}
PREGUNTAS DE INVESTIGACION: {preguntas}
VARIABLES / CATEGORIAS: {variables_cats}
RUTA METODOLOGICA: {ruta}
POBLACION / MUESTRA / CONTEXTO: {poblacion}
TIPO DE DOCUMENTO: {documento}
NORMA DE CITACION: {norma}
AREA DISCIPLINAR: {area}
PAIS / CONTEXTO GEOGRAFICO: {pais}
MODO SOLICITADO: {modo_instruccion}

{fuentes_bloque}

INSTRUCCIONES CRITICAS:
1. La primera seccion SIEMPRE es DECISION DE MODO.
2. Ejecuta el Gate Global ANTES de redactar cualquier seccion narrativa.
3. Si el gate falla -> MODO A: 5 secciones exactas (DECISION / VACIOS / SEMILLAS / CONSULTAS / REINYECCION).
   Ultima linea: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.
4. En MODO A: PROHIBIDO escribir definiciones, sintesis critica, teoria, antecedentes narrativos.
5. Si el gate pasa -> MODO B: marco teorico completo con las 14 secciones.
6. Autores sin metadatos completos = [FUENTE CANDIDATA A VERIFICAR]."""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Ejecutando gate de evidencia y analizando suficiencia documental..."):
                result_area = st.empty()
                full_response = ""
                with client.messages.stream(
                    model="claude-opus-4-5",
                    max_tokens=8000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": mensaje_usuario}]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        result_area.markdown(
                            f'<div class="result-container">{full_response}</div>',
                            unsafe_allow_html=True
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
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except anthropic.AuthenticationError:
            st.error("API Key invalida. Verifica en console.anthropic.com")
        except anthropic.RateLimitError:
            st.error("Limite de uso alcanzado. Intenta en unos minutos o verifica tus creditos.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(f"""
<footer>
  Powered by Claude - Anthropic - v5.3 &nbsp;|&nbsp;
  OpenAlex + Redalyc + Latindex + Google Scholar &nbsp;|&nbsp;
  Rango empirico: {RANGO} &nbsp;|&nbsp;
  Teorias clasicas: sin restriccion &nbsp;|&nbsp;
  Gate global activo - Modo A tecnico compacto
</footer>
""", unsafe_allow_html=True)
