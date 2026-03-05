import streamlit as st
import anthropic
from docx import Document
import io
from datetime import datetime

ANIO_ACTUAL = datetime.now().year
ANIO_INICIO = ANIO_ACTUAL - 5
RANGO = f"{ANIO_INICIO}-{ANIO_ACTUAL}"

st.set_page_config(page_title="Arquitecto de Marco Teorico - Claude", page_icon="📚", layout="wide")

CSS = """
<style>
    html, body, [class*="css"] { font-family: Georgia, serif; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f6f0 0%, #eef2f7 100%);
        border-right: 2px solid #2563eb;
    }
    [data-testid="stSidebar"] * { color: #1e293b !important; }
    [data-testid="stSidebar"] label {
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        color: #2563eb !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        font-weight: 700;
        border-radius: 8px;
        width: 100%;
        padding: 0.75rem;
        border: none;
        letter-spacing: 1px;
        box-shadow: 0 4px 14px rgba(37,99,235,0.35);
    }
    .stButton>button:hover { background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%); }
    .hero-box {
        background: linear-gradient(135deg, #1e3a6e 0%, #2563eb 60%, #3b82f6 100%);
        border-radius: 16px;
        padding: 48px 56px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(37,99,235,0.25);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        color: #bfdbfe;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 3px;
        padding: 4px 14px;
        border-radius: 20px;
        margin-bottom: 16px;
        text-transform: uppercase;
        border: 1px solid rgba(255,255,255,0.25);
    }
    .hero-title { font-size: 2.4rem; font-weight: 900; color: #ffffff; margin: 0 0 10px 0; }
    .hero-sub { color: #bfdbfe; font-size: 0.9rem; letter-spacing: 2px; text-transform: uppercase; }
    .hero-powered {
        margin-top: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255,255,255,0.12);
        padding: 6px 16px;
        border-radius: 20px;
        color: #e0f2fe;
        font-size: 0.78rem;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 22px 16px;
        text-align: center;
        border: 2px solid #e2e8f0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .metric-card:hover { border-color: #2563eb; box-shadow: 0 4px 20px rgba(37,99,235,0.15); }
    .metric-num { font-size: 2rem; font-weight: 900; color: #2563eb; line-height: 1; }
    .metric-label { font-size: 0.62rem; letter-spacing: 2px; color: #64748b; text-transform: uppercase; margin-top: 6px; font-weight: 600; }
    .info-box {
        background: #f0f7ff;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 5px solid #2563eb;
        margin: 20px 0;
        color: #1e3a6e;
    }
    .year-badge {
        background: #fef9ef;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #92400e;
        margin-top: 8px;
        text-align: center;
    }
    .mode-estricto {
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #991b1b;
        margin-top: 8px;
        text-align: center;
        font-weight: 700;
    }
    .mode-borrador {
        background: #fffbeb;
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #92400e;
        margin-top: 8px;
        text-align: center;
        font-weight: 700;
    }
    .ruta-badge {
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        margin-top: 6px;
        text-align: center;
        font-weight: 700;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── SYSTEM PROMPT v4 ARQUITECTO (rutas metodologicas + 13 secciones) ──────────
SYSTEM_PROMPT = """TITULO DEL AGENTE: ARQUITECTO DE MARCO TEORICO BASADO EN RUTAS METODOLOGICAS (APA 7 + Rigor Academico)

Eres un AGENTE ACADEMICO especializado en construir MARCOS TEORICOS para tesis y articulos cientificos en educacion, con nivel de rigor de maestria y doctorado.

Tu funcion no es solo redactar texto: debes pensar y estructurar el marco teorico conforme a los PRINCIPIOS DE LAS RUTAS METODOLOGICAS:
- ruta cuantitativa, ruta cualitativa, ruta mixta.
Ninguna ruta es superior a otra; la eleccion depende del problema, preguntas, proposito y tipo de evidencia necesaria.

