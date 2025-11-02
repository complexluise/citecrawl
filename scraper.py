import click
import pandas as pd
from rich.logging import RichHandler
import logging
from firecrawl import Firecrawl
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

@click.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--output-dir', default='output', help='Directory to save the markdown files.')
def main(csv_path, output_dir):
    """
    Reads a CSV file, scrapes URLs from the 'Enlace/URL' column, and saves the content to markdown files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")

    try:
        df = pd.read_csv(csv_path)
        logging.info(f"Successfully read CSV file: {csv_path}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return

    # Check for Firecrawl API key
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logging.error("FIRECRAWL_API_KEY environment variable not set.")
        return

    firecrawl = Firecrawl(api_key=api_key)

    for index, row in df.iterrows():
        try:
            url = row['Enlace/URL']
            if not isinstance(url, str) or not url.strip():
                logging.warning(f"Skipping row {index} due to empty or invalid URL.")
                continue

            title = str(row.get('Título', ''))[:50]
            author = str(row.get('Autor(es)', ''))[:50]
            year = row.get('Año de Publicación', '')

            filename = f"{title}_{author}_{year}.md".replace(' ', '_').replace('/', '_').replace(':', '_').replace('"', '').replace('?', '').replace('*', '')
            filepath = os.path.join(output_dir, filename)

            logging.info(f"Scraping {url}")
            scraped_data = firecrawl.scrape(url, formats=['markdown'])

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {row.get('Título', '')}\n\n")
                f.write(f"**Autor(es):** {row.get('Autor(es)', '')}\n")
                f.write(f"**Año de Publicación:** {row.get('Año de Publicación', '')}\n")
                f.write(f"**Tipo de Recurso:** {row.get('Tipo de Recurso', '')}\n")
                f.write(f"**Enlace/URL:** {url}\n\n")
                f.write(f"## Resumen Principal\n\n{row.get('Resumen Principal', '')}\n\n")
                f.write(f"## Aspectos Más Relevantes (Relacionado con Bibliotecas)\n\n{row.get('Aspectos Más Relevantes (Relacionado con Bibliotecas)', '')}\n\n")
                f.write(f"## Comentarios / Ideas para la Guía\n\n{row.get('Comentarios / Ideas para la Guía', '')}\n\n")
                f.write("---\n\n")
                f.write(scraped_data.markdown)

            logging.info(f"Saved content to {filepath}")

        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")

if __name__ == '__main__':
    main()
