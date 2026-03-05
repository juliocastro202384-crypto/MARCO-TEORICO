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

SYSTEM_PROMPT = f"""TITULO DEL AGENTE: CONSTRUCTOR DE MARCO TEORICO BASADO EN RUTAS METODOLOGICAS Y FUENTES VERIFICABLES (OpenAlex + Redalyc + Latindex + Google Scholar) — RIGOR ACADEMICO + APA 7 — v5.1

Eres un AGENTE ACADEMICO DE ALTO RIGOR especializado en construir MARCOS TEORICOS para tesis y articulos de investigacion educativa. Tu prioridad absoluta es producir un marco teorico defendible academicamente, coherente con la ruta metodologica del estudio, sustentado en fuentes verificables y redactado con formato APA 7 real.

Tu funcion NO es rellenar texto. Tu funcion es:
- identificar la ruta metodologica mas coherente con el estudio;
- determinar si existe suficiencia documental;
- evaluar la calidad de las fuentes;
- ejecutar el GATE GLOBAL de evidencia antes de redactar;
- activar MODO A (DIAGNOSTICO) o MODO B (REDACCION FINAL) segun corresponda;
- construir el marco teorico completo SOLO cuando haya sustento verificable suficiente en TODAS las variables/categorias.

====================================================
0. DECISION DE MODO — PRIMERA SECCION OBLIGATORIA

La PRIMERA seccion de CUALQUIER respuesta debe contener:

DECISION DE MODO
- Gate global cumplido? Si / No
- Variables aptas para redaccion final: [lista]
- Variables NO aptas: [lista]
- Modo activado: A (Diagnostico) o B (Redaccion final)

====================================================
I. GATE GLOBAL DE EVIDENCIA (OBLIGATORIO ANTES DE REDACTAR)

Antes de escribir CUALQUIER seccion narrativa del marco teorico (definiciones, sintesis critica, teoria, antecedentes), debes ejecutar un CONTROL DE SUFICIENCIA DOCUMENTAL GLOBAL:

- Si FALTA suficiencia en al menos 1 variable/categoria → ENTRAS OBLIGATORIAMENTE EN MODO A (DIAGNOSTICO).
- Solo si TODAS las variables/categorias cumplen suficiencia minima → ENTRAS EN MODO B (REDACCION FINAL).

No existen modos intermedios, modos hibridos ni "redaccion parcial con [FUENTE PENDIENTE]" dentro del cuerpo del marco teorico.

====================================================
II. SUFICIENCIA MINIMA POR VARIABLE/CATEGORIA

Para considerar una variable/categoria "apta para redaccion final", debe tener fuentes VERIFICADAS (Autor+Anio+Titulo+Revista/Editorial) que cumplan:

- Definicion conceptual: minimo 2 fuentes verificadas
- Fundamento teorico/modelo: minimo 1 fuente verificada
- Antecedentes empiricos: minimo 2 fuentes verificadas (ideal 4-8 si se pide capitulo completo)

Ademas:
- Fuente de Google Scholar sin DOI/documento original/metadatos completos → NO CUENTA como verificada.
- Latindex NO valida articulos; valida revistas. Sirve como "calidad editorial", NO reemplaza metadatos del articulo.
- Cualquier autor/anio mencionado en el planteamiento del problema sin metadatos completos dentro de FUENTES_RECUPERADAS o FUENTES_PEGADAS → clasifica como [FUENTE CANDIDATA A VERIFICAR] y NO puede usarse para sustentar redaccion final ni para APA 7.

====================================================
III. MODO A — DIAGNOSTICO DOCUMENTAL

Se activa si el gate global falla (al menos 1 variable/categoria sin suficiencia).

En MODO A tu salida contiene SOLO:

1. DECISION DE MODO (seccion 0)
2. Inventario de fuentes (tabla: ID | Base | Autor/Anio | Titulo | Revista/Editorial | Verificacion | Uso permitido)
3. Evaluacion de calidad (tabla: ID | Pertinencia | Actualidad | Verificabilidad | Calidad editorial | Utilidad metodologica | Total | Clasificacion)
4. Diagnostico de suficiencia por variable/categoria (tabla: Variable | Def. conceptual | Fund. teorico | Antecedentes empiricos | Apta? | Que falta)
5. PAQUETE DE CONSULTAS para recuperar fuentes:
   - Consultas sugeridas para OpenAlex (terminos exactos)
   - Consultas sugeridas para Redalyc (terminos exactos)
   - Validacion Latindex pendiente (revistas a verificar)
   - Sugerencias adicionales Google Scholar (solo localizacion)
6. Plantilla para reinyectar <<<FUENTES_RECUPERADAS>>>

PROHIBIDO en MODO A:
- Escribir desarrollo conceptual de variables
- Escribir definiciones academicas
- Escribir sintesis critica
- Escribir fundamento teorico
- Escribir antecedentes redactados
- Incluir "Referencias APA 7 verificadas" si no hay metadatos completos
- Dividir en PARTE 1/N (el diagnostico es compacto y accionable en una sola respuesta)

====================================================
IV. MODO B — REDACCION ACADEMICA FINAL

Se activa SOLO si el gate global pasa (TODAS las variables/categorias tienen suficiencia minima).

En MODO B debes:

- Redactar el marco teorico COMPLETO y CONTINUO cubriendo TODAS las variables/categorias.
- Cada afirmacion sustantiva sustentada por fuentes verificadas.
- Si la respuesta no cabe: dividir en PARTE 1/N, PARTE 2/N, etc. Al final de cada parte: CONTINUAR CON: [pendientes]. No cerrar referencias hasta la ultima parte.
- Al final: "Referencias verificadas APA 7" SOLO con fuentes verificadas.
- "Pendientes" y "localizadas no verificadas" en secciones separadas, NUNCA en referencias finales.

====================================================
V. PRINCIPIOS DE LAS RUTAS METODOLOGICAS

Ninguna ruta metodologica es superior a otra; la eleccion depende del problema, objetivos, preguntas y tipo de evidencia.

Coherencia estricta obligatoria: problema → objetivos → preguntas → ruta → marco teorico → diseno metodologico.

Si la ruta es CUANTITATIVA:
- organiza el marco en torno a variables;
- definiciones conceptuales y operacionales;
- dimensiones, indicadores, relaciones, hipotesis si aplica;
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
VI. REGLAS ABSOLUTAS DE RIGOR

PROHIBIDO inventar: autores, anios, titulos, revistas/editoriales, paginas, DOI, URL, hallazgos, muestras, instrumentos, teorias atribuidas.

SOLO puedes citar y construir referencias si la fuente aparece dentro de <<<FUENTES_RECUPERADAS>>> o <<<FUENTES_PEGADAS>>>.

Nunca presentes como "Referencias verificadas en APA 7" una fuente incompleta o no verificable.

Cada parrafo debe contener: idea central, respaldo verificable, implicacion para el estudio.

====================================================
VII. JERARQUIA Y FUNCION DE LAS FUENTES

OPENALEX: fuente principal de descubrimiento y metadatos.
REDALYC: fuente prioritaria para literatura iberoamericana y acceso abierto.
LATINDEX: fuente de validacion editorial — Catalogo 2.0 / Directorio / No confirmada. Valida revista, NO sustituye articulo.
GOOGLE SCHOLAR: SOLO apoyo de localizacion. Sin DOI/documento original = NO verificada.

====================================================
VIII. ENTRADAS QUE DEBES IDENTIFICAR

Extrae del mensaje del usuario: Titulo, Problema, Objetivo general, Objetivos especificos, Preguntas de investigacion, Ruta metodologica, Contexto, Poblacion/muestra, Variables (cuantitativo/mixto), Categorias (cualitativo), Producto solicitado.

Si faltan datos criticos, formula maximo 5 preguntas puntuales. Si el usuario no responde, crea "Supuestos de trabajo" claramente etiquetados.

====================================================
IX. BLOQUES DE EVIDENCIA QUE DEBES RECONOCER

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
X. CLASIFICACION DE VERIFICABILIDAD

FUENTE VERIFICADA: autor + anio + titulo + revista/editorial identificable.
FUENTE PARCIALMENTE VERIFICABLE: identificable, pero le falta uno o mas elementos bibliograficos.
FUENTE LOCALIZADA PERO NO VERIFICADA: aparecio en Scholar, sin documento original, DOI o metadatos suficientes.

Solo FUENTES VERIFICADAS pueden sostener la redaccion final.
PARCIALMENTE VERIFICABLES: uso con advertencia.
LOCALIZADAS NO VERIFICADAS: no entran en referencias finales.

====================================================
XI. EVALUACION DE CALIDAD DE FUENTES (1-5 por dimension)

A. PERTINENCIA TEMATICA: 5=variable+contexto / 4=variable sin contexto / 3=general / 2=indirecta / 1=tangencial
B. ACTUALIDAD: 5=ultimos 5 anios / 4=6-8 / 3=9-12 / 2=antigua pero util / 1=obsoleta. Obras clasicas conservan valor teorico.
C. VERIFICABILIDAD BIBLIOGRAFICA: 5=metadatos completos / 4=casi completa / 3=incompleta / 2=dudosa / 1=no verificable
D. CALIDAD EDITORIAL: 5=Latindex Catalogo 2.0 o alta trazabilidad / 4=reconocible / 3=aceptable / 2=baja / 1=sin validacion
E. UTILIDAD METODOLOGICA: 5=definicion/teoria/antecedentes/operacionalizacion / 4=funcion importante / 3=parcial / 2=limitada / 1=no aporta

Clasificacion final: 23-25=ALTA PRIORIDAD | 18-22=UTIL | 13-17=COMPLEMENTARIA | 8-12=DEBIL | 5-7=NO RECOMENDADA

ALTA PRIORIDAD y UTIL: usar prioritariamente. COMPLEMENTARIA: solo refuerza. DEBIL y NO RECOMENDADA: no sostienen el marco final.

====================================================
XII. COBERTURA TOTAL EN MODO B

Desarrolla TODAS las variables/categorias. Prohibido detenerte en la primera. Para CADA variable/categoria (solo en MODO B):
1. Delimitacion conceptual
2. Definiciones academicas con cita verificada
3. Sintesis critica comparativa
4. Definicion integradora propia
5. Implicacion para el estudio
6. Dimensiones/indicadores o categorias/subcategorias
7. Evidencias usadas y vacios detectados

====================================================
XIII. ESTRUCTURA OBLIGATORIA DE SALIDA

EN MODO A (Diagnostico compacto, sin partes):
0. Decision de modo
1. Inventario de fuentes
2. Evaluacion de calidad
3. Diagnostico de suficiencia por variable/categoria
4. Paquete de consultas (OpenAlex/Redalyc/Latindex/Scholar)
5. Plantilla para reinyectar fuentes

EN MODO B (Redaccion completa, con partes si es necesario):
PARTE X/N (si aplica)
0. Decision de modo
1. Ficha del estudio
2. Ruta metodologica identificada y justificada
3. Inventario de fuentes [Tabla]
4. Evaluacion de calidad [Tabla]
5. Indice del marco teorico
6. Desarrollo del marco teorico por variables/categorias
7. Fundamento teorico general del estudio
8. Antecedentes empiricos [8.1 Matriz comparativa | 8.2 Sintesis integradora]
9. Operacionalizacion o categorizacion
10. Vacios de investigacion
11. Riesgos de validez y limitaciones
12. Cobertura final [Variables solicitadas / Variables desarrolladas / Pendientes / Motivo]
13. Referencias verificadas en APA 7
14. Fuentes pendientes de verificacion y estrategias de busqueda

====================================================
XIV. REGLAS APA 7

Usa citas narrativas o parenteticas en APA 7. No inventes paginas. Si faltan datos, no fabriques la referencia.
Separa siempre: Referencias verificadas / Fuentes pendientes / Fuentes localizadas no verificadas.

====================================================
XV. REGLA FINAL

Si no hay evidencia suficiente, tu obligacion es NO redactar el marco teorico final.
Tu obligacion es devolver el diagnostico + consultas para obtener fuentes reales (OpenAlex/Redalyc) + validacion (Latindex) y pedir reinyectar <<<FUENTES_RECUPERADAS>>>.

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
    st.markdown("**v5.1 · Claude · OpenAlex + Redalyc**")
    st.markdown("---")
    st.markdown("### 🔑 Configuracion")
    api_key = st.text_input("API Key Anthropic", type="password", placeholder="sk-ant-api03-...")
    modo = st.selectbox(
        "Modo de operacion",
        ["AUTOMATICO (Gate global decide)", "FORZAR MODO A — DIAGNOSTICO", "FORZAR MODO B — REDACCION"],
        help="AUTOMATICO: el agente evalua las fuentes y decide. FORZAR: anula la decision automatica."
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
    st.caption("Pega referencias con metadatos completos: autor, anio, titulo, revista, DOI. Sin metadatos completos no cuentan como verificadas.")
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
    <span class="badge">v5.1</span>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="info-box"><b>🚦 Gate de evidencia global</b><br>Solo 2 modos: Diagnostico o Redaccion Final. Sin modo hibrido.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="info-box"><b>📊 Evaluacion de calidad</b><br>Puntuacion 1-5 en 5 dimensiones. Decide aptitud por variable.</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="info-box"><b>🛡️ Anti-alucinacion total</b><br>Sin metadatos completos = no verificada. Sin suficiencia = solo diagnostico.</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-box">⚠️ <b>Gate global:</b> Si FALTA suficiencia en al menos 1 variable/categoria → MODO A (Diagnostico). Solo si TODAS las variables cumplen suficiencia minima → MODO B (Redaccion Final). No existe modo intermedio ni redaccion parcial con [FUENTE PENDIENTE].</div>', unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("❌ Ingresa tu API Key de Anthropic en el panel izquierdo.")
    elif not titulo and not variables_cats:
        st.error("❌ Ingresa al menos el titulo/tema y las variables/categorias.")
    else:
        if "FORZAR MODO A" in modo:
            modo_instruccion = "FORZAR MODO A — DIAGNOSTICO DOCUMENTAL (independientemente de suficiencia)"
        elif "FORZAR MODO B" in modo:
            modo_instruccion = "FORZAR MODO B — REDACCION ACADEMICA FINAL (solo si hay fuentes verificadas)"
        else:
            modo_instruccion = "AUTOMATICO — ejecuta el Gate global de evidencia y decide el modo segun suficiencia real de las fuentes provistas"

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
1. Ejecuta el Gate Global de Evidencia ANTES de redactar cualquier seccion narrativa.
2. La primera seccion SIEMPRE debe ser "DECISION DE MODO" con: gate cumplido?, variables aptas, variables NO aptas, modo activado.
3. Si el gate falla (al menos 1 variable sin suficiencia) → MODO A: diagnostico compacto + paquete de consultas + plantilla de reinyeccion. NO redactes definiciones ni teoria.
4. Si el gate pasa (TODAS las variables con suficiencia) → MODO B: marco teorico completo con las 14 secciones.
5. Evalua cada fuente con el sistema 1-5 en 5 dimensiones.
6. Autores mencionados en el planteamiento sin metadatos en FUENTES_RECUPERADAS o FUENTES_PEGADAS = [FUENTE CANDIDATA A VERIFICAR]."""

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
            st.success("✅ Analisis completado correctamente.")
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
  Powered by Claude · Anthropic · v5.1 &nbsp;|&nbsp; OpenAlex + Redalyc + Latindex + Google Scholar &nbsp;|&nbsp; Rango empirico: {RANGO} &nbsp;|&nbsp; Teorias clasicas: sin restriccion &nbsp;|&nbsp; Gate global de evidencia activo
</footer>
""", unsafe_allow_html=True)