I. PRINCIPIOS RECTORES:
1. El marco teorico debe responder a la ruta metodologica elegida.
2. Ruta CUANTITATIVA: variables, definiciones conceptuales y operacionales, dimensiones, indicadores, hipotesis, soporte para medicion.
3. Ruta CUALITATIVA: categorias o ejes analiticos, perspectivas teoricas interpretativas, antecedentes comprensivos, sentidos y significados, categorias emergentes.
4. Ruta MIXTA: variables y categorias, antecedentes cuantitativos y cualitativos, fundamentos de integracion, articulacion entre medicion e interpretacion.
5. Velar por coherencia: problema → objetivos → preguntas → ruta → marco teorico → diseno metodologico.

II. REGLAS ABSOLUTAS DE RIGOR (CERO ALUCINACION):
1. PROHIBIDO inventar: autores, anos, titulos, revistas, editoriales, paginas, DOIs, URLs, hallazgos, muestras, teorias atribuidas.
2. SOLO puedes citar (APA 7) si el usuario proporciona evidencia explicita en FUENTES_PROVISTAS (fragmento textual o ficha completa).
3. Si falta sustento: marca [FUENTE PENDIENTE]. NO lo conviertas en cita.
4. Nunca presentes referencias incompletas como verificadas.
5. Si no hay fuentes suficientes, NO redactes "marco teorico final": entrega diagnostico de insuficiencia + plan de busqueda.
6. Cada parrafo: idea central + soporte verificable o advertencia + implicacion para el estudio.
7. Texto critico, comparativo y metodologicamente coherente. Sin relleno.

III. CONDICION DE ARRANQUE:
Verifica si el usuario proporciono: TITULO, PROBLEMA, OBJETIVO GENERAL, OBJETIVOS ESPECIFICOS, PREGUNTAS, RUTA/ENFOQUE, CONTEXTO, POBLACION/MUESTRA, VARIABLES/CATEGORIAS, FUENTES_PROVISTAS.
Si faltan datos criticos: max 5 preguntas puntuales.
Si faltan fuentes: NO redactes marco final. Entrega: diagnostico + que falta por variable + plan de busqueda + plantilla.

IV. IDENTIFICACION OBLIGATORIA DE LA RUTA:
Antes de escribir el marco, declara:
1. Que ruta metodologica corresponde y por que (segun problema, objetivos, preguntas, unidades de analisis).
2. Que implica esa ruta para la construccion del marco.
3. Si el usuario declara una ruta incoherente con su estudio: advierte la inconsistencia metodologica con lenguaje academico y propone correccion.

V. COBERTURA TOTAL:
- Desarrollar TODAS las variables o categorias. Prohibido detenerse.
- Por cada una (obligatorio): delimitacion conceptual / definiciones con cita verificable / sintesis critica comparativa / definicion integradora propia / implicacion para el estudio / dimensiones-indicadores o subcategorias-evidencias / vacios de sustento.

VI. LOGICA DE REDACCION SEGUN RUTA:
CUANTITATIVA: definicion conceptual + operacional + dimensiones + indicadores + relacion teorica entre variables + hipotesis posible + antecedentes empiricos medibles + tabla de operacionalizacion.
CUALITATIVA: categorias iniciales o sensitivas + enfoques teoricos de comprension + sentidos y significados + antecedentes cualitativos + posibles subcategorias + preguntas guia para profundizacion.
MIXTA: variables y categorias + antecedentes cuantitativos y cualitativos + racionalidad de integracion + articulacion entre medicion e interpretacion.

VII. ESTRUCTURA OBLIGATORIA DE SALIDA (13 secciones):
0. Ficha del estudio
1. Identificacion y justificacion de la ruta metodologica
2. Verificacion inicial de fuentes (2.1 Inventario / 2.2 Suficiencia por variable)
3. Indice del marco teorico
4. Desarrollo del marco teorico por variables o categorias (4.1, 4.2, 4.3...)
5. Fundamento teorico general del estudio
6. Antecedentes empiricos (6.1 Matriz comparativa / 6.2 Sintesis integradora)
7. Articulacion metodologica del marco con la ruta elegida
8. Operacionalizacion o categorizacion (tabla segun ruta)
9. Vacios de investigacion
10. Riesgos de validez y limitaciones del marco teorico
11. Cobertura final (variables solicitadas / desarrolladas / pendientes)
12. Referencias verificadas APA 7
13. Fuentes faltantes para completar el rigor academico

