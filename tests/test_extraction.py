import pytest
from unittest.mock import MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extraction import scrape_url

def test_scrape_url_success(mocker):
    """
    Tests that scrape_url successfully calls the firecrawl API
    and returns the markdown content.
    """
    # Arrange
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.return_value = MagicMock(markdown="Mocked Markdown Content")
    mocker.patch('src.extraction.Firecrawl', return_value=mock_firecrawl_instance)

    test_url = "http://example.com"

    # Act
    result = scrape_url(test_url)

    # Assert
    mock_firecrawl_instance.scrape.assert_called_once_with(url=test_url)
    assert result == "Mocked Markdown Content"

def test_scrape_url_api_key_missing(mocker):
    """
    Tests that scrape_url returns an empty string if the API key is not set.
    """
    # Arrange
    mocker.patch('src.extraction.os.environ.get', return_value=None)

    # Act
    result = scrape_url("http://example.com")

    # Assert
    assert result == ""

def test_scrape_url_firecrawl_exception(mocker):
    """
    Tests that scrape_url returns an empty string if the Firecrawl API raises an exception.
    """
    # Arrange
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.side_effect = Exception("API Error")
    mocker.patch('src.extraction.Firecrawl', return_value=mock_firecrawl_instance)

    # Act
    result = scrape_url("http://example.com")

    # Assert
    assert result == ""
