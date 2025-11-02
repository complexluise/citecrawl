import click
import pandas as pd
import os
from urllib.parse import urlparse
from src.extraction import scrape_url
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
    
    # Get API key from environment
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key:
        click.echo("Error: FIRECRAWL_API_KEY not found in environment variables.", err=True)
        return

    for index, row in df.iterrows():
        url = row['url']
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
        else:
            click.echo(f"  -> Failed to extract content from {url}")

    click.echo("Extraction complete.")

if __name__ == '__main__':
    cli()
