import streamlit as st
import os

# Load .env locally (development), use st.secrets on Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available on Streamlit Cloud

st.set_page_config(
    page_title="CiteCrawl - AI Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔍 CiteCrawl")
st.markdown("""
**Automatiza la recopilación y citación de recursos web para investigación.**

CiteCrawl ayuda a bibliotecarios y investigadores a:
- 📄 **Extraer** contenido de URLs usando IA
- 🧠 **Enriquecer** metadatos automáticamente
- 📚 **Generar** citas BibTeX listas para usar

---
""")

# Sidebar: API Configuration
st.sidebar.markdown("## ⚙️ Configuración")

with st.sidebar.expander("🔑 API Keys", expanded=False):
    st.markdown("""
    Proporciona tus API keys para utilizar los servicios:
    """)

    firecrawl_key = st.text_input(
        "Firecrawl API Key",
        value=os.getenv("FIRECRAWL_API_KEY", ""),
        type="password",
        help="Tu clave API de Firecrawl para scraping web"
    )

    gemini_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Tu clave API de Google Gemini para enriquecimiento de IA"
    )

    # Store in session state
    st.session_state.firecrawl_key = firecrawl_key
    st.session_state.gemini_key = gemini_key

# Main navigation
st.sidebar.markdown("## 📍 Navegación")

if st.sidebar.button("📄 Extraer URLs", use_container_width=True):
    st.switch_page("pages/01_Extract.py")

if st.sidebar.button("📥 Descargar Resultados", use_container_width=True):
    st.switch_page("pages/02_Export.py")

# Home page content
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🚀 Cómo empezar

    1. **Configura tus API keys** en el panel lateral
    2. **Ve a Extraer URLs** y sube tu CSV
    3. **Revisa los resultados** conforme se procesan
    4. **Descarga** los archivos generados
    """)

with col2:
    st.markdown("""
    ### 📋 Formato CSV requerido

    Tu CSV debe incluir:
    - `Enlace/URL` - URLs a procesar
    - `Título` - (opcional) Título del recurso
    - `Autor(es)` - (opcional) Autor del recurso
    - Otras columnas con preguntas personalizadas

    [📥 Descargar ejemplo](examples/sample_input.csv)
    """)

st.divider()
st.markdown("""
### 💡 Características principales

- **Scraping inteligente** con Firecrawl
- **Enriquecimiento con IA** usando Google Gemini
- **Preguntas personalizadas** en campos CSV
- **Generación automática de BibTeX**
- **Sin límites** en cantidad de URLs
""")

st.markdown("""
---
**⚠️ Nota importante:** CiteCrawl asiste tu investigación pero no reemplaza la verificación manual.
Siempre revisa y valida los datos generados antes de usar en tu trabajo.
""")
