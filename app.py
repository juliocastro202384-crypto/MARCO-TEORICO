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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── SYSTEM PROMPT BASE (anti-alucinacion + RAG) ──────────────────────────────
SYSTEM_PROMPT = """Eres un AGENTE ACADÉMICO especializado en construir MARCO TEÓRICO para investigacion educativa (tesis, TFM, articulos). Tu prioridad es el rigor, la coherencia y la etica academica.

REGLAS CRITICAS (OBLIGATORIAS):
1. PROHIBIDO inventar: autores, años, titulos, editoriales, revistas, paginas, DOIs o URLs.
2. SOLO puedes citar (APA 7) si el usuario te proporciono: (a) el texto exacto del fragmento, o (b) una ficha bibliografica completa + idea claramente atribuible.
3. Si falta evidencia para una afirmacion clave, escribe [FUENTE PENDIENTE] y NO lo conviertas en cita.
4. Cada parrafo debe tener: Idea central + sustento (fuente o razonamiento limitado) + implicacion para el estudio.
5. Al final separa: "Referencias (APA 7) verificadas" (solo completas y provistas) y "Referencias sugeridas para buscar" [SUGERENCIA] (sin presentarlas como verificadas).

MODOS DE TRABAJO:
- ESTRICTO (por defecto): si no hay fuentes provistas, entrega estructura + [FUENTE PENDIENTE] + plan de busqueda. No redactas con citas inventadas.
- BORRADOR: redactas texto conceptual sin citas, marcado como "Borrador sin soporte", y propones fuentes a buscar [SUGERENCIA].

FUENTES: Solo usas lo que venga en el bloque <<<FUENTES_PROVISTAS_POR_USUARIO>>>. Si esta vacio o insuficiente, declaralo y propone que recuperar.

ESTRUCTURA DE SALIDA OBLIGATORIA:
1. Indice propuesto del marco teorico
2. Marco conceptual y definiciones
   2.1 Constructo 1: a) Definiciones (con citas SOLO si hay fuente) b) Sintesis critica c) Definicion integradora propia d) Implicacion para el estudio
   2.2 Constructo 2 ...
3. Teorias/modelos que sustentan el estudio (solo si hay soporte; si no, [FUENTE PENDIENTE])
4. Antecedentes empiricos: tabla (Autor/año | contexto | metodo | muestra | hallazgos | limitaciones | aporte) + sintesis integradora. Si faltan: [NO HAY EVIDENCIA EN FUENTES_PROVISTAS] + terminos de busqueda sugeridos.
5. Operacionalizacion segun enfoque:
   - Cuantitativo: Variable → Dimension → Indicador → Ejemplo item → Escala sugerida
   - Cualitativo: Categoria → Subcategoria → Evidencias → Preguntas guia
   - Mixto: ambas + integracion
6. Vacios de investigacion que el estudio atiende (2-5 puntos)
7. Riesgos de validez / limitaciones del marco teorico (2-5 puntos)
8. Referencias (APA 7) verificadas
9. Referencias sugeridas para buscar [SUGERENCIA]

CHECKLIST ANTI-ALUCINACION (aplica antes de responder):
- ¿Mencionne algun autor/año que NO este en FUENTES_PROVISTAS? Si si, moverlo a [SUGERENCIA] o eliminar.
- ¿Puse DOIs/URLs? Solo si el usuario los dio.
- ¿Cada afirmacion fuerte tiene soporte? Si no, marcar [FUENTE PENDIENTE].
- ¿Incluí operacionalizacion/categorias segun enfoque? Si no, agregar."""

