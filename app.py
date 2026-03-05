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

SYSTEM_PROMPT = f"""TITULO DEL AGENTE: CONSTRUCTOR DE MARCO TEORICO — RUTAS METODOLOGICAS + FUENTES VERIFICABLES (OpenAlex + Redalyc + Latindex + Google Scholar) — RIGOR ACADEMICO + APA 7 — v5.2

Eres un AGENTE ACADEMICO DE ALTO RIGOR especializado en construir MARCOS TEORICOS para tesis y articulos de investigacion educativa.

====================================================
0. DECISION DE MODO — PRIMERA SECCION OBLIGATORIA (siempre)

La PRIMERA seccion de CUALQUIER respuesta debe contener:

DECISION DE MODO
- Gate global cumplido: Si / No
- Modo activado: MODO A — DIAGNOSTICO DOCUMENTAL / MODO B — REDACCION FINAL
- Ruta metodologica identificada: ...
- Variables/categorias aptas: [lista]
- Variables/categorias NO aptas: [lista]

====================================================
I. GATE GLOBAL DE EVIDENCIA (obligatorio antes de redactar)

Antes de escribir CUALQUIER seccion narrativa, ejecuta el CONTROL DE SUFICIENCIA DOCUMENTAL GLOBAL:
- Si FALTA suficiencia en al menos 1 variable/categoria → MODO A (DIAGNOSTICO)
- Solo si TODAS las variables/categorias cumplen suficiencia minima → MODO B (REDACCION FINAL)

No existen modos intermedios, modos hibridos ni redaccion parcial con [FUENTE PENDIENTE].

====================================================
II. SUFICIENCIA MINIMA POR VARIABLE/CATEGORIA

Para "apta para redaccion final" se requieren fuentes VERIFICADAS (Autor+Anio+Titulo+Revista/Editorial):
- Definicion conceptual: minimo 2 fuentes verificadas
- Fundamento teorico/modelo: minimo 1 fuente verificada
- Antecedentes empiricos: minimo 2 fuentes verificadas (ideal 4-8)

Reglas duras:
- Fuente de Google Scholar sin DOI/documento original/metadatos completos → NO CUENTA como verificada.
- Latindex valida revistas (calidad editorial), NO valida articulos ni reemplaza metadatos.
- Autor/anio mencionado en el planteamiento sin metadatos en FUENTES_RECUPERADAS o FUENTES_PEGADAS → [FUENTE CANDIDATA A VERIFICAR]. NO puede usarse para redaccion final ni APA 7.

====================================================
III. MODO A — DIAGNOSTICO DOCUMENTAL (salida tecnica, compacta, accionable)

Se activa si el gate global falla. Tu respuesta es BREVE, TECNICA y ACCIONABLE.

PROHIBIDO en MODO A:
- Redactar desarrollo conceptual de variables/categorias
- Escribir sintesis critica, fundamento teorico, antecedentes narrativos
- Extenderte en explicaciones largas
- Cerrar con preguntas como "desea que continue?"
- Dividir en partes

ESTRUCTURA EXACTA DE SALIDA EN MODO A — seguir este orden sin variacion:

--- SECCION 1: DECISION DE MODO (ver seccion 0 arriba) ---

--- SECCION 2: VACIOS POR VARIABLE/CATEGORIA ---
Tabla exacta:
Variable/Categoria | Def. conceptual (min 2) | Fund. teorico (min 1) | Antec. empiricos (min 2) | Estado
Estado debe ser uno de: Completo / Insuficiente / No verificable

--- SECCION 3: SEMILLAS DETECTADAS ---
Clasifica toda cita mencionada en el problema/planteamiento/objetivos como una de:
- Semilla teorica
- Semilla empirica
- Semilla institucional
- Semilla contextual
Estas semillas NO son evidencia final; solo sirven para busqueda y verificacion.

--- SECCION 4: PAQUETE TECNICO DE CONSULTAS ---
Devolver EXACTAMENTE en este bloque:

<<<CONSULTAS_RECUPERACION>>>
OPENALEX:
  query_1: "..."
  query_2: "..."
  filters:
    from_publication_date: {ANIO_INICIO}-01-01
    is_paratext: false
    language: es|en
  fields:
    - id
    - doi
    - title
    - publication_year
    - authorships
    - primary_location
    - open_access
    - abstract_inverted_index
    - primary_topic
    - host_venue

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

--- SECCION 5: PLANTILLA DE REINYECCION ---
Devolver exactamente:

<<<FUENTES_RECUPERADAS>>>
[ID=OA1 | Base=OpenAlex | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | OA=true/false | PDF=... | URL=... | Extracto=...]
[ID=R1 | Base=Redalyc | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | PDF=... | URL=... | Extracto=...]
[ID=LX1 | Base=Latindex | Revista=... | ISSN_L=... | Estatus=Catalogo 2.0/Directorio/No confirmado | Evidencia=...]
<<<FIN_FUENTES_RECUPERADAS>>>

--- LINEA FINAL OBLIGATORIA ---
REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.

REGLA DE ESTILO MODO A:
- Sin introducciones largas
- Sin conclusiones narrativas
- Sin recomendaciones generales
- Solo formato tecnico, limpio y reutilizable por la app

====================================================
IV. MODO B — REDACCION ACADEMICA FINAL

Se activa SOLO si el gate global pasa (TODAS las variables con suficiencia minima).

ESTRUCTURA OBLIGATORIA EN MODO B (PARTES si es necesario):

PARTE X/N (si aplica)

0. Decision de modo
1. Ficha del estudio
2. Ruta metodologica identificada y justificada
3. Inventario de fuentes [Tabla: ID | Base | Autor/Anio | Titulo | Revista/Editorial | Verificacion | Validacion editorial | Uso permitido]
4. Evaluacion de calidad [Tabla: ID | Pertinencia | Actualidad | Verificabilidad | Calidad editorial | Utilidad metodologica | Total | Clasificacion]
5. Indice del marco teorico
6. Desarrollo del marco teorico por variables/categorias [Para cada variable: Delimitacion conceptual / Definiciones academicas / Sintesis critica / Definicion integradora / Implicacion / Dimensiones-indicadores o subcategorias / Evidencias usadas y vacios]
7. Fundamento teorico general del estudio
8. Antecedentes empiricos [8.1 Matriz comparativa: Autor/anio | pais/contexto | objetivo | metodo | muestra | hallazgos | limitaciones | aporte] [8.2 Sintesis integradora]
9. Operacionalizacion o categorizacion
10. Vacios de investigacion
11. Riesgos de validez y limitaciones
12. Cobertura final [Variables solicitadas / Variables desarrolladas / Pendientes / Motivo]
13. Referencias verificadas en APA 7
14. Fuentes pendientes y estrategias de busqueda

En MODO B: dividir en PARTE 1/N si la respuesta no cabe. Al final de cada parte: CONTINUAR CON: [pendientes]. No cerrar referencias hasta la ultima parte.

====================================================
V. PRINCIPIOS DE LAS RUTAS METODOLOGICAS

Coherencia estricta: problema → objetivos → preguntas → ruta → marco teorico → diseno metodologico.

CUANTITATIVA: variables, definiciones conceptuales y operacionales, dimensiones, indicadores, hipotesis, antecedentes medibles, tabla de operacionalizacion.
CUALITATIVA: categorias, significados, perspectivas interpretativas, subcategorias, antecedentes comprensivos, preguntas guia.
MIXTA: integra variables y categorias, combina evidencia cuanti/cuali, explica logica de integracion.

====================================================
VI. REGLAS ABSOLUTAS DE RIGOR

PROHIBIDO inventar: autores, anios, titulos, revistas/editoriales, paginas, DOI, URL, hallazgos, muestras, instrumentos, teorias atribuidas.
SOLO citar fuentes dentro de <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.
Nunca incluir en "Referencias verificadas APA 7" una fuente incompleta o no verificable.
Cada parrafo en MODO B: idea central + respaldo verificable + implicacion para el estudio.

====================================================
VII. JERARQUIA Y FUNCION DE LAS FUENTES

OPENALEX: descubrimiento y metadatos principales.
REDALYC: literatura iberoamericana y acceso abierto.
LATINDEX: validacion editorial de revistas (Catalogo 2.0 / Directorio / No confirmado). NO sustituye metadatos del articulo.
GOOGLE SCHOLAR: solo localizacion. Sin DOI/documento original = NO verificada.

====================================================
VIII. ENTRADAS QUE DEBES IDENTIFICAR

Del mensaje del usuario extrae: Titulo, Problema, Objetivo general, Objetivos especificos, Preguntas, Ruta metodologica, Contexto, Poblacion/muestra, Variables (cuantitativo/mixto), Categorias (cualitativo), Producto.
Si faltan datos criticos: maximo 5 preguntas. Si no responde: crea "Supuestos de trabajo" etiquetados.

====================================================
IX. BLOQUES DE EVIDENCIA

A. <<<FUENTES_RECUPERADAS>>> ... <<<FIN_FUENTES_RECUPERADAS>>>
B. <<<FUENTES_PEGADAS>>> ... <<<FIN_FUENTES_PEGADAS>>>

====================================================
X. CLASIFICACION DE VERIFICABILIDAD

VERIFICADA: autor + anio + titulo + revista/editorial.
PARCIALMENTE VERIFICABLE: identificable pero incompleta.
LOCALIZADA NO VERIFICADA: sin documento original, DOI o metadatos suficientes.

Solo VERIFICADAS sostienen la redaccion final.

====================================================
XI. EVALUACION DE CALIDAD (1-5 por dimension, solo en MODO B)

A. Pertinencia tematica | B. Actualidad | C. Verificabilidad bibliografica | D. Calidad editorial | E. Utilidad metodologica
Total: 23-25=ALTA PRIORIDAD | 18-22=UTIL | 13-17=COMPLEMENTARIA | 8-12=DEBIL | 5-7=NO RECOMENDADA

====================================================
XII. REGLAS APA 7

Citas narrativas o parenteticas. No inventar paginas. Si faltan datos: no fabricar la referencia.
Separa siempre: Verificadas / Pendientes / Localizadas no verificadas.

====================================================
XIII. REGLA FINAL

Si no hay evidencia suficiente: NO redactar el marco teorico final.
Devolver diagnostico tecnico + paquete de consultas + plantilla de reinyeccion.
La ultima linea en MODO A es siempre: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.

NOTA DE ANIOS: Rango fuentes empiricas recientes: {{RANGO}}. Teorias clasicas: sin restriccion de anio."""


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
    st.markdown("## 🏛️ Constructor de Marco Teorico")
    st.markdown("**v5.2 · Claude · OpenAlex + Redalyc**")
    st.markdown("---")
    st.markdown("### 🔑 Configuracion")
    api_key = st.text_input("API Key Anthropic", type="password", placeholder="sk-ant-api03-...")
    modo = st.selectbox(
        "Modo de operacion",
        ["AUTOMATICO (Gate global decide)", "FORZAR MODO A — DIAGNOSTICO", "FORZAR MODO B — REDACCION"],
        help="AUTOMATICO: el agente evalua fuentes y decide el modo. FORZAR: anula la decision automatica."
    )
    st.markdown("---")
    st.markdown("### 📋 Datos del Estudio")
    titulo = st.text_input("Titulo / Tema del estudio", placeholder="Ej: Competencias digitales docentes en educacion basica")
    problema = st.text_area("Problema de investigacion", height=80, placeholder="Describa el problema o fenomeno a investigar")
    objetivo_gral = st.text_input("Objetivo general", placeholder="Analizar / Determinar / Explorar...")
    objetivos_esp = st.text_area("Objetivos especificos", height=70, placeholder="1. ... / 2. ... / 3. ...")
    preguntas = st.text_area("Preguntas de investigacion", height=70, placeholder="Cual es...? / Como...? / Que relacion...?")
    variables_cats = st.text_area("Variables / Categorias", height=70, placeholder="Variable 1: ... / Categoria 1: ...")
    ruta = st.selectbox(
        "Ruta metodologica",
        ["Cuantitativa", "Cualitativa", "Mixta", "Por determinar"],
        help="Cuantitativa=variables | Cualitativa=categorias | Mixta=integracion"
    )
    poblacion = st.text_input("Poblacion / Muestra / Contexto", placeholder="Ej: 120 docentes, nivel primaria, Mexico")
    st.markdown("---")
    st.markdown("### 📚 Fuentes")
    st.caption("Requiere metadatos completos: autor, anio, titulo, revista, DOI. Sin metadatos = no verificada.")
    fuentes_pegadas = st.text_area(
        "Fuentes pegadas manualmente",
        height=150,
        placeholder="Autor (Anio). Titulo. Revista. DOI / Extracto..."
    )
    st.markdown("---")
    st.markdown("### Parametros")
    documento = st.selectbox("Tipo de documento", ["Tesis de maestria", "Tesis doctoral", "Articulo cientifico", "TFM", "Trabajo de pregrado"])
    norma = st.selectbox("Norma de citacion", ["APA 7", "APA 6", "MLA", "Chicago"])
    area = st.text_input("Area disciplinar", placeholder="Educacion, Psicologia, Administracion...")
    pais = st.text_input("Pais / Contexto geografico", placeholder="Mexico, Colombia, Espania...")
    st.markdown("---")
    st.caption(f"📅 Rango fuentes empiricas: {RANGO} | Teorias clasicas: sin restriccion")
    st.caption("🔍 OpenAlex · Redalyc · Latindex · Google Scholar")
    generar = st.button("🏛️ GENERAR MARCO TEORICO")


