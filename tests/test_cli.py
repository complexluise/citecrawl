import os
import shutil
import csv
from click.testing import CliRunner
from src.cli import extract, cite
from src.models import ScrapedData, EnrichedData, Bibliography
from unittest.mock import patch

def test_extract_command_e2e():
    """
    End-to-end test for the 'extract' command.
    It simulates the user flow of providing a CSV and getting updated CSV and Markdown files.
    """
    # Arrange: Create a temporary directory and a dummy CSV file
    test_dir = "test_cli_output"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    output_path = os.path.join(test_dir, "output")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted'])
        writer.writerow([1, '', '', '', '', 'https://example.com', '', '', '', False])
        writer.writerow([2, '', '', '', '', 'https://anotherexample.com', '', '', '', False])

    runner = CliRunner()

    # Mock the scraping and enrichment functions
    with patch('src.cli.scrape_url') as mock_scrape, \
         patch('src.cli.enrich_content') as mock_enrich:
        
        mock_scrape.side_effect = [
            ScrapedData(url="https://example.com", content="# Example Content"),
            ScrapedData(url="https://anotherexample.com", content="# Another Example")
        ]
        
        mock_enrich.side_effect = [
            {
                'ID': 1, 'Título': 'Example Title', 'Autor(es)': 'Author 1', 'Año de Publicación': 2023, 
                'Tipo de Recurso': 'Article', 'Enlace/URL': 'https://example.com', 
                'Resumen Principal': 'This is a summary.', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)': 'Aspect 1', 
                'Comentarios / Ideas para la Guía': 'Comment 1', 'Extracted': True
            },
            {
                'ID': 2, 'Título': 'Another Example Title', 'Autor(es)': 'Author 2', 'Año de Publicación': 2024, 
                'Tipo de Recurso': 'Blog Post', 'Enlace/URL': 'https://anotherexample.com', 
                'Resumen Principal': 'This is another summary.', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)': 'Aspect 2', 
                'Comentarios / Ideas para la Guía': 'Comment 2', 'Extracted': True
            }
        ]

        # Act: Run the 'extract' command
        result = runner.invoke(extract, [csv_path, "--output", output_path])

    # Assert: Check command execution and output files
    assert result.exit_code == 0
    assert "Processing https://example.com" in result.output
    assert "Processing https://anotherexample.com" in result.output
    assert "Processing complete" in result.output

    expected_file1 = os.path.join(output_path, "example_com.md")
    expected_file2 = os.path.join(output_path, "anotherexample_com.md")
    assert os.path.exists(expected_file1)
    assert os.path.exists(expected_file2)

    # Assert: Check that the CSV was updated correctly
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows[0]['Título'] == 'Example Title'
        assert rows[0]['Extracted'] == 'True'
        assert rows[1]['Título'] == 'Another Example Title'
        assert rows[1]['Extracted'] == 'True'

    # Teardown: Clean up the temporary directory
    shutil.rmtree(test_dir)


def test_cite_command_e2e():
    """
    End-to-end test for the 'cite' command.
    It checks if the command correctly generates a bibliography.bib file.
    """
    # Arrange: Create a temporary directory and a dummy CSV file
    test_dir = "test_cite_cli"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    bib_output_path = "bibliography.bib"

    # Create dummy CSV file
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recuro', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted'])
        writer.writerow([1, 'Title 1', 'Author 1', 2023, 'Article', 'https://example.com', 'Summary 1', 'Aspect 1', 'Comment 1', True])
        writer.writerow([2, 'Title 2', 'Author 2', 2024, 'Blog Post', 'https://example.org', 'Summary 2', 'Aspect 2', 'Comment 2', True])

    runner = CliRunner()

    # Act: Run the 'cite' command
    result = runner.invoke(cite, [csv_path])

    # Assert: Check command execution and output file
    assert result.exit_code == 0
    assert "Generating bibliography.bib..." in result.output
    assert "Bibliography generated at" in result.output
    assert os.path.exists(bib_output_path)

    # Assert: Check the content of the generated .bib file
    with open(bib_output_path, "r") as f:
        content = f.read()
        assert "@misc{12023Title," in content
        assert "  title      = {Title 1}" in content
        assert "  author     = {Author 1}" in content
        assert "  year       = {2023}" in content
        assert "@misc{22024Title," in content
        assert "  title      = {Title 2}" in content
        assert "  author     = {Author 2}" in content
        assert "  year       = {2024}" in content

    # Teardown
    shutil.rmtree(test_dir)
    if os.path.exists(bib_output_path):
        os.remove(bib_output_path)

def test_cite_command_with_google_docs_integration(mocker):
    """
    Tests that the 'cite' command calls the Google Docs update function
    when a document ID is provided.
    """
    # Arrange
    test_dir = "test_gdocs_cli"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    doc_id = "fake_doc_id"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted'])
        writer.writerow([1, 'T', 'A', 2023, 'Article', 'https://example.com', 'S', 'Aspect 1', 'Comment 1', True])

    runner = CliRunner()
    # Patch the function in the module where it is defined
    mock_gdocs_update = mocker.patch('src.gdocs.update_google_doc')

    # Act
    result = runner.invoke(cite, [csv_path, "--doc-id", doc_id])

    # Assert
    assert result.exit_code == 0
    assert "Updating citations in Google Doc..." in result.output
    mock_gdocs_update.assert_called_once()
    
    # Verify the bibtex content passed to the mock
    args, _ = mock_gdocs_update.call_args
    assert args[0] == doc_id
    assert "@misc{A2023T," in args[1]
    assert "title      = {T}" in args[1]

    # Teardown
    shutil.rmtree(test_dir)
    if os.path.exists("bibliography.bib"):
        os.remove("bibliography.bib")
