from unittest.mock import MagicMock
from citecrawl.models import CSVRow, ScrapedData
from citecrawl.enrichment import enrich_content
import google.generativeai as genai

def test_enrich_row_updates_model(mocker):
    """
    Tests that the enrich_content function correctly calls the Gemini API
    and updates the Pydantic model with the enriched data.
    """
    # Arrange
    # 1. Mock the Gemini API client
    mock_genai_model = MagicMock()
    mock_genai_model.generate_content.return_value.text = """
    {
        "Resumen Principal": "This is a test summary.",
        "Título": "Test Title"
    }
    """
    mocker.patch('citecrawl.enrichment.genai.GenerativeModel', return_value=mock_genai_model)
    mocker.patch('citecrawl.enrichment.genai.configure')

    # 2. Create input data
    row = CSVRow(**{
        'ID': 1,
        'Título': '',
        'Autor(es)': '',
        'Año de Publicación': '',
        'Tipo de Recurso': '',
        'Enlace/URL': 'https://example.com',
        'Resumen Principal': '',
        'Aspectos Más Relevantes (Relacionado con Bibliotecas)': '',
        'Comentarios / Ideas para la Guía': '',
        'Extracted': False
    })
    scraped_data = ScrapedData(
        url=row.url,
        content="This is the content of the scraped page.",
        csv_row=row
    )
    api_key = "fake_gemini_key"

    # Act
    result = enrich_content(scraped_data, api_key)

    # Assert
    # 1. Verify the return type and content
    assert isinstance(result, CSVRow)
    assert result.main_summary == "This is a test summary."
    assert result.title == "Test Title"
    assert result.extracted is True

    # 2. Verify the API was called correctly
    genai.configure.assert_called_once_with(api_key=api_key)
    call_args, _ = mock_genai_model.generate_content.call_args
    sent_prompt = call_args[0]
    assert "This is the content of the scraped page." in sent_prompt
    assert "output a JSON object" in sent_prompt