VIII. FORMATO POR VARIABLE/CATEGORIA:
[NOMBRE]
1. Delimitacion conceptual
2. Definiciones academicas con citas verificadas
3. Sintesis critica comparativa
4. Definicion integradora propia
5. Implicacion para el estudio
6. Dimensiones e indicadores / subcategorias y evidencias
7. Vacios de sustento detectados

IX. ANTECEDENTES EMPIRICOS:
Si hay estudios: matriz (Autor/ano | pais | objetivo | metodo | muestra | hallazgos | limitaciones | aporte) + sintesis integradora.
Si no hay: [EVIDENCIA EMPIRICA INSUFICIENTE] + plan de busqueda por ruta.

X. APA 7: Citas narrativas o parenteticas. No inventes paginas. Solo normaliza lo suficientemente identificado. Incompletas → "Fuentes pendientes de normalizacion APA".

XI. CONTROL DE LONGITUD: divide en PARTE 1/N, 2/N... Escribe "CONTINUAR CON: [pendientes]" al final de cada parte. No cierres referencias hasta la ultima.

XII. CONTROL FINAL DE CALIDAD (verifica antes de responder):
- Ruta identificada y justificada
- Marco responde a esa ruta
- Todas las variables/categorias desarrolladas
- Cada una con sustento verificable
- Coherencia problema-objetivos-preguntas-ruta-marco
- Operacionalizacion/categorizacion correcta al enfoque
- Referencias en APA 7 real
- Informe completo

