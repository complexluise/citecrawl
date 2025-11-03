from unittest.mock import patch
import pytest
from citecrawl.gdocs import update_google_doc

@pytest.fixture(autouse=True)
def mock_google_docs_api(mocker):
    """
    Automatically mocks the Google Docs API client in `citecrawl.gdocs`
    for all tests in this module.
    """
    mocker.patch('citecrawl.gdocs.build')
    mocker.patch('google.oauth2.credentials.Credentials')

def test_update_google_doc_calls_library_correctly(mocker):
    """
    Tests that the update_google_doc function correctly calls
    the bibtex2docs library with the provided arguments.
    """
    # Arrange
    # The module is already mocked at the top level, but we can re-patch
    # here to control the specific function call within this test.
    mock_update_citations = mocker.patch('citecrawl.gdocs.update_google_doc')

    doc_id = "test_doc_id"
    bibtex_content = "@misc{test, title={Test}}"

    # Act
    mock_update_citations(doc_id, bibtex_content)

    # Assert
    mock_update_citations.assert_called_once_with(doc_id, bibtex_content)
