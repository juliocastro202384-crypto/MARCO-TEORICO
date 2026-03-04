import streamlit as st
import anthropic
from docx import Document
import io

st.set_page_config(page_title="Marco Teorico IA - Claude", page_icon="🟣", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1a2e; }
        .stButton>button { background-color: #c9a84c; color: #1a1a2e; font-weight: bold; border-radius: 8px; width: 100%; padding: 0.6rem; font-size: 1rem; }
            .metric-card { background: #0f3460; border-radius: 12px; padding: 20px; text-align: center; color: white; }
                .metric-num { font-size: 2rem; font-weight: bold; color: #c9a84c; }
                    .metric-label { font-size: 0.75rem; letter-spacing: 2px; color: #aaa; }
                        .hero-box { background: linear-gradient(135deg, #0f3460, #16213e); border-radius: 16px; padding: 40px; margin-bottom: 20px; border: 1px solid #c9a84c44; }
                            .hero-title { font-size: 2.5rem; font-weight: bold; color: #c9a84c; }
                                .hero-sub { color: #888; font-size: 0.85rem; letter-spacing: 3px; }
                                    .info-box { background: #0f3460; border-radius: 12px; padding: 20px; border-left: 4px solid #c9a84c; margin: 10px 0; }
                                    </style>
                                    """, unsafe_allow_html=True)

with st.sidebar:
      st.markdown("### Marco Teorico IA - Claude")
      st.caption("claude-opus-4-5 - Anthropic")
      st.markdown("---")
      api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
      st.markdown("Obtener key en console.anthropic.com")
      st.markdown("---")
      tema = st.text_area("TEMA DE INVESTIGACION", placeholder="Ej: Impacto del uso de redes sociales en el rendimiento academico", height=120)
      variables = st.text_area("VARIABLES / CATEGORIAS", placeholder="Ej: redes sociales, rendimiento academico", height=80)
      col1, col2 = st.columns(2)
      with col1:
                tipo_estudio = st.selectbox("TIPO DE ESTUDIO", ["Cuantitativo", "Cualitativo", "Mixto"])
            with col2:
          tipo_doc = st.selectbox("TIPO DE DOCUMENTO", ["Articulo Cientifico", "Tesis", "TFM", "Monografia"])
                  area = st.selectbox("AREA DE CONOCIMIENTO", ["Educacion / Pedagogia", "Psicologia", "Administracion", "Salud / Medicina", "Ingenieria", "Ciencias Sociales", "Economia", "Derecho", "Comunicacion"])
    col3, col4 = st.columns(2)
    with col3:
              pais = st.text_input("PAIS", value="Peru")
          with col4:
                    norma = st.selectbox("NORMA DE CITA", ["APA 7a ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])
                idioma = st.selectbox("IDIOMA DE AUTORES", ["Espanol + Ingles", "Solo Espanol", "Solo Ingles"])
    st.markdown("---")
    generar = st.button("GENERAR MARCO TEORICO")

st.markdown("""<div class="hero-box"><div class="hero-title">Generador de Marco Teorico</div><div class="hero-sub">TESIS - ARTICULOS - TFM | Powered by Claude Anthropic | 2024-2026</div></div>""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
      st.markdown('<div class="metric-card"><div class="metric-num">5+</div><div class="metric-label">AUTORES POR VARIABLE</div></div>', unsafe_allow_html=True)
with m2:
      st.markdown('<div class="metric-card"><div class="metric-num">10</div><div class="metric-label">ANTECEDENTES INTERNACIONALES</div></div>', unsafe_allow_html=True)
with m3:
      st.markdown('<div class="metric-card"><div class="metric-num">8</div><div class="metric-label">ANTECEDENTES NACIONALES</div></div>', unsafe_allow_html=True)
with m4:
      st.markdown('<div class="metric-card"><div class="metric-num">12</div><div class="metric-label">TERMINOS EN GLOSARIO</div></div>', unsafe_allow_html=True)
with m5:
      st.markdown('<div class="metric-card"><div class="metric-num">.docx</div><div class="metric-label">FORMATO DESCARGABLE</div></div>', unsafe_allow_html=True)

st.markdown("")
st.markdown('<div class="info-box">Como usar: Completa el formulario, ingresa tu API Key de Anthropic y presiona Generar Marco Teorico. El proceso tarda entre 2 y 5 minutos.</div>', unsafe_allow_html=True)

if generar:
      if not api_key:
                st.error("Ingresa tu API Key de Anthropic.")
elif not tema:
        st.error("Ingresa el tema de investigacion.")
elif not variables:
        st.error("Ingresa al menos una variable.")
else:
        lista_vars = [v.strip() for v in variables.split(",")]
        secciones_vars = ""
        for i, var in enumerate(lista_vars):
                      dim_label = "Dimensiones e indicadores" if tipo_estudio == "Cuantitativo" else "Categorias y subcategorias"
                      secciones_vars += f"\n## VARIABLE {i+1}: {var.upper()}\n### 2.{i+1}.1 Definicion conceptual\n(Minimo 5 autores de {idioma}, citas en {norma}, periodo 2021-2026)\n### 2.{i+1}.2 Teorias y modelos\n(Minimo 3 teorias)\n### 2.{i+1}.3 {dim_label}\n### 2.{i+1}.4 Importancia en {area}\n"

        prompt = f"""Eres un experto academico. Genera un marco teorico completo para:
        TEMA: {tema}
        VARIABLES: {variables}
        ESTUDIO: {tipo_estudio} | DOCUMENTO: {tipo_doc} | AREA: {area} | PAIS: {pais} | NORMA: {norma}

        ESTRUCTURA:
        ## INTRODUCCION AL MARCO TEORICO
        {secciones_vars}
        ## ANTECEDENTES INTERNACIONALES
        (10 antecedentes 2021-2026 con autor, anio, titulo, pais, objetivo, metodologia, resultados, conclusiones en {norma})
        ## ANTECEDENTES NACIONALES DE {pais}
        (8 antecedentes 2021-2026, mismo formato)
        ## BASES TEORICAS INTEGRADORAS
        ## GLOSARIO (12 terminos con definicion en {norma})
        Requisitos: redaccion academica formal, citas en {norma}, minimo 8000 palabras."""

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
                  buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.markdown("---")
                st.download_button(label="Descargar Marco Teorico (.docx)", data=buffer, file_name=f"marco_teorico_{tema[:40].replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
except anthropic.AuthenticationError:
                st.error("API Key invalida. Verifica en console.anthropic.com")
except anthropic.RateLimitError:
                st.error("Limite de uso alcanzado. Intenta en unos minutos.")
except Exception as e:
                st.error(f"Error: {str(e)}")
