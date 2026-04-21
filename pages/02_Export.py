import streamlit as st
import pandas as pd
import io
import zipfile
from citecrawl.bibtex import generate_bibliography_file
from citecrawl.models import Publication

st.set_page_config(page_title="Descargar Resultados - CiteCrawl", layout="wide")

st.title("📥 Descargar Resultados")

st.markdown("""
Descarga tus datos procesados en diferentes formatos:
- CSV actualizado con metadatos enriquecidos
- BibTeX para tus referencias
- Archivos Markdown (uno por URL)
""")

# Check if there are results
if not st.session_state.get("processing_results"):
    st.info("👆 Primero procesa URLs en la sección 'Extraer'")
    st.stop()

results = st.session_state.processing_results
results_df = pd.DataFrame(results)

st.subheader(f"✅ {len(results)} URLs procesadas")
st.dataframe(results_df, use_container_width=True)

st.divider()

# Download options
st.subheader("📥 Descargas disponibles")

col1, col2, col3 = st.columns(3)

# 1. CSV Export
with col1:
    csv_buffer = io.StringIO()
    results_df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode()

    st.download_button(
        "📄 CSV Actualizado",
        csv_bytes,
        "citecrawl_results.csv",
        "text/csv",
        use_container_width=True
    )

# 2. BibTeX Export
with col2:
    try:
        # Create Publication objects from results
        publications = []
        for _, row in results_df.iterrows():
            pub = Publication(
                title=row.get("Título", "Unknown"),
                author=row.get("Autor(es)", None),
                year=int(row["Año de Publicación"]) if pd.notna(row.get("Año de Publicación")) else None,
                url=row.get("Enlace/URL", "")
            )
            publications.append(pub)

        bibtex_content = generate_bibliography_file(publications)

        st.download_button(
            "📚 bibliography.bib",
            bibtex_content,
            "bibliography.bib",
            "text/plain",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generando BibTeX: {str(e)}")

# 3. Markdown Files (ZIP)
with col3:
    try:
        # Create ZIP with markdown files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, row in results_df.iterrows():
                title = row.get("Título", f"Document_{idx}").replace("/", "_")[:50]
                filename = f"{idx + 1}_{title}.md"

                # Create markdown content
                markdown_content = f"""---
ID: {row.get('ID', idx)}
Título: {row.get('Título', '')}
Autor(es): {row.get('Autor(es)', '')}
Año de Publicación: {row.get('Año de Publicación', '')}
Tipo de Recurso: {row.get('Tipo de Recurso', '')}
URL: {row.get('Enlace/URL', '')}
---

## Resumen

{row.get('Resumen Principal', '')}

## Aspectos Relevantes

{row.get('Aspectos Más Relevantes (Relacionado con Bibliotecas)', '')}

## Comentarios

{row.get('Comentarios / Ideas para la Guía', '')}
"""
                zip_file.writestr(filename, markdown_content)

        zip_buffer.seek(0)

        st.download_button(
            "📦 Markdown (ZIP)",
            zip_buffer.getvalue(),
            "citecrawl_markdown.zip",
            "application/zip",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error creando ZIP: {str(e)}")

st.divider()

# Additional options
st.subheader("⚙️ Opciones adicionales")

with st.expander("Copiar BibTeX al portapapeles"):
    try:
        publications = []
        for _, row in results_df.iterrows():
            pub = Publication(
                title=row.get("Título", "Unknown"),
                author=row.get("Autor(es)", None),
                year=int(row["Año de Publicación"]) if pd.notna(row.get("Año de Publicación")) else None,
                url=row.get("Enlace/URL", "")
            )
            publications.append(pub)

        bibtex = generate_bibliography_file(publications)
        st.code(bibtex, language="bibtex")
        st.info("Copía el código anterior para pegarlo en tu gestor de referencias")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Reset processing
if st.button("🔄 Nueva búsqueda", use_container_width=True):
    st.session_state.processing_results = []
    st.switch_page("pages/01_Extract.py")
