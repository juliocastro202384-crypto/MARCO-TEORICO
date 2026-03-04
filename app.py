import streamlit as st
import anthropic
from docx import Document
import io
from datetime import datetime

# Rango de años dinámico
ANIO_ACTUAL = datetime.now().year
ANIO_INICIO = ANIO_ACTUAL - 5
RANGO = f"{ANIO_INICIO}–{ANIO_ACTUAL}"

st.set_page_config(page_title="Marco Teórico IA · Claude", page_icon="📚", layout="wide")

CSS = """
<style>
    /* ── Fuente general ── */
    html, body, [class*="css"] { font-family: 'Georgia', serif; }

    /* ── Sidebar claro ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f6f0 0%, #eef2f7 100%);
        border-right: 2px solid #2563eb;
    }
    [data-testid="stSidebar"] * { color: #1e293b !important; }
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextArea label {
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        color: #2563eb !important;
    }

    /* ── Botón principal ── */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        font-weight: 700;
        font-size: 0.9rem;
        border-radius: 8px;
        width: 100%;
        padding: 0.75rem;
        border: none;
        letter-spacing: 1px;
        box-shadow: 0 4px 14px rgba(37,99,235,0.35);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 20px rgba(37,99,235,0.5);
        transform: translateY(-1px);
    }

    /* ── Fondo principal blanco/crema ── */
    .main .block-container { background: #ffffff; padding-top: 1.5rem; }

    /* ── Hero banner ── */
    .hero-box {
        background: linear-gradient(135deg, #1e3a6e 0%, #2563eb 60%, #3b82f6 100%);
        border-radius: 16px;
        padding: 48px 56px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(37,99,235,0.25);
        position: relative;
        overflow: hidden;
    }
    .hero-box::before {
        content: "";
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
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
    .hero-title {
        font-size: 2.6rem;
        font-weight: 900;
        color: #ffffff;
        margin: 0 0 10px 0;
        line-height: 1.2;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        color: #bfdbfe;
        font-size: 0.9rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-family: 'Arial', sans-serif;
    }
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
        font-family: 'Arial', sans-serif;
        border: 1px solid rgba(255,255,255,0.2);
    }

    /* ── Tarjetas de métricas ── */
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 22px 16px;
        text-align: center;
        border: 2px solid #e2e8f0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        border-color: #2563eb;
        box-shadow: 0 4px 20px rgba(37,99,235,0.15);
        transform: translateY(-2px);
    }
    .metric-num {
        font-size: 2.2rem;
        font-weight: 900;
        color: #2563eb;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.65rem;
        letter-spacing: 2px;
        color: #64748b;
        text-transform: uppercase;
        margin-top: 6px;
        font-family: 'Arial', sans-serif;
        font-weight: 600;
    }

    /* ── Caja de instrucciones ── */
    .info-box {
        background: #f0f7ff;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 5px solid #2563eb;
        margin: 20px 0;
        color: #1e3a6e;
        font-size: 0.95rem;
    }

    /* ── Caja de rango de años ── */
    .year-badge {
        background: #fef9ef;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #92400e;
        font-family: 'Arial', sans-serif;
        margin-top: 8px;
        text-align: center;
    }

    /* ── Divisor estilo académico ── */
    .academic-divider {
        border: none;
        border-top: 2px solid #e2e8f0;
        margin: 24px 0;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Marco Teórico IA")
    st.caption("Powered by Claude · Anthropic")
    st.markdown('<div class="year-badge">📅 Fuentes: <strong>' + RANGO + '</strong> (últimos 5 años)<br>⚡ Teorías clásicas: sin restricción de año</div>', unsafe_allow_html=True)
    st.markdown("---")

    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.caption("→ Obtener key gratuita en [console.anthropic.com](https://console.anthropic.com)")
    st.markdown("---")

    tema = st.text_area("TEMA DE INVESTIGACIÓN", placeholder="Ej: Impacto del uso de redes sociales en el rendimiento académico de estudiantes universitarios", height=110)
    variables = st.text_area("VARIABLES / CATEGORÍAS", placeholder="Ej: redes sociales, rendimiento académico, motivación", height=75)

    col1, col2 = st.columns(2)
    with col1:
        tipo_estudio = st.selectbox("ENFOQUE", ["Cuantitativo", "Cualitativo", "Mixto"])
    with col2:
        tipo_doc = st.selectbox("DOCUMENTO", ["Tesis", "Artículo Científico", "TFM", "Monografía"])

    area = st.selectbox("ÁREA DE CONOCIMIENTO", [
        "Educación / Pedagogía", "Psicología", "Administración",
        "Salud / Medicina", "Ingeniería", "Ciencias Sociales",
        "Economía", "Derecho", "Comunicación"
    ])

    col3, col4 = st.columns(2)
    with col3:
        pais = st.text_input("PAÍS", value="Perú")
    with col4:
        norma = st.selectbox("NORMA", ["APA 7ª ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])

    idioma = st.selectbox("IDIOMA DE AUTORES", [
        "Español + Inglés", "Solo Español", "Solo Inglés", "Español + Inglés + Portugués"
    ])
    st.markdown("---")
    generar = st.button("⚡ GENERAR MARCO TEÓRICO")

# ─── HERO BANNER ───────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Generador Académico con IA</div>
    <div class="hero-title">Generador de Marco Teórico</div>
    <div class="hero-sub">Tesis &nbsp;·&nbsp; Artículos Científicos &nbsp;·&nbsp; TFM &nbsp;·&nbsp; Monografías</div>
    <div class="hero-powered">🤖 Powered by Claude · Anthropic &nbsp;|&nbsp; 📅 Fuentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

# ─── MÉTRICAS ──────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
metricas = [
    ("5+", "Autores por Variable"),
    ("10", "Antecedentes Internacionales"),
    ("8", "Antecedentes Nacionales"),
    ("12", "Términos en Glosario"),
    (".docx", "Formato Descargable"),
]
for col, (num, lbl) in zip([m1, m2, m3, m4, m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

# ─── INSTRUCCIONES ─────────────────────────────────────────────────
st.markdown(f"""
<div class="info-box">
    📌 <strong>¿Cómo usar?</strong> Completa el formulario en el panel izquierdo, ingresa tu 
    <strong>API Key de Anthropic</strong> y presiona <em>Generar Marco Teórico</em>. 
    El proceso tarda entre <strong>2 y 5 minutos</strong>. 
    Se incluirán fuentes del período <strong>{RANGO}</strong> (últimos 5 años) 
    y teorías clásicas sin restricción de año.
