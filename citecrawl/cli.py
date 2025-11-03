import click
import pandas as pd
import os
import logging
import sys
from rich.logging import RichHandler
from rich.console import Console
from urllib.parse import urlparse
from citecrawl.extraction import scrape_url, load_urls_from_csv
from citecrawl.enrichment import enrich_content
from citecrawl.bibtex import generate_bibliography_file
import csv
from citecrawl.models import ScrapedData, Publication, CSVRow
from dotenv import load_dotenv

import sys
from rich.console import Console

# --- Logger Setup ---
# Configure logging to use RichHandler for beautiful output
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[]
)
log = logging.getLogger("rich")

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

    # Load the data from the CSV file
    rows = load_urls_from_csv(csv_path)
    
    # Get API keys from environment
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not firecrawl_api_key or not gemini_api_key:
        log.error("FIRECRAWL_API_KEY or GEMINI_API_KEY not found in environment variables.")
        return

    updated_rows = []
    for row in rows:
        if not row.extracted:
            log.info(f"Processing {row.url}...")
            
            # Scrape the URL
            scraped_data = scrape_url(row=row, api_key=firecrawl_api_key)
            
            if scraped_data and scraped_data.content:
                # Enrich the content
                row = enrich_content(
                    row=row,
                    scraped_content=scraped_data.content,
                    api_key=gemini_api_key
                )
                
                # Save the content to a Markdown file
                filename = sanitize_filename(row.url)
                filepath = os.path.join(output, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    # Write the enriched data as YAML front matter
                    f.write("---\n")
                    for field, value in row.model_dump(by_alias=True).items():
                        f.write(f"{field}: {value}\n")
                    f.write("---\n\n")
                    f.write(scraped_data.content)
                log.info(f"  -> Saved to {filepath}")
            else:
                log.warning(f"  -> Failed to extract content from {row.url}")
        updated_rows.append(row)

    # Save the updated data to the CSV file
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([field.alias for field in CSVRow.model_fields.values()])
        for row in updated_rows:
            writer.writerow(row.model_dump(by_alias=True).values())
    log.info("Processing complete.")

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--doc-id', default=None, help='The Google Doc ID to update with the new citations.')
def cite(csv_path: str, doc_id: str):
    """
    Generates a bibliography.bib file and optionally updates a Google Doc.
    """
    if not os.path.exists(csv_path):
        log.error(f"Error: {csv_path} not found")
        return

    log.info("Generating bibliography.bib...")
    rows = load_urls_from_csv(csv_path)
    
    # Convert CSVRow objects to Publication objects
    publications = [
        Publication(
            title=row.title,
            author=row.authors,
            year=int(row.publication_year) if row.publication_year else None,
            url=row.url
        )
        for row in rows
    ]

    # Generate the .bib file content
    bibtex_content = generate_bibliography_file(publications)

    # Write to bibliography.bib
    bib_output_path = "bibliography.bib"
    with open(bib_output_path, "w", encoding="utf-8") as f:
        f.write(bibtex_content)

    log.info(f"Bibliography generated at {bib_output_path}")

    # If a Google Doc ID is provided, update the doc
    if doc_id:
        log.info("Updating citations in Google Doc...")
        try:
            # Dynamic import to avoid issues when bibtex2docs is not installed
            from src.gdocs import update_google_doc
            update_google_doc(doc_id, bibtex_content)
            log.info("Google Doc update complete.")
        except ImportError:
            log.error("'bibtex2docs' is not installed. Please install it to use the Google Docs integration.")
        except Exception as e:
            log.error(f"Error updating Google Doc: {e}")

if __name__ == '__main__':
    log = logging.getLogger("rich")
    console = Console(file=sys.stdout)
    handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    log.addHandler(handler)
    cli()
