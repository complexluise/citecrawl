import pytest
from pydantic import ValidationError
from src.models import CSVRow

def test_csv_row_model_parses_correctly():
    """
    Tests that the CSVRow model correctly parses a dictionary with Spanish keys
    and that the aliases map to the correct attribute names.
    """
    # Arrange
    data = {
        "ID": 1,
        "Título": "Test Title",
        "Autor(es)": "Test Author",
        "Año de Publicación": "2023",
        "Tipo de Recurso": "Article",
        "Enlace/URL": "https://example.com",
        "Resumen Principal": "This is a summary.",
        "Aspectos Más Relevantes (Relacionado con Bibliotecas)": "Relevant aspect.",
        "Comentarios / Ideas para la Guía": "A comment.",
        "Extracted": False
    }

    # Act
    row = CSVRow(**data)

    # Assert
    assert row.id == 1
    assert row.title == "Test Title"
    assert row.authors == "Test Author"
    assert row.publication_year == "2023"
    assert row.resource_type == "Article"
    assert row.url == "https://example.com"
    assert row.main_summary == "This is a summary."
    assert row.relevant_aspects == "Relevant aspect."
    assert row.comments == "A comment."
    assert row.extracted is False

def test_csv_row_model_handles_missing_data():
    """
    Tests that the CSVRow model handles missing optional data gracefully.
    """
    # Arrange
    data = {
        "ID": 1,
        "Enlace/URL": "https://example.com",
        "Extracted": False
    }

    # Act
    row = CSVRow(**data)

    # Assert
    assert row.id == 1
    assert row.url == "https://example.com"
    assert row.extracted is False
    assert row.title is None
    assert row.authors is None

def test_csv_row_model_validation_error():
    """
    Tests that the CSVRow model raises a ValidationError for missing required fields.
    """
    # Arrange
    data = {
        "ID": 1,
        "Extracted": False
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        CSVRow(**data)
