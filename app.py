import streamlit as st
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
    .hero-title { font-size: 2.6rem; font-weight: 900; color: #ffffff; margin: 0 0 10px 0; }
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
    .metric-num { font-size: 2.2rem; font-weight: 900; color: #2563eb; line-height: 1; }
    .metric-label { font-size: 0.65rem; letter-spacing: 2px; color: #64748b; text-transform: uppercase; margin-top: 6px; font-weight: 600; }
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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📚 Marco Teorico IA")
    st.caption("Powered by Claude · Anthropic")
    st.markdown(f'<div class="year-badge">📅 Fuentes: <strong>{RANGO}</strong> (ultimos 5 anios)<br>Teorias clasicas: sin restriccion de anio</div>', unsafe_allow_html=True)
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
    idioma = st.selectbox("IDIOMA", ["Espanol + Ingles", "Solo Espanol", "Solo Ingles", "Espanol + Ingles + Portugues"])
    st.markdown("---")
    generar = st.button("GENERAR MARCO TEORICO")

st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Generador Academico con IA</div>
    <div class="hero-title">Generador de Marco Teorico</div>
    <div class="hero-sub">Tesis · Articulos Cientificos · TFM · Monografias</div>
    <div class="hero-powered">Powered by Claude Anthropic | Fuentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
metricas = [("5+","Autores por Variable"),("10","Antecedentes Internacionales"),("8","Antecedentes Nacionales"),("12","Terminos en Glosario"),(".docx","Formato Descargable")]
for col, (num, lbl) in zip([m1,m2,m3,m4,m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="info-box">📌 Completa el formulario, ingresa tu API Key de Anthropic y presiona el boton. Fuentes del periodo <strong>{RANGO}</strong> (ultimos 5 anios). Teorias clasicas sin restriccion de anio.</div>', unsafe_allow_html=True)

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
            secciones += f"\n## VARIABLE {i+1}: {var.upper()}\n### 2.{i+1}.1 Definicion conceptual (min 5 autores, {norma}, {RANGO})\n### 2.{i+1}.2 Teorias y modelos (min 3, clasicos y contemporaneos)\n### 2.{i+1}.3 {dim}\n### 2.{i+1}.4 Importancia en {area}\n"
        prompt = f"""Eres un experto academico. Genera un marco teorico completo para:
TEMA: {tema} | VARIABLES: {variables}
ESTUDIO: {tipo_estudio} | DOC: {tipo_doc} | AREA: {area} | PAIS: {pais} | NORMA: {norma}
PERIODO FUENTES: {RANGO} | TEORIAS CLASICAS: sin restriccion de anio
{secciones}
## ANTECEDENTES INTERNACIONALES (10, {RANGO}, formato {norma})
## ANTECEDENTES NACIONALES DE {pais} (8, {RANGO}, mismo formato)
## BASES TEORICAS INTEGRADORAS
## GLOSARIO (12 terminos, {norma})
Redaccion academica formal, minimo 8000 palabras."""
        with st.spinner("Generando marco teorico con Claude... (2-5 minutos)"):
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
                st.error("API Key invalida.")
            except anthropic.RateLimitError:
                st.error("Limite de uso alcanzado.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
