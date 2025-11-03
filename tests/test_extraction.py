from unittest.mock import patch, MagicMock
from citecrawl.extraction import scrape_url, load_urls_from_csv
from citecrawl.models import ScrapedData, CSVRow
import pandas as pd
import pytest

def test_load_urls_from_csv(tmp_path):
    """
    Tests that load_urls_from_csv function reads a CSV and returns a list of CSVRow objects.
    """
    # Arrange
    csv_content = """ID,Título,Autor(es),Año de Publicación,Tipo de Recurso,Enlace/URL,Resumen Principal,Aspectos Más Relevantes (Relacionado con Bibliotecas),Comentarios / Ideas para la Guía,Extracted
1,"Title 1","Author 1",2023,"Article","http://example.com/1","Summary 1","Aspect 1","Comment 1",False
2,"Title 2","Author 2",2024,"Blog Post","http://example.com/2","Summary 2","Aspect 2","Comment 2",True
"""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(csv_content, encoding='utf-8')

    # Act
    result = load_urls_from_csv(csv_path)

    # Assert
    assert len(result) == 2
    assert isinstance(result[0], CSVRow)
    assert result[0].id == 1
    assert result[0].url == "http://example.com/1"
    assert result[0].extracted is False
    assert isinstance(result[1], CSVRow)
    assert result[1].id == 2
    assert result[1].url == "http://example.com/2"
    assert result[1].extracted is True

def test_returns_scraped_data_object(mocker):
    """
    Tests that scrape_url function processes a URL from a dictionary, calls the scraper,
    and returns a structured ScrapedData object.
    """
    # Arrange: Configure the mock to simulate a successful scrape
    mock_firecrawl = mocker.patch('citecrawl.extraction.Firecrawl')
    mock_scrape_data = MagicMock()
    mock_scrape_data.markdown = '# Example Domain\nThis domain is for use in illustrative examples.'
    mock_scrape_data.metadata = {
        'title': 'Example Domain',
        'description': 'An example domain for use in tests.',
    }
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.return_value = mock_scrape_data
    mock_firecrawl.return_value = mock_firecrawl_instance

    test_row = CSVRow(
        ID=1,
        Título="Test Title",
        **{"Autor(es)": "Test Author"},
        **{"Año de Publicación": "2023"},
        **{"Tipo de Recurso": "Article"},
        **{"Enlace/URL": "https://example.com"},
        **{"Resumen Principal": ""},
        **{"Aspectos Más Relevantes (Relacionado con Bibliotecas)": ""},
        **{"Comentarios / Ideas para la Guía": ""},
        Extracted=False
    )

    # Act: Call the domain function
    result = scrape_url(row=test_row, api_key="fake_key")

    # Assert: Verify the return type and content
    assert isinstance(result, ScrapedData)
    assert result.url == test_row.url
    assert result.content == mock_scrape_data.markdown
    assert result.metadata['title'] == 'Example Domain'

    # Assert: Verify the mock was called correctly
    mock_firecrawl.assert_called_once_with(api_key="fake_key")
    mock_firecrawl_instance.scrape.assert_called_once_with(url=test_row.url)

def test_handles_empty_scrape_result(mocker):
    """
    Tests that the function handles an empty or malformed response
    from the scraping service gracefully.
    """
    # Arrange
    mock_firecrawl = mocker.patch('citecrawl.extraction.Firecrawl')
    mock_scrape_data = MagicMock()
    mock_scrape_data.markdown = ""
    mock_scrape_data.metadata = {}
    mock_firecrawl_instance = MagicMock()
    mock_firecrawl_instance.scrape.return_value = mock_scrape_data
    mock_firecrawl.return_value = mock_firecrawl_instance

    test_row = CSVRow(
        ID=1,
        Título="Test Title",
        **{"Autor(es)": "Test Author"},
        **{"Año de Publicación": "2023"},
        **{"Tipo de Recurso": "Article"},
        **{"Enlace/URL": "https://empty.com"},
        **{"Resumen Principal": ""},
        **{"Aspectos Más Relevantes (Relacionado con Bibliotecas)": ""},
        **{"Comentarios / Ideas para la Guía": ""},
        Extracted=False
    )

    # Act
    result = scrape_url(row=test_row, api_key="fake_key")

    # Assert
    assert isinstance(result, ScrapedData)
    assert result.url == test_row.url
    assert result.content == ""
    assert result.metadata == {}
