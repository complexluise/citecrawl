import click
import pandas as pd
import os
from urllib.parse import urlparse
from src.extraction import scrape_url
from src.enrichment import enrich_content
from src.bibtex import generate_bibliography_file
from src.models import ScrapedData, Publication
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@click.group()
def cli():
    """A CLI tool for scraping web content and generating citations."""
    pass

def sanitize_filename(url: str) -> str:
    """Creates a filesystem-safe filename from a URL."""
    parsed_url = urlparse(url)
    # Replace dots and other special characters to avoid issues
    sanitized_netloc = parsed_url.netloc.replace('.', '_')
    sanitized_path = parsed_url.path.replace('/', '_').replace('.', '_')
    # Avoid overly long filenames
    return f"{sanitized_netloc}{sanitized_path[:50]}.md"

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--output', default='output', help='The directory to save the scraped content.')
def extract(csv_path: str, output: str):
    """
    Scrapes URLs from a CSV file, enriches the content, and saves the results.
    """
    # Ensure the output directory exists
    os.makedirs(output, exist_ok=True)

    # Define dtypes for string columns to avoid pandas inferring float for empty ones
    string_cols = ['Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 
                   'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 
                   'Comentarios / Ideas para la Guía']
    dtype_map = {col: str for col in string_cols}
    
    # Read the CSV file
    df = pd.read_csv(csv_path, dtype=dtype_map)
    
    # Get API keys from environment
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not firecrawl_api_key or not gemini_api_key:
        click.echo("Error: FIRECRAWL_API_KEY or GEMINI_API_KEY not found in environment variables.", err=True)
        return

    for index, row in df.iterrows():
        if not row['Extracted']:
            url = row['Enlace/URL']
            click.echo(f"Processing {url}...")
            
            # Scrape the URL
            scraped_data = scrape_url(row=row.to_dict(), api_key=firecrawl_api_key)
            
            if scraped_data and scraped_data.content:
                # Enrich the content
                enriched_row = enrich_content(
                    row=row.to_dict(),
                    scraped_content=scraped_data.content,
                    api_key=gemini_api_key
                )
                
                # Update the DataFrame
                df.loc[index] = pd.Series(enriched_row)
                
                # Save the content to a Markdown file
                filename = sanitize_filename(url)
                filepath = os.path.join(output, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(scraped_data.content)
                click.echo(f"  -> Saved to {filepath}")
            else:
                click.echo(f"  -> Failed to extract content from {url}")

    # Save the updated DataFrame to the CSV file
    df.to_csv(csv_path, index=False)
    click.echo("Processing complete.")

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--doc-id', default=None, help='The Google Doc ID to update with the new citations.')
def cite(csv_path: str, doc_id: str):
    """
    Generates a bibliography.bib file and optionally updates a Google Doc.
    """
    if not os.path.exists(csv_path):
        click.echo(f"Error: {csv_path} not found", err=True)
        return

    click.echo("Generating bibliography.bib...")
    # Define dtypes for string columns to avoid pandas inferring float for empty ones
    string_cols = ['Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 
                   'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 
                   'Comentarios / Ideas para la Guía']
    dtype_map = {col: str for col in string_cols}
    df = pd.read_csv(csv_path, dtype=dtype_map)
    
    # Convert dataframe rows to Publication objects
    publications = [
        Publication(
            title=row['Título'],
            author=row['Autor(es)'],
            year=int(row['Año de Publicación']) if pd.notna(row['Año de Publicación']) else None,
            url=row['Enlace/URL']
        )
        for index, row in df.iterrows()
    ]

    # Generate the .bib file content
    bibtex_content = generate_bibliography_file(publications)

    # Write to bibliography.bib
    bib_output_path = "bibliography.bib"
    with open(bib_output_path, "w", encoding="utf-8") as f:
        f.write(bibtex_content)

    click.echo(f"Bibliography generated at {bib_output_path}")

    # If a Google Doc ID is provided, update the doc
    if doc_id:
        click.echo("Updating citations in Google Doc...")
        try:
            # Dynamic import to avoid issues when bibtex2docs is not installed
            from src.gdocs import update_google_doc
            update_google_doc(doc_id, bibtex_content)
            click.echo("Google Doc update complete.")
        except ImportError:
            click.echo("Error: 'bibtex2docs' is not installed. Please install it to use the Google Docs integration.", err=True)
        except Exception as e:
            click.echo(f"Error updating Google Doc: {e}", err=True)

if __name__ == '__main__':
    cli()
