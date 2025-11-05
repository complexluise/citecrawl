"""Tests for embedding generation"""
import pytest
from unittest.mock import patch, Mock
from doc_handler.infrastructure.embeddings import generate_embedding, generate_embeddings_batch
from doc_handler.domain.exceptions import EmbeddingAPIError


@pytest.fixture
def mock_jina_response():
    """Mock successful Jina AI API response"""
    return {
        "data": [
            {"embedding": [0.1] * 768, "index": 0}
        ]
    }


@pytest.fixture
def mock_jina_batch_response():
    """Mock successful batch Jina AI API response"""
    return {
        "data": [
            {"embedding": [0.1] * 768, "index": 0},
            {"embedding": [0.2] * 768, "index": 1},
            {"embedding": [0.3] * 768, "index": 2}
        ]
    }


# Ciclo 16: Embeddings con Jina AI
@patch("doc_handler.infrastructure.embeddings.requests.post")
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_paragraph_embeddings_generation(mock_post, mock_jina_response):
    """Test generating embeddings for a single paragraph"""
    mock_post.return_value.json.return_value = mock_jina_response
    mock_post.return_value.status_code = 200

    text = "Este es un párrafo de ejemplo."
    embedding = generate_embedding(text)

    assert len(embedding) == 768
    assert embedding == [0.1] * 768

    # Verify API call
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://api.jina.ai/v1/embeddings"
    assert call_args[1]["json"]["input"] == [text]
    assert call_args[1]["json"]["model"] == "jina-embeddings-v3"
    assert call_args[1]["json"]["dimensions"] == 768


# Ciclo 17: Embeddings en batch para eficiencia
@patch("doc_handler.infrastructure.embeddings.requests.post")
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_batch_embeddings_generation(mock_post, mock_jina_batch_response):
    """Test batch processing of embeddings"""
    mock_post.return_value.json.return_value = mock_jina_batch_response
    mock_post.return_value.status_code = 200

    texts = ["Primer párrafo.", "Segundo párrafo.", "Tercer párrafo."]
    embeddings = generate_embeddings_batch(texts)

    assert len(embeddings) == 3
    assert embeddings[0] == [0.1] * 768
    assert embeddings[1] == [0.2] * 768
    assert embeddings[2] == [0.3] * 768

    # Verify only one API call was made
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]["json"]["input"] == texts


# Ciclo 18: Manejo de errores de API
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", None)
def test_embedding_api_error_no_key():
    """Test error when API key is missing"""
    with pytest.raises(EmbeddingAPIError) as exc_info:
        generate_embedding("test")

    assert "JINA_API_KEY not found" in str(exc_info.value)


@patch("doc_handler.infrastructure.embeddings.requests.post")
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_embedding_api_error_http_error(mock_post):
    """Test error handling for HTTP errors"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.raise_for_status.side_effect = Exception("401 error")

    mock_post.return_value = mock_response

    with pytest.raises(EmbeddingAPIError) as exc_info:
        generate_embedding("test")

    assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value) or "Unexpected" in str(exc_info.value)


@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_embedding_empty_text():
    """Test handling of empty text"""
    embedding = generate_embedding("")
    assert embedding == []

    embedding = generate_embedding("   ")
    assert embedding == []


@patch("doc_handler.infrastructure.embeddings.requests.post")
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_batch_embeddings_with_empty_texts(mock_post):
    """Test batch processing with some empty texts"""
    mock_response = {
        "data": [
            {"embedding": [0.1] * 768, "index": 0},
            {"embedding": [0.2] * 768, "index": 1}
        ]
    }
    mock_post.return_value.json.return_value = mock_response
    mock_post.return_value.status_code = 200

    texts = ["First", "", "Second", "  "]
    embeddings = generate_embeddings_batch(texts)

    assert len(embeddings) == 4
    assert embeddings[0] == [0.1] * 768
    assert embeddings[1] == []  # Empty
    assert embeddings[2] == [0.2] * 768
    assert embeddings[3] == []  # Empty (whitespace)
