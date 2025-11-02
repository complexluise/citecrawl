from unittest.mock import MagicMock, patch
from src.models import ScrapedData, EnrichedData, Bibliography
from src.enrichment import enrich_content
import google.generativeai as genai

def test_enrich_content_returns_enriched_data(mocker):
    """
    Tests that the enrich_content function correctly calls the Gemini API
    and parses its response into an EnrichedData object.
    """
    # Arrange
    # 1. Mock the Gemini API client
    mock_genai_model = MagicMock()
    mock_genai_model.generate_content.return_value.text = """
    {
        "summary": "This is a test summary.",
        "bibliography": {
            "title": "Test Title",
            "author": "Test Author",
            "year": 2023
        }
    }
    """
    # Patch the entire module, not just the class
    mocker.patch('src.enrichment.genai.GenerativeModel', return_value=mock_genai_model)
    mocker.patch('src.enrichment.genai.configure')


    # 2. Create input data
    scraped_data = ScrapedData(
        url="https://example.com",
        content="This is the content of the scraped page.",
        metadata={"title": "Original Title"}
    )
    prompt = "What is the summary and bibliography?"
    api_key = "fake_gemini_key"

    # Act
    result = enrich_content(scraped_data, prompt, api_key)

    # Assert
    # 1. Verify the return type and content
    assert isinstance(result, EnrichedData)
    assert result.summary == "This is a test summary."
    assert isinstance(result.bibliography, Bibliography)
    assert result.bibliography.title == "Test Title"
    assert result.bibliography.author == "Test Author"
    assert result.bibliography.year == 2023

    # 2. Verify the API was called correctly
    genai.configure.assert_called_once_with(api_key=api_key)
    call_args, _ = mock_genai_model.generate_content.call_args
    sent_prompt = call_args[0]
    assert "This is the content of the scraped page." in sent_prompt
    assert "What is the summary and bibliography?" in sent_prompt
    assert "output a JSON object" in sent_prompt
