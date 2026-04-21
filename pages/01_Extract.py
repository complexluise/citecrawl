import streamlit as st
import pandas as pd
import io
import logging
from citecrawl.extraction import load_urls_from_csv, scrape_url
from citecrawl.enrichment import enrich_content
from citecrawl.models import CSVRow

log = logging.getLogger("rich")

st.set_page_config(page_title="Extraer URLs - CiteCrawl", layout="wide")

st.title("📄 Extraer y Enriquecer URLs")

st.markdown("""
Edita la tabla de ejemplo o sube tu CSV. CiteCrawl:
1. Scrapeará el contenido de cada URL
2. Enriquecerá metadatos usando IA
3. Generará un CSV con los datos extraídos
""")

# Check if API keys are configured
if not st.session_state.get("firecrawl_key") or not st.session_state.get("gemini_key"):
    st.warning("⚠️ Configura tus API keys en la página principal")
    st.stop()

# Initialize session state
if "extracted_df" not in st.session_state:
    st.session_state.extracted_df = None
if "processing_results" not in st.session_state:
    st.session_state.processing_results = []

# ============================================================================
# SECTION 1: Tabla de ejemplo editable
# ============================================================================

st.subheader("📋 Tabla de URLs (editable)")

# Default example data with fake URLs
example_data = {
    "ID": [1, 2, 3],
    "Enlace/URL": [
        "https://www.example-ia.com/articulo-machine-learning",
        "https://blog.tech-insights.io/ia-etica",
        "https://research.biblioteca-digital.org/estudio-2024"
    ],
    "Título": ["", "", ""],
    "Autor(es)": ["", "", ""],
    "Año de Publicación": ["", "", ""],
    "Tipo de Recurso": ["Article", "Blog Post", "Report"],
    "Extracted": [False, False, False]
}

example_df = pd.DataFrame(example_data)

# Editable table
edited_df = st.data_editor(
    example_df,
    use_container_width=True,
    num_rows="dynamic",
    key="url_table",
    column_config={
        "Enlace/URL": st.column_config.TextColumn(
            "URL",
            width="large",
            help="URL a procesar"
        ),
        "Extracted": st.column_config.CheckboxColumn(
            "¿Procesada?",
            help="Marca si ya fue procesada"
        )
    }
)

st.caption("✏️ Edita directamente o agrega nuevas filas")

# ============================================================================
# SECTION 2: O subir CSV
# ============================================================================

st.divider()
st.subheader("📁 O importa tu propio CSV")

uploaded_file = st.file_uploader(
    "Carga tu archivo CSV",
    type=["csv"],
    help="CSV con columna 'Enlace/URL'"
)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        if "Enlace/URL" not in df.columns:
            st.error("❌ Tu CSV debe tener una columna 'Enlace/URL'")
            st.stop()
        edited_df = df
        st.success("✅ CSV cargado")
    except Exception as e:
        st.error(f"❌ Error leyendo CSV: {str(e)}")
        st.stop()

# ============================================================================
# SECTION 3: Processing
# ============================================================================

st.divider()

col1, col2 = st.columns(2)

with col1:
    process_unprocessed_only = st.checkbox(
        "Procesar solo URLs no procesadas",
        value=True,
        help="Solo procesa URLs con Extracted=FALSE"
    )

with col2:
    num_urls = len(edited_df[edited_df["Enlace/URL"].notna()])
    st.metric("URLs en tabla", num_urls)

# Process button
if st.button("▶️ Comenzar extracción", type="primary", use_container_width=True):

    # Filter URLs
    urls_to_process = edited_df.copy()
    if process_unprocessed_only and "Extracted" in urls_to_process.columns:
        urls_to_process = urls_to_process[urls_to_process["Extracted"] == False].copy()

    urls_to_process = urls_to_process[urls_to_process["Enlace/URL"].notna()].copy()

    if len(urls_to_process) == 0:
        st.info("✅ Todas las URLs ya han sido procesadas")
        st.stop()

    st.info(f"🔄 Procesando {len(urls_to_process)} URLs...")

    # Progress tracking
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    error_container = st.container()
    results_container = st.container()

    errors = []
    processed_rows = []

    # Process each URL
    for idx, (_, row) in enumerate(urls_to_process.iterrows()):
        url = row.get("Enlace/URL", "").strip()

        if not url:
            errors.append(f"Fila {idx}: URL vacía")
            continue

        # Update status
        progress = (idx + 1) / len(urls_to_process)
        progress_bar.progress(progress)
        status_placeholder.info(f"Procesando {idx + 1}/{len(urls_to_process)}: {url[:60]}...")

        try:
            # Create CSVRow from dict
            row_dict = row.to_dict()
            row_dict["ID"] = row_dict.get("ID", idx + 1)
            csv_row = CSVRow.model_validate(row_dict)

            # Step 1: Scrape
            scraped = scrape_url(csv_row, st.session_state.firecrawl_key)

            if not scraped.content:
                errors.append(f"{url}: No se pudo extraer contenido")
                continue

            # Step 2: Enrich
            enriched_row = enrich_content(scraped, st.session_state.gemini_key)
            enriched_row.extracted = True

            processed_rows.append(enriched_row.model_dump(by_alias=True))

        except Exception as e:
            log.error(f"Error procesando {url}: {str(e)}")
            errors.append(f"{url}: {str(e)[:100]}")

    # Display results
    progress_bar.empty()
    status_placeholder.empty()

    # Show errors if any
    if errors:
        with error_container:
            with st.expander(f"⚠️ Errores ({len(errors)})"):
                for error in errors:
                    st.error(error)

    # Show processed
    if processed_rows:
        with results_container:
            st.success(f"✅ {len(processed_rows)} URLs procesadas exitosamente")

            results_df = pd.DataFrame(processed_rows)
            st.dataframe(results_df, use_container_width=True)

            # Save to session for export
            st.session_state.processing_results = processed_rows
