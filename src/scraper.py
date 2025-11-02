import os
import logging
from firecrawl import Firecrawl
from dotenv import load_dotenv

load_dotenv()

def scrape_url(url: str) -> str:
    """
    Scrapes the content of a single URL using Firecrawl.

    Args:
        url: The URL to scrape.

    Returns:
        The scraped content in Markdown format, or an empty string if an error occurs.
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logging.error("FIRECRAWL_API_KEY environment variable not set.")
        return ""

    try:
        firecrawl = Firecrawl(api_key=api_key)
        scraped_data = firecrawl.scrape(url)
        return scraped_data.markdown
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return ""
