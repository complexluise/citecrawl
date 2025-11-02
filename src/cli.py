import click
import pandas as pd
import os
from urllib.parse import urlparse
from src.extraction import scrape_url
from src.enrichment import enrich_content
from src.models import ScrapedData
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
    Scrapes the URLs from the given CSV file and saves the content.
    """
    # Ensure the output directory exists
    os.makedirs(output, exist_ok=True)

    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Prepare a list to hold metadata for the new CSV
    metadata_list = []

    # Get API key from environment
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key:
        click.echo("Error: FIRECRAWL_API_KEY not found in environment variables.", err=True)
        return

    for index, row in df.iterrows():
        url = row['url']
        prompt = row.get('prompt', '') # Use .get for optional prompt column
        click.echo(f"Extracting from {url}...")
        
        # Scrape the URL
        scraped_data = scrape_url(url=url, api_key=firecrawl_api_key)
        
        # Save the content to a Markdown file
        if scraped_data and scraped_data.content:
            filename = sanitize_filename(url)
            filepath = os.path.join(output, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(scraped_data.content)
            click.echo(f"  -> Saved to {filepath}")
            # Add metadata to the list
            metadata_list.append({"url": url, "prompt": prompt, "filename": filename})
        else:
            click.echo(f"  -> Failed to extract content from {url}")

    # Save the metadata to a new CSV file
    if metadata_list:
        metadata_df = pd.DataFrame(metadata_list)
        metadata_csv_path = os.path.join(output, "metadata.csv")
        metadata_df.to_csv(metadata_csv_path, index=False)
        click.echo(f"Metadata saved to {metadata_csv_path}")

    click.echo("Extraction complete.")

@cli.command()
@click.option('--input-dir', default='output', help='The directory containing the metadata.csv and content files.')
def enrich(input_dir: str):
    """
    Enriches the scraped content with AI-generated summaries and metadata.
    """
    metadata_path = os.path.join(input_dir, "metadata.csv")
    if not os.path.exists(metadata_path):
        click.echo(f"Error: metadata.csv not found in {input_dir}", err=True)
        return

    df = pd.read_csv(metadata_path)
    enriched_list = []

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        click.echo("Error: GEMINI_API_KEY not found in environment variables.", err=True)
        return

    for index, row in df.iterrows():
        filename = row['filename']
        filepath = os.path.join(input_dir, filename)
        
        if not os.path.exists(filepath):
            click.echo(f"  -> Warning: File {filename} not found. Skipping.")
            continue

        click.echo(f"Enriching content from {filename}...")
        with open(filepath, "r+", encoding="utf-8") as f:
            original_content = f.read()
            scraped_data = ScrapedData(url=row['url'], content=original_content)
            
            enriched_data = enrich_content(
                scraped_data=scraped_data,
                user_prompt=row['prompt'],
                api_key=gemini_api_key
            )

            if enriched_data:
                # Prepend the summary to the file
                f.seek(0, 0)
                f.write(f"# Summary\n\n{enriched_data.summary}\n\n---\n\n{original_content}")
                
                # Append enriched data to our list for the new CSV
                enriched_list.append({
                    "url": row['url'],
                    "summary": enriched_data.summary,
                    "bib_title": enriched_data.bibliography.title,
                    "bib_author": enriched_data.bibliography.author,
                    "bib_year": enriched_data.bibliography.year,
                    "filename": filename
                })
                click.echo(f"  -> Enriched {filename}")
            else:
                click.echo(f"  -> Failed to enrich {filename}")

    # Save the enriched metadata to a new CSV
    if enriched_list:
        enriched_df = pd.DataFrame(enriched_list)
        enriched_csv_path = os.path.join(input_dir, "enriched_metadata.csv")
        enriched_df.to_csv(enriched_csv_path, index=False)
        click.echo(f"Enriched metadata saved to {enriched_csv_path}")

    click.echo("Enrichment complete.")

if __name__ == '__main__':
    cli()