</div>
""", unsafe_allow_html=True)

# ─── GENERACIÓN ────────────────────────────────────────────────────
if generar:
    if not api_key:
        st.error("⚠️ Ingresa tu API Key de Anthropic.")
    elif not tema:
        st.error("⚠️ Ingresa el tema de investigación.")
    elif not variables:
        st.error("⚠️ Ingresa al menos una variable o categoría.")
    else:
        lista_vars = [v.strip() for v in variables.split(",")]
        secciones = ""
        for i, var in enumerate(lista_vars):
            dim = "Dimensiones e indicadores" if tipo_estudio == "Cuantitativo" else "Categorías y subcategorías"
            secciones += f"\n## VARIABLE {i+1}: {var.upper()}\n### 2.{i+1}.1 Definición conceptual (mínimo 5 autores, {norma}, período {RANGO})\n### 2.{i+1}.2 Teorías y modelos teóricos (mínimo 3, con autores clásicos y contemporáneos)\n### 2.{i+1}.3 {dim}\n### 2.{i+1}.4 Importancia en el contexto de {area}\n"

        prompt = f"""Eres un experto académico en metodología de la investigación científica.
Genera un marco teórico completo, riguroso y extenso para la siguiente investigación:

TEMA: {tema}
VARIABLES: {variables}
TIPO DE ESTUDIO: {tipo_estudio}
TIPO DE DOCUMENTO: {tipo_doc}
ÁREA: {area}
PAÍS DE REFERENCIA: {pais}
NORMA DE CITACIÓN: {norma}
IDIOMA DE AUTORES: {idioma}
PERÍODO DE FUENTES RECIENTES: {RANGO} (últimos 5 años)
NOTA: Las teorías y autores clásicos NO tienen restricción de año.

ESTRUCTURA REQUERIDA:

## INTRODUCCIÓN AL MARCO TEÓRICO
(Párrafo introductorio académico que contextualice el marco)
{secciones}
## ANTECEDENTES DE LA INVESTIGACIÓN

### Antecedentes Internacionales
(10 antecedentes internacionales del período {RANGO}, cada uno con: autor(es), año, título, país, objetivo, metodología, resultados principales, conclusiones y relación con el presente estudio. Formato {norma})

### Antecedentes Nacionales de {pais}
(8 antecedentes nacionales de {pais} del período {RANGO}, mismo formato)

## BASES TEÓRICAS INTEGRADORAS
(Síntesis que integre todas las variables y explique su relación teórica)

## DEFINICIÓN DE TÉRMINOS BÁSICOS (GLOSARIO)
(Mínimo 12 términos con definición académica y cita en {norma})

