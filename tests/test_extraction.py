from unittest.mock import patch, MagicMock
from src.extraction import scrape_url
from src.models import ScrapedData

def test_returns_scraped_data_object(mocker):
    """
    Tests that scrape_url function processes a URL, calls the scraper,
    and returns a structured ScrapedData object.
    """
    # Arrange: Configure the mock to simulate a successful scrape
    mock_firecrawl_app = mocker.patch('src.extraction.FirecrawlApp')
    mock_scrape_data = {
        'content': '# Example Domain\nThis domain is for use in illustrative examples.',
        'metadata': {
            'title': 'Example Domain',
            'description': 'An example domain for use in tests.',
        }
    }
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.return_value = mock_scrape_data
    mock_firecrawl_app.return_value = mock_firecrawl_instance

    test_url = "https://example.com"

    # Act: Call the domain function
    result = scrape_url(url=test_url, api_key="fake_key")

    # Assert: Verify the return type and content
    assert isinstance(result, ScrapedData)
    assert result.url == test_url
    assert result.content == mock_scrape_data['content']
    assert result.metadata['title'] == 'Example Domain'

    # Assert: Verify the mock was called correctly
    mock_firecrawl_app.assert_called_once_with(api_key="fake_key")
    mock_firecrawl_instance.scrape.assert_called_once_with(url=test_url)

def test_handles_empty_scrape_result(mocker):
    """
    Tests that the function handles an empty or malformed response
    from the scraping service gracefully.
    """
    # Arrange
    mock_firecrawl_app = mocker.patch('src.extraction.FirecrawlApp')
    mock_scrape_data = {}  # Simulate an empty response
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.return_value = mock_scrape_data
    mock_firecrawl_app.return_value = mock_firecrawl_instance

    test_url = "https://empty.com"

    # Act
    result = scrape_url(url=test_url, api_key="fake_key")

    # Assert
    assert isinstance(result, ScrapedData)
    assert result.url == test_url
    assert result.content == ""
    assert result.metadata == {}
