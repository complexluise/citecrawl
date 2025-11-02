from firecrawl import FirecrawlApp
from src.models import ScrapedData
import pandas as pd

def load_urls_from_csv(csv_path: str) -> list[dict]:
    """
    Loads URLs from a CSV file.

    Args:
        csv_path: The path to the CSV file.

    Returns:
        A list of dictionaries, where each dictionary represents a row in the CSV file.
    """
    df = pd.read_csv(csv_path)
    return df.to_dict('records')

def scrape_url(row: dict, api_key: str) -> ScrapedData:
    """
    Scrapes a single URL from a dictionary row using the FirecrawlApp and returns the
    content and metadata wrapped in a ScrapedData object.

    Args:
        row: A dictionary representing a row from the CSV file.
        api_key: The API key for the Firecrawl service.

    Returns:
        A ScrapedData object containing the scraped information.
    """
    url = row['Enlace/URL']
    try:
        app = FirecrawlApp(api_key=api_key)
        scraped_result = app.scrape(url=url)

        # Ensure scraped_result is a dictionary
        if not isinstance(scraped_result, dict):
            # Handle cases where the scrape might not return the expected dict
            # (e.g., errors, empty responses)
            return ScrapedData(url=url)

        content = scraped_result.get('content', '')
        metadata = scraped_result.get('metadata', {})

        return ScrapedData(
            url=url,
            content=content,
            metadata=metadata
        )
    except Exception as e:
        # In case of an exception during the scrape, return an empty ScrapedData object
        # to ensure the function is robust. A logging mechanism could be added here.
        print(f"An error occurred while scraping {url}: {e}")
        return ScrapedData(url=url)