XIII. REGLA FINAL: Nunca entregues "marco teorico final" si no puedes sostenerlo documentalmente y si no respetaste la logica de la ruta metodologica. Prioridad: rigor academico, no apariencia de completitud."""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Arquitecto de Marco Teórico")
    st.caption("Powered by Claude · Anthropic · v4")
    st.markdown(f'<div class="year-badge">📅 Antecedentes: <strong>{RANGO}</strong> (últimos 5 años)<br>Teorías clásicas: sin restricción de año</div>', unsafe_allow_html=True)
    st.markdown("---")

    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.caption("Obtener key en console.anthropic.com")
    st.markdown("---")

    modo = st.radio(
        "MODO DE TRABAJO",
        ["ESTRICTO (solo fuentes provistas)", "BORRADOR (sugiere bibliografía)"],
        index=0,
        help="ESTRICTO: no inventa citas, marca [FUENTE PENDIENTE]. BORRADOR: genera texto y marca [SUGERENCIA]."
    )
    modo_tag = "ESTRICTO" if "ESTRICTO" in modo else "BORRADOR"
    if modo_tag == "ESTRICTO":
        st.markdown('<div class="mode-estricto">🔒 MODO ESTRICTO — cero alucinación</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-borrador">✏️ MODO BORRADOR — sugiere fuentes</div>', unsafe_allow_html=True)

    st.markdown("---")
    tema = st.text_area("TÍTULO / TEMA", placeholder="Ej: Impacto del uso de TIC en el aprendizaje matemático en secundaria", height=70)
    problema = st.text_area("PROBLEMA (1 párrafo)", placeholder="Describe el problema de investigación...", height=80)
    objetivo = st.text_input("OBJETIVO GENERAL", placeholder="Ej: Determinar la relación entre uso de TIC y aprendizaje...")
    obj_esp = st.text_area("OBJETIVOS ESPECÍFICOS", placeholder="1. Identificar... / 2. Analizar... / 3. Establecer...", height=70)
    preguntas = st.text_area("PREGUNTAS DE INVESTIGACIÓN", placeholder="P1: ¿Cuál es el nivel de...? / P2: ¿Qué relación existe entre...?", height=70)
    variables = st.text_area("VARIABLES / CATEGORÍAS", placeholder="V1: uso de TIC | V2: aprendizaje matematico | V3: motivacion", height=70)

    ruta = st.selectbox(
        "RUTA METODOLÓGICA",
        ["Cuantitativa", "Cualitativa", "Mixta"],
        help="El agente verificará la coherencia entre tu ruta y tu problema/objetivos."
    )
    ruta_colors = {"Cuantitativa": "#dbeafe", "Cualitativa": "#dcfce7", "Mixta": "#fef9c3"}
    st.markdown(f'<div class="ruta-badge" style="background:{ruta_colors[ruta]};border:1px solid #94a3b8;">🔬 Ruta: <strong>{ruta}</strong></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        tipo_doc = st.selectbox("DOCUMENTO", ["Tesis", "Artículo Científico", "TFM", "Monografía"])
    with col2:
        norma = st.selectbox("NORMA", ["APA 7a ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])

    area = st.selectbox("ÁREA", ["Educación / Pedagogía", "Psicología", "Administración", "Salud / Medicina", "Ingeniería", "Ciencias Sociales", "Economía", "Derecho", "Comunicación"])
    col3, col4 = st.columns(2)
    with col3:
        pais = st.text_input("PAÍS / CONTEXTO", value="Perú")
    with col4:
        poblacion = st.text_input("POBLACIÓN / MUESTRA", placeholder="Ej: 120 estudiantes")

    fuentes = st.text_area(
        "FUENTES PROVISTAS",
        placeholder="[FICHA: Autor, Año, Título, Revista/Editorial]\n[EXTRACTO: fragmento textual o resumen fiel]\n\nDejar vacío = diagnóstico de insuficiencia documental",
        height=180,
        help="El agente SOLO cita lo que pongas aquí. Mínimo 1 ficha + extracto por variable para citas reales."
    )

    st.markdown("---")
    generar = st.button("🏛️ GENERAR MARCO TEÓRICO")

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Arquitecto de Marco Teórico · v4 · Rutas Metodológicas · APA 7</div>
    <div class="hero-title">Generador de Marco Teórico</div>
    <div class="hero-sub">Tesis · Artículos Científicos · TFM · Nivel Maestría / Doctorado</div>
    <div class="hero-powered">Powered by Claude Anthropic | Antecedentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
metricas = [("3","Rutas Metodológicas"),("13","Secciones Salida"),("APA 7","Refs Verificadas"),("v4","Anti-Alucinación"),(".docx","Descargable")]
for col, (num, lbl) in zip([m1,m2,m3,m4,m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="info-box">🏛️ Modo <strong>{modo_tag}</strong> · Ruta <strong>{ruta}</strong> · Período antecedentes <strong>{RANGO}</strong>. El agente verifica coherencia metodológica antes de redactar.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### ¿Qué hace este agente?")
st.markdown("*Arquitecto de Marco Teórico con lógica de rutas metodológicas — no solo redacta, estructura según rigor de maestría/doctorado:*")
st.markdown(f"""
**🔬 Identifica y justifica la ruta metodológica** (cuantitativa / cualitativa / mixta) y alerta si hay inconsistencia con tu problema

**🔒 Cero alucinación:** Solo cita lo que tú pegues en Fuentes Provistas — marca [FUENTE PENDIENTE] donde falta evidencia

**📐 13 secciones de salida:**
Ficha del estudio · Ruta metodológica · Verificación de fuentes · Índice · Marco por variable/categoría · Fundamento teórico · Antecedentes (tabla) · Articulación metodológica · Operacionalización · Vacíos · Limitaciones · Cobertura final · Referencias APA 7

**🛡️ Cobertura total:** Desarrolla TODAS las variables — divide en partes si es necesario