with st.sidebar:
    st.markdown("## 📚 Marco Teorico IA")
    st.caption("Powered by Claude · Anthropic")
    st.markdown(f'<div class="year-badge">📅 Fuentes: <strong>{RANGO}</strong> (últimos 5 años)<br>Teorías clásicas: sin restricción de año</div>', unsafe_allow_html=True)
    st.markdown("---")
    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.caption("Obtener key en console.anthropic.com")
    st.markdown("---")

    modo = st.radio(
        "MODO DE TRABAJO",
        ["ESTRICTO (solo fuentes provistas)", "BORRADOR (sugiere bibliografía)"],
        index=0,
        help="ESTRICTO: no inventa citas. BORRADOR: genera texto y sugiere fuentes a buscar."
    )
    modo_tag = "ESTRICTO" if "ESTRICTO" in modo else "BORRADOR"
    if modo_tag == "ESTRICTO":
        st.markdown('<div class="mode-estricto">🔒 MODO ESTRICTO — sin alucinaciones</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-borrador">✏️ MODO BORRADOR — sugiere fuentes</div>', unsafe_allow_html=True)

    st.markdown("---")
    tema = st.text_area("TEMA / TÍTULO DE INVESTIGACIÓN", placeholder="Ej: Impacto del uso de TIC en el aprendizaje matemático en secundaria", height=80)
    problema = st.text_area("PROBLEMA (1 párrafo)", placeholder="Describe brevemente el problema de investigación...", height=80)
    objetivo = st.text_input("OBJETIVO GENERAL", placeholder="Ej: Determinar la relación entre...")
    variables = st.text_area("VARIABLES / CONSTRUCTOS", placeholder="Ej: V1=uso de TIC, V2=aprendizaje matemático", height=60)

    col1, col2 = st.columns(2)
    with col1:
        tipo_estudio = st.selectbox("ENFOQUE", ["Cuantitativo", "Cualitativo", "Mixto"])
    with col2:
        tipo_doc = st.selectbox("DOCUMENTO", ["Tesis", "Artículo Científico", "TFM", "Monografía"])

    area = st.selectbox("ÁREA", ["Educación / Pedagogía", "Psicología", "Administración", "Salud / Medicina", "Ingeniería", "Ciencias Sociales", "Economía", "Derecho", "Comunicación"])
    col3, col4 = st.columns(2)
    with col3:
        pais = st.text_input("PAÍS", value="Perú")
    with col4:
        norma = st.selectbox("NORMA", ["APA 7a ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])

    fuentes = st.text_area(
        "FUENTES PROVISTAS (pega aquí tus fragmentos o fichas)",
        placeholder="[Fuente 1: Autor, Año, Título. Fragmento o idea resumida]\n[Fuente 2: ...]\n(Dejar vacío para modo ESTRICTO sin fuentes)",
        height=150,
        help="Pega fragmentos reales de tus PDFs o fichas bibliográficas completas. El agente SOLO citará lo que pongas aquí."
    )

    st.markdown("---")
    generar = st.button("⚡ GENERAR MARCO TEÓRICO")

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Agente Académico con IA · Rigor Anti-Alucinación</div>
    <div class="hero-title">Generador de Marco Teórico</div>
    <div class="hero-sub">Tesis · Artículos Científicos · TFM · Monografías</div>
    <div class="hero-powered">Powered by Claude Anthropic | Fuentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
metricas = [("RAG","Anti-Alucinación"),("APA 7","Citas Verificadas"),("2 Modos","Estricto/Borrador"),("9","Secciones Salida"),(".docx","Descargable")]
for col, (num, lbl) in zip([m1,m2,m3,m4,m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="info-box">📌 Completa el formulario lateral, pega tus fuentes y presiona el botón. Modo <strong>{modo_tag}</strong> activado — período de búsqueda <strong>{RANGO}</strong>.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### ¿Qué genera esta herramienta?")
st.markdown("*Marco teórico con rigor académico real. El agente no inventa citas — solo usa lo que tú provees como evidencia:*")
st.markdown(f"""
**🔒 Modo ESTRICTO (anti-alucinación):**
- Solo cita autores/textos que tú pegues en "Fuentes Provistas"
- Marca [FUENTE PENDIENTE] cuando no hay evidencia
- Propone términos de búsqueda para lo que falta

**✏️ Modo BORRADOR:**
- Genera texto conceptual completo
- Marca sugerencias como [SUGERENCIA] (no como citas reales)
- Ideal para tener una estructura inicial

**📐 Estructura de salida (9 secciones):**
- Índice · Marco conceptual · Teorías · Antecedentes empíricos (tabla)
- Operacionalización · Vacíos de investigación · Limitaciones
- Referencias verificadas APA 7 · Referencias sugeridas

**📄 Período de antecedentes:** {RANGO} (últimos 5 años) | Teorías clásicas: sin restricción
""")
st.markdown("---")

# ── GENERACIÓN ────────────────────────────────────────────────────────────────
if generar:
    if not api_key:
        st.error("Ingresa tu API Key de Anthropic.")
    elif not tema:
        st.error("Ingresa el tema de investigación.")
    elif not variables:
        st.error("Ingresa al menos una variable o constructo.")
    else:
        bloque_fuentes = f"""<<<FUENTES_PROVISTAS_POR_USUARIO>>>
{fuentes if fuentes.strip() else "[BLOQUE VACÍO — no se proveyeron fuentes. Aplicar modo " + modo_tag + " sin citas reales.]"}
<<<FIN_FUENTES_PROVISTAS_POR_USUARIO>>>"""

        prompt = f"""MODO: {modo_tag}

DATOS DEL ESTUDIO:
- Tema/Título: {tema}
- Problema: {problema if problema.strip() else "[No especificado — usa supuestos de trabajo]"}
- Objetivo general: {objetivo if objetivo.strip() else "[No especificado]"}
- Variables/Constructos: {variables}
- Enfoque: {tipo_estudio}
- Tipo de documento: {tipo_doc}
- Área: {area}
- País/contexto: {pais}
- Norma de citación: {norma}
- Período de antecedentes: {RANGO} (últimos 5 años; teorías clásicas sin restricción)

{bloque_fuentes}

INSTRUCCIÓN:
Genera el marco teórico completo siguiendo EXACTAMENTE la estructura de 9 secciones del sistema.
- Aplica el checklist anti-alucinación antes de responder.
- En modo ESTRICTO: no inventes ninguna cita. Usa [FUENTE PENDIENTE] donde falte evidencia.
- En modo BORRADOR: genera texto completo pero marca [SUGERENCIA] en toda bibliografía no provista.
- La operacionalización debe corresponder al enfoque {tipo_estudio}.
- Mínimo 6,000 palabras en redacción académica formal en español."""

        with st.spinner(f"Generando marco teórico en modo {modo_tag}... (puede tomar 3-5 minutos)"):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=8096,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}]
                )
                contenido = response.content[0].text
                st.success(f"✅ Marco teórico generado en modo {modo_tag}")
                st.markdown("---")
                st.markdown(contenido)

                doc = Document()
                doc.add_heading("MARCO TEÓRICO", 0)
                doc.add_heading(tema, 1)
                doc.add_paragraph(f"Modo: {modo_tag} | Enfoque: {tipo_estudio} | Norma: {norma} | Período: {RANGO}")
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
