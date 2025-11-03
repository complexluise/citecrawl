from firecrawl import Firecrawl
from citecrawl.models import ScrapedData, CSVRow
import csv

def load_urls_from_csv(csv_path: str) -> list[CSVRow]:
    """
    Loads URLs from a CSV file and returns a list of CSVRow objects.

    Args:
        csv_path: The path to the CSV file.

    Returns:
        A list of CSVRow objects.
    """
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = []
        for i, row_data in enumerate(reader):
            # Pydantic will use the alias 'Enlace/URL' to populate the 'url' field
            row_data['ID'] = i + 1
            if 'Extracted' not in row_data:
                row_data['Extracted'] = False
            else:
                row_data['Extracted'] = row_data['Extracted'].lower() in ['true', '1', 't', 'y', 'yes']
            rows.append(CSVRow.model_validate(row_data))
        return rows

def scrape_url(row: CSVRow, api_key: str) -> ScrapedData:
    """
    Scrapes a single URL from a CSVRow object using the FirecrawlApp and returns the
    content and metadata wrapped in a ScrapedData object.

    Args:
        row: A CSVRow object representing a row from the CSV file.
        api_key: The API key for the Firecrawl service.

    Returns:
        A ScrapedData object containing the scraped information.
    """
    url = row.url
    try:
        app = Firecrawl(api_key=api_key)
        scraped_result = app.scrape(url=url)
        
        content = scraped_result.markdown
        metadata = dict(scraped_result.metadata)

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
