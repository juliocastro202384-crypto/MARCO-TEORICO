import streamlit as st
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