REQUISITOS:
- Redacción académica formal y rigurosa, sin bullet points en definiciones
- Citas estrictamente en {norma}
- Fuentes recientes: período {RANGO}; teorías clásicas: sin restricción de año
- Variedad de autores: latinoamericanos, europeos, norteamericanos
- Extensión mínima: 8,000 palabras"""

        with st.spinner("📚 Claude generando tu marco teórico... (2–5 minutos)"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=8096,
                    messages=[{"role": "user", "content": prompt}]
                )
                contenido = response.content[0].text
                st.success("✅ ¡Marco teórico generado exitosamente!")
                st.markdown("---")
                st.markdown(contenido)

                doc = Document()
                doc.add_heading("MARCO TEÓRICO", 0)
                doc.add_heading(tema, 1)
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
                    label="📄 Descargar Marco Teórico (.docx)",
                    data=buf,
                    file_name=f"marco_teorico_{tema[:40].replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except anthropic.AuthenticationError:
                st.error("❌ API Key inválida. Verifica en console.anthropic.com")
            except anthropic.RateLimitError:
                st.error("❌ Límite de uso alcanzado. Intenta en unos minutos.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")import streamlit as stimport streamlit as st
import anthropic
from docx import Document
import io
from datetime import datetime

ANIO_ACTUAL = datetime.now().year
ANIO_INICIO = ANIO_ACTUAL - 5
RANGO = f"{ANIO_INICIO}-{ANIO_ACTUAL}"

st.set_page_config(page_title="Marco Teorico IA - Claude", page_icon="📚", layout="wide")

CSS = """
<style>
    html, body, [class*="css"] { font-family: 'Georgia', serif; }
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
        font-size: 0.9rem;
        border-radius: 8px;
        width: 100%;
        padding: 0.75rem;
        border: none;
        letter-spacing: 1px;
        box-shadow: 0 4px 14px rgba(37,99,235,0.35);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-1px);
    }
    .main .block-container { background: #ffffff; padding-top: 1.5rem; }
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
    .hero-title {
        font-size: 2.6rem;
        font-weight: 900;
        color: #ffffff;
        margin: 0 0 10px 0;
        line-height: 1.2;
    }
    .hero-sub {
        color: #bfdbfe;
        font-size: 0.9rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-family: Arial, sans-serif;
    }
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
        font-family: Arial, sans-serif;
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
    .metric-card:hover {
        border-color: #2563eb;
        box-shadow: 0 4px 20px rgba(37,99,235,0.15);
        transform: translateY(-2px);
    }
    .metric-num {
        font-size: 2.2rem;
        font-weight: 900;
        color: #2563eb;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.65rem;
        letter-spacing: 2px;
        color: #64748b;
        text-transform: uppercase;
        margin-top: 6px;
        font-family: Arial, sans-serif;
        font-weight: 600;
    }
    .info-box {
        background: #f0f7ff;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 5px solid #2563eb;
        margin: 20px 0;
        color: #1e3a6e;
        font-size: 0.95rem;
    }
    .year-badge {
        background: #fef9ef;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #92400e;
        font-family: Arial, sans-serif;
        margin-top: 8px;
        text-align: center;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📚 Marco Teorico IA")
    st.caption("Powered by Claude · Anthropic")
    st.markdown(f'<div class="year-badge">📅 Fuentes: <strong>{RANGO}</strong> (ultimos 5 anios)<br>⚡ Teorias clasicas: sin restriccion de anio</div>', unsafe_allow_html=True)
    st.markdown("---")
    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.caption("Obtener key en console.anthropic.com")
    st.markdown("---")
    tema = st.text_area("TEMA DE INVESTIGACION", placeholder="Ej: Impacto del uso de redes sociales en el rendimiento academico", height=110)
    variables = st.text_area("VARIABLES / CATEGORIAS", placeholder="Ej: redes sociales, rendimiento academico", height=75)
    col1, col2 = st.columns(2)
    with col1:
        tipo_estudio = st.selectbox("ENFOQUE", ["Cuantitativo", "Cualitativo", "Mixto"])
    with col2:
        tipo_doc = st.selectbox("DOCUMENTO", ["Tesis", "Articulo Cientifico", "TFM", "Monografia"])
    area = st.selectbox("AREA", ["Educacion / Pedagogia", "Psicologia", "Administracion", "Salud / Medicina", "Ingenieria", "Ciencias Sociales", "Economia", "Derecho", "Comunicacion"])
    col3, col4 = st.columns(2)
    with col3:
        pais = st.text_input("PAIS", value="Peru")
    with col4:
        norma = st.selectbox("NORMA", ["APA 7a ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])
    idioma = st.selectbox("IDIOMA DE AUTORES", ["Espanol + Ingles", "Solo Espanol", "Solo Ingles", "Espanol + Ingles + Portugues"])
    st.markdown("---")
    generar = st.button("GENERAR MARCO TEORICO")

st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Generador Academico con IA</div>
    <div class="hero-title">Generador de Marco Teorico</div>
    <div class="hero-sub">Tesis &nbsp;·&nbsp; Articulos Cientificos &nbsp;·&nbsp; TFM &nbsp;·&nbsp; Monografias</div>
    <div class="hero-powered">🤖 Powered by Claude Anthropic &nbsp;|&nbsp; 📅 Fuentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
metricas = [("5+","Autores por Variable"),("10","Antecedentes Internacionales"),("8","Antecedentes Nacionales"),("12","Terminos en Glosario"),(".docx","Formato Descargable")]
for col, (num, lbl) in zip([m1,m2,m3,m4,m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="info-box">
    📌 <strong>Como usar?</strong> Completa el formulario, ingresa tu API Key de Anthropic y presiona
    <em>Generar Marco Teorico</em>. Tarda entre <strong>2 y 5 minutos</strong>.
    Fuentes del periodo <strong>{RANGO}</strong> (ultimos 5 anios). Teorias clasicas sin restriccion de anio.
</div>
""", unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic.")
    elif not tema:
        st.error("Ingresa el tema de investigacion.")
    elif not variables:
        st.error("Ingresa al menos una variable.")
    else:
        lista_vars = [v.strip() for v in variables.split(",")]
        secciones = ""
        for i, var in enumerate(lista_vars):
            dim = "Dimensiones e indicadores" if tipo_estudio == "Cuantitativo" else "Categorias y subcategorias"
            secciones += f"\n## VARIABLE {i+1}: {var.upper()}\n### 2.{i+1}.1 Definicion conceptual (minimo 5 autores, {norma}, periodo {RANGO})\n### 2.{i+1}.2 Teorias y modelos teoricos (minimo 3, autores clasicos y contemporaneos)\n### 2.{i+1}.3 {dim}\n### 2.{i+1}.4 Importancia en {area}\n"
        prompt = f"""Eres un experto academico en metodologia de la investigacion cientifica.
Genera un marco teorico completo y riguroso para:
TEMA: {tema}
VARIABLES: {variables}
TIPO DE ESTUDIO: {tipo_estudio} | DOCUMENTO: {tipo_doc} | AREA: {area} | PAIS: {pais} | NORMA: {norma} | IDIOMA: {idioma}
PERIODO DE FUENTES RECIENTES: {RANGO} (ultimos 5 anios)
NOTA: Teorias y autores clasicos NO tienen restriccion de anio.

ESTRUCTURA:
## INTRODUCCION AL MARCO TEORICO
{secciones}
## ANTECEDENTES INTERNACIONALES
(10 antecedentes del periodo {RANGO}: autor, anio, titulo, pais, objetivo, metodologia, resultados, conclusiones, relacion con el estudio. Formato {norma})
## ANTECEDENTES NACIONALES DE {pais}
(8 antecedentes del periodo {RANGO}, mismo formato)
## BASES TEORICAS INTEGRADORAS
## GLOSARIO DE TERMINOS BASICOS
(12 terminos con definicion academica en {norma})

Redaccion academica formal, sin bullet points en definiciones, minimo 8000 palabras."""
        with st.spinner("📚 Claude generando tu marco teorico... (2-5 minutos)"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=8096,
                    messages=[{"role": "user", "content": prompt}]
                )
                contenido = response.content[0].text
                st.success("Marco teorico generado exitosamente!")
                st.markdown("---")
                st.markdown(contenido)
                doc = Document()
                doc.add_heading("MARCO TEORICO", 0)
                doc.add_heading(tema, 1)
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
                    label="Descargar Marco Teorico (.docx)",
                    data=buf,
                    file_name=f"marco_teorico_{tema[:40].replace(' ','_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except anthropic.AuthenticationError:
                st.error("API Key invalida. Verifica en console.anthropic.com")
            except anthropic.RateLimitError:
                st.error("Limite de uso alcanzado. Intenta en unos minutos.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
import anthropic
from docx import Document
import io

st.set_page_config(page_title="Marco Teorico IA - Claude", layout="wide")

CSS = """
<style>
[data-testid="stSidebar"] { background-color: #1a1a2e; }
.stButton>button { background-color: #c9a84c; color: #1a1a2e; font-weight: bold; border-radius: 8px; width: 100%; }
.metric-card { background: #0f3460; border-radius: 12px; padding: 20px; text-align: center; color: white; }
.metric-num { font-size: 2rem; font-weight: bold; color: #c9a84c; }
.metric-label { font-size: 0.75rem; letter-spacing: 2px; color: #aaa; }
.hero-box { background: linear-gradient(135deg, #0f3460, #16213e); border-radius: 16px; padding: 40px; margin-bottom: 20px; }
.hero-title { font-size: 2.5rem; font-weight: bold; color: #c9a84c; }
.hero-sub { color: #888; font-size: 0.85rem; letter-spacing: 3px; }
.info-box { background: #0f3460; border-radius: 12px; padding: 20px; border-left: 4px solid #c9a84c; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Marco Teorico IA - Claude")
    st.caption("claude-opus-4-5 - Anthropic")
    st.markdown("---")
    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.markdown("Obtener key en console.anthropic.com")
    st.markdown("---")
    tema = st.text_area("TEMA", placeholder="Ej: Impacto redes sociales en rendimiento academico", height=100)
    variables = st.text_area("VARIABLES", placeholder="Ej: redes sociales, rendimiento academico", height=70)
    tipo_estudio = st.selectbox("TIPO DE ESTUDIO", ["Cuantitativo", "Cualitativo", "Mixto"])
    tipo_doc = st.selectbox("TIPO DE DOCUMENTO", ["Articulo Cientifico", "Tesis", "TFM", "Monografia"])
    area = st.selectbox("AREA", ["Educacion / Pedagogia", "Psicologia", "Administracion", "Salud / Medicina", "Ingenieria", "Economia", "Derecho"])
    pais = st.text_input("PAIS", value="Peru")
    norma = st.selectbox("NORMA", ["APA 7a ed.", "Vancouver", "Chicago", "MLA"])
    idioma = st.selectbox("IDIOMA", ["Espanol + Ingles", "Solo Espanol", "Solo Ingles"])
    st.markdown("---")
    generar = st.button("GENERAR MARCO TEORICO")

st.markdown('<div class="hero-box"><div class="hero-title">Generador de Marco Teorico</div><div class="hero-sub">TESIS - ARTICULOS - TFM | Claude Anthropic | 2024-2026</div></div>', unsafe_allow_html=True)

cols = st.columns(5)
labels = [("5+", "AUTORES/VAR"), ("10", "ANT. INTER."), ("8", "ANT. NAC."), ("12", "GLOSARIO"), (".docx", "DESCARGA")]
for col, (num, lbl) in zip(cols, labels):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="info-box">Como usar: Completa el formulario, ingresa tu API Key de Anthropic y presiona el boton. Tarda 2-5 minutos.</div>', unsafe_allow_html=True)

if generar:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic.")
    elif not tema:
        st.error("Ingresa el tema de investigacion.")
    elif not variables:
        st.error("Ingresa al menos una variable.")
    else:
        lista_vars = [v.strip() for v in variables.split(",")]
        secciones = ""
        for i, var in enumerate(lista_vars):
            dim = "Dimensiones e indicadores" if tipo_estudio == "Cuantitativo" else "Categorias y subcategorias"
            secciones += f"\n## VARIABLE {i+1}: {var.upper()}\n### Definicion conceptual\n### Teorias y modelos\n### {dim}\n### Importancia en {area}\n"
        prompt = f"""Eres un experto academico. Genera un marco teorico completo y riguroso para:
TEMA: {tema}
VARIABLES: {variables}
ESTUDIO: {tipo_estudio} | DOC: {tipo_doc} | AREA: {area} | PAIS: {pais} | NORMA: {norma}
{secciones}
## ANTECEDENTES INTERNACIONALES (10, 2021-2026, formato {norma})
## ANTECEDENTES NACIONALES DE {pais} (8, mismo formato)
## BASES TEORICAS INTEGRADORAS
## GLOSARIO (12 terminos en {norma})
Redaccion academica formal, minimo 8000 palabras, citas en {norma}."""
        with st.spinner("Claude generando marco teorico... (2-5 minutos)"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=8096,
                    messages=[{"role": "user", "content": prompt}]
                )
                contenido = response.content[0].text
                st.success("Marco teorico generado exitosamente!")
                st.markdown("---")
                st.markdown(contenido)
                doc = Document()
                doc.add_heading("MARCO TEORICO", 0)
                doc.add_heading(tema, 1)
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
                st.download_button("Descargar Marco Teorico (.docx)", data=buf, file_name="marco_teorico.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            except anthropic.AuthenticationError:
                st.error("API Key invalida. Verifica en console.anthropic.com")
            except anthropic.RateLimitError:
                st.error("Limite de uso alcanzado. Intenta en unos minutos.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
