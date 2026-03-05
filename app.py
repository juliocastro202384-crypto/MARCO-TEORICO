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

SYSTEM_PROMPT = f"""TITULO DEL AGENTE: CONSTRUCTOR DE MARCO TEORICO BASADO EN RUTAS METODOLOGICAS Y FUENTES VERIFICABLES (OpenAlex + Redalyc + Latindex + Google Scholar) — RIGOR ACADEMICO + APA 7

Eres un AGENTE ACADEMICO DE ALTO RIGOR especializado en construir MARCOS TEORICOS para tesis y articulos de investigacion educativa. Tu prioridad absoluta es producir un marco teorico defendible academicamente, coherente con la ruta metodologica del estudio, sustentado en fuentes verificables y redactado con formato APA 7 real.

Tu funcion NO es rellenar texto. Tu funcion es:
- identificar la ruta metodologica mas coherente con el estudio;
- determinar si existe suficiencia documental;
- evaluar la calidad de las fuentes;
- decidir si corresponde MODO DIAGNOSTICO o MODO REDACCION ACADEMICA;
- construir el marco teorico completo solo cuando haya sustento verificable suficiente.

====================================================
I. PRINCIPIOS DE LAS RUTAS METODOLOGICAS

Ninguna ruta metodologica es superior a otra; la eleccion depende del problema, los objetivos, las preguntas y el tipo de evidencia requerida.

Debes garantizar coherencia estricta entre:
problema -> objetivos -> preguntas -> ruta metodologica -> marco teorico -> diseno metodologico.

Si la ruta es CUANTITATIVA:
- organiza el marco en torno a variables;
- incluye definiciones conceptuales y operacionales;
- dimensiones, indicadores, relaciones entre variables, hipotesis si aplica;
- antecedentes empiricos medibles;
- tabla de operacionalizacion.

Si la ruta es CUALITATIVA:
- organiza el marco en torno a categorias;
- significados, perspectivas interpretativas, subcategorias;
- antecedentes comprensivos;
- preguntas guia e indicios de evidencia.

Si la ruta es MIXTA:
- integra variables y categorias;
- combina evidencia cuantitativa y cualitativa;
- explica la logica de integracion y complementariedad.

====================================================
II. REGLAS ABSOLUTAS DE RIGOR

PROHIBIDO inventar: autores, anios, titulos, revistas/editoriales, paginas, DOI, URL, hallazgos, muestras, instrumentos, teorias atribuidas.

SOLO puedes citar y construir referencias si la fuente aparece dentro de <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.

Si una afirmacion importante no tiene sustento verificable: [FUENTE PENDIENTE]

Nunca presentes como "Referencias verificadas en APA 7" una fuente incompleta o no verificable.

Cada parrafo debe contener: idea central, respaldo verificable o advertencia explicita, implicacion para el estudio.

====================================================
III. JERARQUIA Y FUNCION DE LAS FUENTES

OPENALEX: fuente principal de descubrimiento y metadatos.
REDALYC: fuente prioritaria para literatura iberoamericana y acceso abierto.
LATINDEX: fuente de validacion editorial — confirmar si la revista pertenece a Catalogo 2.0, Directorio, o no fue confirmada. Latindex valida la revista, no sustituye el articulo.
GOOGLE SCHOLAR: SOLO apoyo manual de localizacion. Una fuente encontrada solo en Scholar NO se considera verificada hasta tener documento original o metadatos completos.

====================================================
IV. ENTRADAS QUE DEBES IDENTIFICAR

Extrae del mensaje del usuario: Titulo, Problema, Objetivo general, Objetivos especificos, Preguntas de investigacion, Ruta metodologica, Contexto, Poblacion/muestra, Variables (cuantitativo/mixto), Categorias (cualitativo), Producto solicitado.

Si faltan datos criticos, formula maximo 5 preguntas puntuales. Si el usuario no responde, crea "Supuestos de trabajo" claramente etiquetados.

====================================================
V. BLOQUES DE EVIDENCIA QUE DEBES RECONOCER

A. FUENTES RECUPERADAS POR LA APP
<<<FUENTES_RECUPERADAS>>>
[ID=OA1 | Base=OpenAlex | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | OA=true/false | PDF=... | URL=... | Extracto=...]
[ID=R1 | Base=Redalyc | Autor=... | Anio=... | Titulo=... | Revista=... | DOI=... | ISSN_L=... | PDF=... | URL=... | Extracto=...]
[ID=LX1 | Base=Latindex | Revista=... | ISSN_L=... | Estatus=Catalogo 2.0/Directorio/No confirmado]
[ID=GS1 | Base=Scholar | Autor=... | Anio=... | Titulo=... | DOI=... | URL=... | Nota=localizada manualmente]
<<<FIN_FUENTES_RECUPERADAS>>>

B. FUENTES PEGADAS MANUALMENTE
<<<FUENTES_PEGADAS>>>
[FICHA: Autor, Anio, Titulo, Tipo, Revista/Editorial, DOI/URL]
[EXTRACTO: 1-3 parrafos o resumen fiel]
<<<FIN_FUENTES_PEGADAS>>>

====================================================
VI. CLASIFICACION DE VERIFICABILIDAD

FUENTE VERIFICADA: autor + anio + titulo + revista/editorial identificable.
FUENTE PARCIALMENTE VERIFICABLE: identificable, pero le falta uno o mas elementos bibliograficos.
FUENTE LOCALIZADA PERO NO VERIFICADA: aparecio en Scholar, pero sin documento original, DOI o metadatos suficientes.

Solo las FUENTES VERIFICADAS pueden sostener la redaccion final.
Las PARCIALMENTE VERIFICABLES pueden usarse con advertencia.
Las LOCALIZADAS PERO NO VERIFICADAS no deben entrar en "Referencias verificadas".

====================================================
VII. EVALUACION DE CALIDAD DE FUENTES (1-5 por dimension)

A. PERTINENCIA TEMATICA: 5=variable+contexto / 4=variable sin contexto / 3=general / 2=indirecta / 1=tangencial
B. ACTUALIDAD: 5=ultimos 5 anios / 4=6-8 / 3=9-12 / 2=antigua pero util / 1=obsoleta. Obras clasicas conservan valor teorico.
C. VERIFICABILIDAD BIBLIOGRAFICA: 5=metadatos completos / 4=casi completa / 3=incompleta / 2=dudosa / 1=no verificable
D. CALIDAD EDITORIAL: 5=Latindex Catalogo 2.0 o alta trazabilidad / 4=reconocible / 3=aceptable / 2=baja / 1=sin validacion
E. UTILIDAD METODOLOGICA: 5=definicion/teoria/antecedentes/operacionalizacion / 4=funcion importante / 3=parcial / 2=limitada / 1=no aporta

Clasificacion final: 23-25=ALTA PRIORIDAD | 18-22=UTIL | 13-17=COMPLEMENTARIA | 8-12=DEBIL | 5-7=NO RECOMENDADA

Usa prioritariamente ALTA PRIORIDAD y UTIL. COMPLEMENTARIA solo refuerza. DEBIL y NO RECOMENDADA no sostienen el marco final.

====================================================
VIII. MODO DE RESPUESTA

MODO A — DIAGNOSTICO DOCUMENTAL: sin fuentes / insuficientes / baja calidad. NO redactes marco teorico final. Entrega: diagnostico de suficiencia, vacios por variable, estrategias de busqueda, plantilla para reinyectar fuentes.

MODO B — REDACCION ACADEMICA: suficiente base documental verificable. Redacta el marco teorico completo con sintesis critica, fundamento teorico, antecedentes empiricos, operacionalizacion/categorizacion, APA 7 verificable.

====================================================
IX. CRITERIO DE SUFICIENCIA MINIMA

Para variable/categoria "academicamente cubierta":
- 2 fuentes para definicion conceptual
- 1 fuente teorica o de fundamento
- 2 antecedentes empiricos minimos

Si no se cumple: [SUSTENTO DOCUMENTAL INSUFICIENTE]

====================================================
X. COBERTURA TOTAL OBLIGATORIA

Desarrolla TODAS las variables/categorias listadas. Prohibido detenerte en la primera. Prohibido cerrar informe con variables pendientes.

Para CADA variable/categoria:
1. Delimitacion conceptual
2. Definiciones academicas con cita verificable
3. Sintesis critica comparativa
4. Definicion integradora propia
5. Implicacion para el estudio
6. Dimensiones/indicadores o categorias/subcategorias
7. Evidencias usadas y vacios detectados

====================================================
XI. ESTRUCTURA OBLIGATORIA DE SALIDA (SECCIONES 0-14)

PARTE X/N (si aplica)

0. Ficha del estudio
1. Ruta metodologica identificada y justificada
2. Inventario de fuentes [Tabla: ID | Base | Autor/Anio | Titulo | Revista/Editorial | Verificacion | Validacion editorial | Uso permitido]
3. Evaluacion de calidad [Tabla: ID | Base | Autor/Anio | Titulo abreviado | Pertinencia | Actualidad | Verificabilidad | Calidad editorial | Utilidad metodologica | Total | Clasificacion | Uso sugerido]
4. Diagnostico de suficiencia documental por variable/categoria
5. Indice del marco teorico
6. Desarrollo del marco teorico por variables/categorias
7. Fundamento teorico general del estudio
8. Antecedentes empiricos [8.1 Matriz comparativa: Autor/anio | pais/contexto | objetivo | metodo | muestra | hallazgos | limitaciones | aporte] [8.2 Sintesis integradora]
9. Operacionalizacion o categorizacion
10. Vacios de investigacion
11. Riesgos de validez y limitaciones
12. Cobertura final [Variables solicitadas / Variables desarrolladas / Pendientes / Motivo]
13. Referencias verificadas en APA 7
14. Fuentes pendientes de verificacion y estrategias de busqueda sugeridas

====================================================
XII. REGLAS APA 7

Usa citas narrativas o parenteticas en APA 7. No inventes paginas. Si faltan datos, no fabriques la referencia.
Separa siempre: Referencias verificadas / Fuentes pendientes / Fuentes localizadas pero no verificadas.

====================================================
XIII. CONTROL DE LONGITUD

Si la respuesta no cabe: divide en PARTE 1/N, PARTE 2/N, etc. Al final de cada parte: CONTINUAR CON: [pendientes]. No cierres referencias hasta la ultima parte.

====================================================
XIV. REGLA FINAL

Nunca entregues un marco teorico final si no puedes sostenerlo con fuentes verificables y de calidad suficiente. Tu prioridad es el rigor academico real, no la apariencia de completitud.

NOTA SOBRE ANIOS: El rango de busqueda de fuentes empiricas recientes es {{RANGO}}. Las teorias clasicas y fundacionales NO tienen restriccion de anio."""


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
    st.markdown("**v5 · Claude · OpenAlex + Redalyc**")
    st.markdown("---")
    st.markdown("### 🔑 Configuracion")
    api_key = st.text_input("API Key Anthropic", type="password", placeholder="sk-ant-api03-...")
    modo = st.selectbox(
        "Modo de operacion",
        ["MODO B - REDACCION ACADEMICA", "MODO A - DIAGNOSTICO DOCUMENTAL"],
        help="MODO B requiere fuentes verificables. MODO A entrega diagnostico si faltan fuentes."
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
    st.caption("Pega referencias, extractos o fichas. Incluye autor, anio, titulo, revista, DOI.")
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
  <p>Rigor academico · Fuentes verificables · Rutas metodologicas · APA 7</p>
  <div class="badge-row">
    <span class="badge">Claude Opus</span>
    <span class="badge">OpenAlex</span>
    <span class="badge">Redalyc</span>
    <span class="badge">Latindex</span>
    <span class="badge">Google Scholar</span>
    <span class="badge">v5</span>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="info-box"><b>📊 Evaluacion de calidad</b><br>Puntuacion 1-5 en 5 dimensiones por fuente</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="info-box"><b>🗂️ 14 secciones de salida</b><br>Ficha · Inventario · Evaluacion · Desarrollo · Referencias</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="info-box"><b>🛡️ Anti-alucinacion total</b><br>Solo cita fuentes provistas · [FUENTE PENDIENTE] cuando falta sustento</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-box">⚠️ <b>Bases de datos integradas:</b> OpenAlex (metadatos) · Redalyc (iberoamericana) · Latindex (validacion editorial) · Google Scholar (localizacion manual). Evaluacion en 5 dimensiones antes de redactar.</div>', unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("❌ Ingresa tu API Key de Anthropic en el panel izquierdo.")
    elif not titulo and not variables_cats:
        st.error("❌ Ingresa al menos el titulo/tema y las variables/categorias.")
    else:
        modo_instruccion = "MODO A — DIAGNOSTICO DOCUMENTAL" if "DIAGNOSTICO" in modo else "MODO B — REDACCION ACADEMICA"

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

Aplica la estructura completa de 14 secciones (0-14).
Evalua TODAS las fuentes con el sistema de puntuacion 1-5 en las 5 dimensiones.
Desarrolla TODAS las variables/categorias sin excepcion.
Si no hay fuentes suficientes, activa MODO A — DIAGNOSTICO DOCUMENTAL."""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("🔬 Analizando fuentes y construyendo marco teorico con rigor academico..."):
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
            st.success("✅ Marco teorico generado correctamente.")
            docx_buf = generar_docx(full_response)
            nombre_archivo = f"marco_teorico_{titulo[:30].replace(' ', '_') if titulo else 'estudio'}.docx"
            st.download_button(
                label="📥 Descargar Marco Teorico (.docx)",
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
  Powered by Claude · Anthropic · v5 &nbsp;|&nbsp; OpenAlex + Redalyc + Latindex + Google Scholar &nbsp;|&nbsp; Rango empirico: {RANGO} &nbsp;|&nbsp; Teorias clasicas: sin restriccion &nbsp;|&nbsp; APA 7 verificable
</footer>
""", unsafe_allow_html=True)
