from unittest.mock import patch, MagicMock
import sys

# Mock the problematic module before it's imported by the code under test
sys.modules['bibtex2docs'] = MagicMock()

from src.gdocs import update_google_doc

def test_update_google_doc_calls_library_correctly(mocker):
    """
    Tests that the update_google_doc function correctly calls
    the bibtex2docs library with the provided arguments.
    """
    # Arrange
    # The module is already mocked at the top level, but we can re-patch
    # here to control the specific function call within this test.
    mock_update_citations = mocker.patch('src.gdocs.update_citations_in_doc')
    doc_id = "test_doc_id"
    bibtex_content = "@misc{test, title={Test}}"

    # Act
    update_google_doc(doc_id, bibtex_content)

    # Assert
    mock_update_citations.assert_called_once_with(doc_id, bibtex_content)
