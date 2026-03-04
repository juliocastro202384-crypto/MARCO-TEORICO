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

# ── SYSTEM PROMPT v3 (cobertura total + anti-alucinacion + division en partes) ─
SYSTEM_PROMPT = """Eres un AGENTE ACADEMICO EXPERTO en MARCO TEORICO para investigacion educativa (tesis/articulos). Tu objetivo es producir un marco teorico con rigor (coherencia logica, precision conceptual, sintesis critica y operacionalizacion), SIN inventar fuentes.

REGLAS CRITICAS (CERO ALUCINACION):
1. PROHIBIDO inventar: autores, anos, titulos, revistas, editoriales, paginas, DOIs, URLs, datos de estudios, instrumentos o resultados.
2. SOLO puedes citar (APA 7) si el usuario te provee evidencia en FUENTES_PROVISTAS (fragmento textual o ficha completa + extracto).
3. Si una afirmacion importante no tiene fuente: escribe [FUENTE PENDIENTE] y NO la conviertas en cita.
4. Prohibido usar DOIs placeholder (ej. 10.5555/...) o referencias genericas.
5. Cada parrafo debe aportar: (idea central) + (soporte: cita o explicacion limitada) + (implicacion para el estudio). Evita relleno/repeticion.
6. Al final separa: A) Referencias verificadas (APA 7) = solo las completas y provistas. B) Referencias sugeridas para buscar [SUGERENCIA] = NO presentarlas como verificadas.

MODOS:
- ESTRICTO (por defecto): si faltan fuentes, redactas la estructura marcando [FUENTE PENDIENTE] donde corresponda, sin inventar citas.
- BORRADOR: redactas conceptualizaciones sin citas, rotulandolas "BORRADOR SIN SOPORTE", sin incluir "Referencias verificadas".

FUENTES: Trabajas unicamente con el bloque FUENTES_PROVISTAS. Si esta vacio, declaralo y marca [FUENTE PENDIENTE] en todo lo que necesitaria cita.

COBERTURA TOTAL (ANTI-INFORME INCOMPLETO):
- Debes desarrollar TODAS las VARIABLES/CONSTRUCTOS listadas, en el orden dado.
- PROHIBIDO detenerte tras la primera variable.
- Si faltan fuentes para una variable, igual incluye: definicion integradora + propuesta de dimensiones/indicadores (marcando [FUENTE PENDIENTE]).

CONTROL DE LONGITUD (SI NO CABE, DIVIDE):
- Si no puedes terminar todo en una sola respuesta, divide en PARTE 1/N, PARTE 2/N, etc.
- Al final de cada parte escribe EXACTAMENTE: CONTINUAR CON: [lista de variables y secciones pendientes]
- NO escribas conclusiones hasta la ultima parte.

MODO COMPACTO (para 3+ variables):
- Max. 2 definiciones por variable.
- Sintesis critica: 5-7 lineas.
- Definicion integradora: 4-6 lineas.
- Tabla: 2-3 dimensiones, 3-5 indicadores por dimension.
- Prioridad absoluta: completar todas las variables.

FORMATO OBLIGATORIO DE SALIDA:
0. Supuestos de trabajo (solo si faltan datos del usuario)
1. Indice propuesto del marco teorico (4-7 secciones)
2. Marco conceptual y definiciones (por variable/constructo)
   2.1 VARIABLE 1
       (1) Delimitacion conceptual (que incluye / que excluye)
       (2) Definiciones academicas (max. 2) [solo con cita si hay fuente]
       (3) Sintesis critica (similitudes, diferencias, tensiones, limitaciones)
       (4) Definicion integradora propia (derivada de 2 y 3)
       (5) Implicacion para el estudio (como se observara/medira en tu contexto)
       (6) Tabla: Dimensiones e indicadores
   2.2 VARIABLE 2 (mismo esquema) ... hasta terminar TODAS
3. Teorias/modelos que sustentan el estudio [FUENTE PENDIENTE si no hay soporte]
4. Antecedentes empiricos
   4.1 Tabla: Autor/ano | contexto | metodo | muestra | hallazgos | limitaciones | aporte
   4.2 Sintesis integradora
   Si no hay estudios: [NO HAY EVIDENCIA EN FUENTES_PROVISTAS] + terminos de busqueda sugeridos
5. Operacionalizacion segun enfoque:
   Cuantitativo: Variable -> Definicion operacional -> Dimensiones -> Indicadores -> Ejemplos de items -> Escala sugerida
   Cualitativo: Categoria -> Subcategoria -> Evidencias -> Preguntas guia -> Fuentes de datos
   Mixto: ambas + como se integran
6. Vacios de investigacion que el estudio atiende (2-5 puntos)
7. Riesgos de validez / limitaciones del marco teorico (2-5 puntos)
8. COBERTURA FINAL (obligatorio):
   - Variables solicitadas: [...]
   - Variables desarrolladas: [...]
   - Variables pendientes (si hay): [...]
   - Razon: (limite de salida / faltan fuentes / faltan datos)
9. Referencias (APA 7) verificadas (solo las completas provistas)
10. Referencias sugeridas para buscar [SUGERENCIA] (sin fingir verificacion)"""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Marco Teorico IA")
    st.caption("Powered by Claude · Anthropic · v3")
    st.markdown(f'<div class="year-badge">📅 Fuentes: <strong>{RANGO}</strong> (últimos 5 años)<br>Teorías clásicas: sin restricción de año</div>', unsafe_allow_html=True)
    st.markdown("---")

    api_key = st.text_input("API KEY DE ANTHROPIC", type="password", placeholder="sk-ant-...")
    st.caption("Obtener key en console.anthropic.com")
    st.markdown("---")

    modo = st.radio(
        "MODO DE TRABAJO",
        ["ESTRICTO (solo fuentes provistas)", "BORRADOR (sugiere bibliografía)"],
        index=0,
        help="ESTRICTO: no inventa citas. BORRADOR: genera texto y sugiere fuentes [SUGERENCIA]."
    )
    modo_tag = "ESTRICTO" if "ESTRICTO" in modo else "BORRADOR"
    if modo_tag == "ESTRICTO":
        st.markdown('<div class="mode-estricto">🔒 MODO ESTRICTO — sin alucinaciones</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-borrador">✏️ MODO BORRADOR — sugiere fuentes</div>', unsafe_allow_html=True)

    st.markdown("---")
    tema = st.text_area("TEMA / TÍTULO", placeholder="Ej: Impacto del uso de TIC en el aprendizaje matemático en secundaria", height=75)
    problema = st.text_area("PROBLEMA (1 párrafo)", placeholder="Describe brevemente el problema de investigación...", height=75)
    objetivo = st.text_input("OBJETIVO GENERAL", placeholder="Ej: Determinar la relación entre uso de TIC y aprendizaje...")
    obj_esp = st.text_area("OBJETIVOS ESPECÍFICOS (uno por línea)", placeholder="1. Identificar...
2. Analizar...
3. Establecer...", height=80)
    variables = st.text_area("VARIABLES / CONSTRUCTOS", placeholder="V1: uso de TIC
V2: aprendizaje matemático
V3: motivación", height=80)

    col1, col2 = st.columns(2)
    with col1:
        tipo_estudio = st.selectbox("ENFOQUE", ["Cuantitativo", "Cualitativo", "Mixto"])
    with col2:
        tipo_doc = st.selectbox("DOCUMENTO", ["Tesis", "Artículo Científico", "TFM", "Monografía"])

    area = st.selectbox("ÁREA", ["Educación / Pedagogía", "Psicología", "Administración", "Salud / Medicina", "Ingeniería", "Ciencias Sociales", "Economía", "Derecho", "Comunicación"])
    col3, col4 = st.columns(2)
    with col3:
        pais = st.text_input("PAÍS / CONTEXTO", value="Perú")
    with col4:
        norma = st.selectbox("NORMA", ["APA 7a ed.", "Vancouver", "Chicago", "ISO 690", "MLA"])

    poblacion = st.text_input("POBLACIÓN / MUESTRA", placeholder="Ej: 120 estudiantes de 3° secundaria")

    fuentes = st.text_area(
        "FUENTES PROVISTAS (pega fragmentos o fichas)",
        placeholder="[Fuente 1: Autor, Año, Título.\nFragmento pegado o ficha + extracto]\n[Fuente 2: ...]\n\nDejar vacío = modo sin citas reales",
        height=160,
        help="El agente SOLO cita lo que pongas aquí. Mínimo 1 fragmento por variable si quieres citas reales."
    )

    st.markdown("---")
    generar = st.button("⚡ GENERAR MARCO TEÓRICO COMPLETO")

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-box">
    <div class="hero-badge">Agente Académico v3 · Anti-Alucinación · Cobertura Total</div>
    <div class="hero-title">Generador de Marco Teórico</div>
    <div class="hero-sub">Tesis · Artículos Científicos · TFM · Monografías</div>
    <div class="hero-powered">Powered by Claude Anthropic | Fuentes {RANGO}</div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
metricas = [("v3","Anti-Alucinación"),("APA 7","Refs Verificadas"),("10","Secciones"),("2","Modos"),(".docx","Descargable")]
for col, (num, lbl) in zip([m1,m2,m3,m4,m5], metricas):
    col.markdown(f'<div class="metric-card"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="info-box">📌 Modo <strong>{modo_tag}</strong> activo. Período de antecedentes: <strong>{RANGO}</strong>. Completa el formulario lateral, pega tus fuentes y genera.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### ¿Qué genera esta herramienta?")
st.markdown("*Marco teórico completo con rigor académico real, cobertura de todas las variables y sin inventar fuentes:*")
st.markdown(f"""
**🔒 Modo ESTRICTO:** Solo cita lo que tú pegues — marca [FUENTE PENDIENTE] donde falta evidencia

**✏️ Modo BORRADOR:** Genera texto completo marcando [SUGERENCIA] en bibliografía no provista

**📐 Estructura de 10 secciones:**
Supuestos · Índice · Marco conceptual por variable · Teorías · Antecedentes (tabla) · Operacionalización · Vacíos · Limitaciones · Cobertura final · Referencias APA 7

**🛡️ Cobertura total:** Desarrolla TODAS las variables, divide en partes si es necesario

**📅 Período antecedentes:** {RANGO} | Teorías clásicas: sin restricción de año
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
        num_vars = len([v for v in variables.strip().split("\n") if v.strip()])
        modo_compacto = "MODO COMPACTO ACTIVADO (hay 3+ variables): máx. 2 definiciones, síntesis 5-7 líneas, tabla 2-3 dimensiones. PRIORIDAD: completar todas las variables." if num_vars >= 3 else ""

        bloque_fuentes = f"""<<<FUENTES_PROVISTAS>>>
{fuentes.strip() if fuentes.strip() else "[BLOQUE VACIO — no se proveyeron fuentes. Aplicar modo " + modo_tag + ": marcar [FUENTE PENDIENTE] en todo lo que requiera cita.]"}
<<<FIN_FUENTES_PROVISTAS>>>"""

        prompt = f"""MODO: {modo_tag}
{modo_compacto}

DATOS DEL ESTUDIO:
- Tema/Título: {tema}
- Problema: {problema.strip() if problema.strip() else "[No especificado — crear Supuesto de trabajo]"}
- Objetivo general: {objetivo.strip() if objetivo.strip() else "[No especificado]"}
- Objetivos específicos:
{obj_esp.strip() if obj_esp.strip() else "[No especificados]"}
- VARIABLES/CONSTRUCTOS (desarrollar TODAS en orden):
{variables.strip()}
- Enfoque: {tipo_estudio}
- Tipo de documento: {tipo_doc}
- Área: {area}
- País/contexto: {pais}
- Población/muestra: {poblacion.strip() if poblacion.strip() else "[No especificada]"}
- Norma de citación: {norma}
- Período de antecedentes: {RANGO} (últimos 5 años; teorías clásicas: sin restricción de año)

{bloque_fuentes}

INSTRUCCIÓN FINAL:
1. Aplica el checklist anti-alucinación antes de responder.
2. Desarrolla TODAS las variables listadas sin excepción. Si no cabes en una respuesta, divide en PARTE 1/N, PARTE 2/N, etc. y escribe "CONTINUAR CON: [pendientes]" al final de cada parte.
3. Sigue el FORMATO OBLIGATORIO de 10 secciones (0 a 10).
4. La operacionalización debe corresponder al enfoque {tipo_estudio}.
5. Incluye la sección 8 COBERTURA FINAL con checklist de variables.
6. Redacción académica formal en español. Mínimo 6,000 palabras en total."""

        with st.spinner(f"⚡ Generando marco teórico completo en modo {modo_tag}... (3-5 min)"):
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
                doc.add_paragraph(f"Modo: {modo_tag} | Enfoque: {tipo_estudio} | Norma: {norma} | Período: {RANGO} | País: {pais}")
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