**📅 Período antecedentes:** {RANGO} | Teorías clásicas: sin restricción de año
""")
st.markdown("---")

# ── GENERACIÓN ────────────────────────────────────────────────────────────────
if generar:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic.")
    elif not tema:
        st.error("Ingresa el título o tema de investigación.")
    elif not variables:
        st.error("Ingresa al menos una variable o categoría.")
    else:
        num_vars = len([v for v in variables.strip().split("|") if v.strip()])
        modo_compacto = "MODO COMPACTO ACTIVADO (3+ variables): max 2 definiciones por variable, sintesis 5-7 lineas, tablas 2-3 dimensiones. PRIORIDAD ABSOLUTA: completar todas las variables." if num_vars >= 3 else ""

        bloque_fuentes = f"""<<<FUENTES_PROVISTAS>>>
{fuentes.strip() if fuentes.strip() else "[BLOQUE VACIO — no se proveyeron fuentes. NO redactar marco final. Entregar: diagnostico de insuficiencia documental + plan de busqueda por ruta " + ruta + " + plantilla para que el usuario pegue fuentes.]"}
<<<FIN_FUENTES_PROVISTAS>>>"""

        prompt = f"""MODO: {modo_tag}
RUTA METODOLOGICA DECLARADA POR EL USUARIO: {ruta}
{modo_compacto}

FICHA DEL ESTUDIO:
- Titulo: {tema}
- Problema: {problema.strip() if problema.strip() else "[No especificado — crear Supuesto de trabajo]"}
- Objetivo general: {objetivo.strip() if objetivo.strip() else "[No especificado]"}
- Objetivos especificos: {obj_esp.strip() if obj_esp.strip() else "[No especificados]"}
- Preguntas de investigacion: {preguntas.strip() if preguntas.strip() else "[No especificadas]"}
- Variables/Categorias (desarrollar TODAS): {variables.strip()}
- Ruta metodologica: {ruta}
- Tipo de documento: {tipo_doc}
- Area: {area}
- Pais/Contexto: {pais}
- Poblacion/Muestra: {poblacion.strip() if poblacion.strip() else "[No especificada]"}
- Norma de citacion: {norma}
- Periodo de antecedentes: {RANGO} (ultimos 5 anos; teorias clasicas: sin restriccion)

{bloque_fuentes}

INSTRUCCIONES FINALES:
1. Aplica el control final de calidad (XII) antes de responder.
2. Identifica y justifica la ruta metodologica {ruta} ANTES de redactar el marco.
3. Si la ruta declarada es incoherente con problema/objetivos/preguntas: advierte la inconsistencia con lenguaje academico y propone correccion.
4. Si FUENTES_PROVISTAS esta vacio: NO redactes marco teorico final. Entrega diagnostico + plan de busqueda.
5. Desarrolla TODAS las variables/categorias listadas sin excepcion. Divide en PARTE 1/N si es necesario.
6. Usa la estructura obligatoria de 13 secciones (0 a 13).
7. La operacionalizacion/categorizacion debe corresponder exactamente a la ruta {ruta}.
8. Redaccion academica formal en espanol. Nivel maestria/doctorado."""

        with st.spinner(f"🏛️ Arquitecto construyendo marco teórico ({ruta}) en modo {modo_tag}... (3-5 min)"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=8096,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}]
                )
                contenido = response.content[0].text
                st.success(f"✅ Marco teórico generado | Ruta: {ruta} | Modo: {modo_tag}")
                st.markdown("---")
                st.markdown(contenido)

                doc = Document()
                doc.add_heading("MARCO TEÓRICO", 0)
                doc.add_heading(tema, 1)
                doc.add_paragraph(f"Ruta: {ruta} | Modo: {modo_tag} | Norma: {norma} | Período: {RANGO} | País: {pais}")
                doc.add_paragraph("")
                for linea in contenido.split("\n"):
                    linea = linea.strip()
                    if not linea:
                        continue
                    if linea.startswith("### "):
                        doc.add_heading(linea[4:], level=3)
                    elif linea.startswith("## "):
                        doc.add_heading(linea[3:], level=2)
                    elif linea.startswith("# "):
                        doc.add_heading(linea[2:], level=1)
                    else:
                        doc.add_paragraph(linea)
                buf = io.BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.markdown("---")
                st.download_button(
                    label="📥 Descargar Marco Teórico (.docx)",
                    data=buf,
                    file_name=f"marco_teorico_{tema[:40].replace(' ','_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except anthropic.AuthenticationError:
                st.error("API Key inválida. Verifica en console.anthropic.com")
            except anthropic.RateLimitError:
                st.error("Límite de uso alcanzado. Espera unos minutos o recarga créditos.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
