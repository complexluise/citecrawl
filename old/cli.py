import click
import pandas as pd
import os
import logging
from rich.logging import RichHandler
from .scraper import scrape_url
from .enricher import enrich_content
from .bibtex import generate_bibtex
from .gdocs import update_gdocs_citations

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

@click.group()
def cli():
    """A CLI for the AI pipeline."""
    pass

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.option('--output-dir', default='output', help='Directory to save the markdown files.')
def extract(csv_path, output_dir):
    """
    Reads a CSV of URLs, scrapes their content, and saves them as markdown files.
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

    metadata = []
    for index, row in df.iterrows():
        url = row.get('url')
        if not isinstance(url, str) or not url.strip():
            logging.warning(f"Skipping row {index} due to empty or invalid URL.")
            continue

        logging.info(f"Scraping URL: {url}")
        content = scrape_url(url)

        if content:
            filename = f"article_{index + 1}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Saved content to {filepath}")
            metadata.append({
                'source_url': url,
                'local_file': filepath,
                'prompt': row.get('prompt', '')
            })
        else:
            logging.warning(f"Failed to scrape content from {url}")

    # Save metadata
    if metadata:
        metadata_df = pd.DataFrame(metadata)
        results_dir = 'results'
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        metadata_filepath = os.path.join(results_dir, 'metadata.csv')
        metadata_df.to_csv(metadata_filepath, index=False)
        logging.info(f"Metadata saved to {metadata_filepath}")

@cli.command()
@click.option('--metadata-file', default='results/metadata.csv', help='Path to the metadata CSV file.')
def enrich(metadata_file):
    """
    Enriches the scraped content using the Gemini API.
    """
    try:
        df = pd.read_csv(metadata_file)
        logging.info(f"Successfully read metadata file: {metadata_file}")
    except Exception as e:
        logging.error(f"Error reading metadata file: {e}")
        return

    enriched_metadata = []
    for index, row in df.iterrows():
        filepath = row.get('local_file')
        prompt = row.get('prompt')

        if not os.path.exists(filepath):
            logging.warning(f"File not found: {filepath}. Skipping.")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        logging.info(f"Enriching content from {filepath}")
        enriched_content = enrich_content(content, prompt)

        if enriched_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(enriched_content)
            logging.info(f"Successfully enriched {filepath}")

            # Extract metadata from enriched content
            try:
                metadata_part, summary_part = enriched_content.split('### AI Summary', 1)
                metadata_lines = metadata_part.strip().split('\n')
                title = metadata_lines[1].split(':', 1)[1].strip()
                authors = metadata_lines[2].split(':', 1)[1].strip()
                year = metadata_lines[3].split(':', 1)[1].strip()
                url = metadata_lines[4].split(':', 1)[1].strip()
                summary = summary_part.split('---', 1)[0].strip()

                enriched_metadata.append({
                    'source_url': row.get('source_url'),
                    'local_file': filepath,
                    'title': title,
                    'author': authors,
                    'year': year,
                    'ai_summary': summary
                })
            except Exception as e:
                logging.error(f"Error parsing enriched content from {filepath}: {e}")

    # Save enriched metadata
    if enriched_metadata:
        enriched_df = pd.DataFrame(enriched_metadata)
        enriched_filepath = os.path.join('results', 'enriched_metadata.csv')
        enriched_df.to_csv(enriched_filepath, index=False)
        logging.info(f"Enriched metadata saved to {enriched_filepath}")

@cli.command()
@click.argument('doc_id')
@click.option('--input-dir', default='output', help='Directory containing the enriched markdown files.')
@click.option('--output-file', default='bibliography.bib', help='Path to the output BibTeX file.')
def cite(doc_id, input_dir, output_file):
    """
    Generates a BibTeX file and updates citations in a Google Doc.
    """
    generate_bibtex(input_dir, output_file)
    update_gdocs_citations(doc_id, output_file)

if __name__ == '__main__':
    cli()