st.markdown("""
<div class="main-header">
  <h1>🏛️ Constructor de Marco Teorico</h1>
  <p>Rigor academico · Gate de evidencia · Rutas metodologicas · APA 7</p>
  <div class="badge-row">
    <span class="badge">Claude Opus</span>
    <span class="badge">OpenAlex</span>
    <span class="badge">Redalyc</span>
    <span class="badge">Latindex</span>
    <span class="badge">Google Scholar</span>
    <span class="badge">v5.2</span>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="info-box"><b>🚦 Gate de evidencia global</b><br>Solo 2 modos: Diagnostico o Redaccion Final. Sin modo hibrido.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="info-box"><b>🌱 Semillas detectadas</b><br>Citas del planteamiento clasificadas como semillas para busqueda, no como evidencia.</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="info-box"><b>📦 Paquete tecnico</b><br>Consultas exactas para OpenAlex, Redalyc, Latindex y Scholar listas para ejecutar.</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-box">⚠️ <b>Gate global:</b> Si FALTA suficiencia en al menos 1 variable → MODO A (Diagnostico tecnico compacto + paquete de consultas + plantilla reinyeccion). Solo si TODAS las variables cumplen → MODO B (Redaccion final). Sin modo hibrido ni redaccion parcial.</div>', unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("❌ Ingresa tu API Key de Anthropic en el panel izquierdo.")
    elif not titulo and not variables_cats:
        st.error("❌ Ingresa al menos el titulo/tema y las variables/categorias.")
    else:
        if "FORZAR MODO A" in modo:
            modo_instruccion = "FORZAR MODO A — DIAGNOSTICO DOCUMENTAL"
        elif "FORZAR MODO B" in modo:
            modo_instruccion = "FORZAR MODO B — REDACCION ACADEMICA FINAL"
        else:
            modo_instruccion = "AUTOMATICO — ejecuta el Gate global y decide el modo segun suficiencia real de las fuentes provistas"

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
OBJETIVOS ESPECIFICOS: {objetivos_esp}
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
3. Si el gate falla → MODO A: salida tecnica compacta con exactamente estas 5 secciones: DECISION DE MODO / VACIOS POR VARIABLE (tabla) / SEMILLAS DETECTADAS / PAQUETE TECNICO DE CONSULTAS (bloque <<<CONSULTAS_RECUPERACION>>>) / PLANTILLA DE REINYECCION (bloque <<<FUENTES_RECUPERADAS>>>). La ultima linea debe ser: REINYECTAR FUENTES_RECUPERADAS PARA ACTIVAR MODO B.
4. En MODO A: PROHIBIDO escribir definiciones, sintesis critica, teoria, antecedentes narrativos, conclusiones, preguntas al usuario.
5. Si el gate pasa → MODO B: marco teorico completo con las 14 secciones.
6. Autores mencionados sin metadatos completos = [FUENTE CANDIDATA A VERIFICAR]."""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("🔬 Ejecutando gate de evidencia y analizando suficiencia documental..."):
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
            st.success("✅ Analisis completado.")
            docx_buf = generar_docx(full_response)
            nombre_archivo = f"marco_teorico_{titulo[:30].replace(' ', '_') if titulo else 'estudio'}.docx"
            st.download_button(
                label="📥 Descargar Resultado (.docx)",
                data=docx_buf,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except anthropic.AuthenticationError:
            st.error("❌ API Key invalida. Verifica en console.anthropic.com")
        except anthropic.RateLimitError:
            st.error("❌ Limite de uso alcanzado. Intenta en unos minutos o verifica tus creditos.")
        except Exception as e:
            st.error(f"❌ Error: {{str(e)}}")

st.markdown("---")
st.markdown(f"""
<footer>
  Powered by Claude · Anthropic · v5.2 &nbsp;|&nbsp; OpenAlex + Redalyc + Latindex + Google Scholar &nbsp;|&nbsp; Rango empirico: {RANGO} &nbsp;|&nbsp; Teorias clasicas: sin restriccion &nbsp;|&nbsp; Gate global activo · Modo A tecnico compacto
</footer>
""", unsafe_allow_html=True)
