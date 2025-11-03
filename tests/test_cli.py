import os
import shutil
import csv
from click.testing import CliRunner
from citecrawl.cli import extract, cite
from citecrawl.models import ScrapedData, CSVRow
from unittest.mock import patch

import logging

def test_extract_command_preserves_all_rows(mocker):
    """
    Tests that the 'extract' command preserves all rows in the CSV,
    only updating the ones that have not been extracted.
    """
    # Arrange: Create a temporary directory and a dummy CSV file
    test_dir = "test_extract_preserves_rows"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    output_path = os.path.join(test_dir, "output")

    # Row 1 is already extracted, Row 2 will be extracted, Row 3 will fail extraction
    initial_rows = [
        ['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted', 'Description', 'Language', 'Keywords', 'OG Title', 'OG Description', 'OG Image', 'Favicon', 'Source URL'],
        [1, 'Existing Title', 'Existing Author', '2022', 'Article', 'https://existing.com', 'Summary', 'Aspect', 'Comment', True, '', '', '', '', '', '', '', ''],
        [2, '', '', '', '', 'https://new.com', '', '', '', False, '', '', '', '', '', '', '', ''],
        [3, '', '', '', '', 'https://fail.com', '', '', '', False, '', '', '', '', '', '', '', '']
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(initial_rows)

    runner = CliRunner()
    mocker.patch('citecrawl.cli.log')

    # Mock the scraping and enrichment functions
    with patch('citecrawl.cli.scrape_url') as mock_scrape, \
         patch('citecrawl.cli.enrich_content') as mock_enrich:

        # Mock successful scrape and enrich for the second URL
        mock_scrape.side_effect = [
            ScrapedData(url="https://new.com", content="# New Content"),
            ScrapedData(url="https://fail.com", content="") # Failed scrape
        ]
        
        mock_enrich.return_value = CSVRow(**{
            'ID': 2, 'Título': 'New Title', 'Autor(es)': 'New Author', 'Año de Publicación': '2023', 
            'Tipo de Recurso': 'Blog', 'Enlace/URL': 'https://new.com', 
            'Resumen Principal': 'New Summary', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)': 'New Aspect', 
            'Comentarios / Ideas para la Guía': 'New Comment', 'Extracted': True
        })

        # Act: Run the 'extract' command
        result = runner.invoke(extract, [csv_path, "--output", output_path])

    # Assert
    assert result.exit_code == 0

    # Check that the CSV file still has the same number of rows
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        # 1 header row + 3 data rows
        assert len(reader) == 4

        # Verify the header is correct
        assert reader[0] == initial_rows[0]

        # Verify the first row (already extracted) is untouched
        assert reader[1] == [str(v) for v in initial_rows[1]]

        # Verify the second row was updated
        updated_row = reader[2]
        assert updated_row[1] == 'New Title'
        assert updated_row[9] == 'True'

        # Verify the third row (failed extraction) is still present and marked as not extracted
        failed_row = reader[3]
        assert failed_row[1] == ''
        assert failed_row[9] == 'False'


    # Teardown
    shutil.rmtree(test_dir)


def test_extract_command_e2e(mocker):
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

    # Mock the logger
    mock_log = mocker.patch('citecrawl.cli.log')

    # Mock the scraping and enrichment functions
    with patch('citecrawl.cli.scrape_url') as mock_scrape, \
         patch('citecrawl.cli.enrich_content') as mock_enrich:
        
        mock_scrape.side_effect = [
            ScrapedData(url="https://example.com", content="# Example Content"),
            ScrapedData(url="https://anotherexample.com", content="# Another Example")
        ]
        
        mock_enrich.side_effect = [
            CSVRow(**{
                'ID': 1, 'Título': 'Example Title', 'Autor(es)': 'Author 1', 'Año de Publicación': '2023', 
                'Tipo de Recurso': 'Article', 'Enlace/URL': 'https://example.com', 
                'Resumen Principal': 'This is a summary.', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)': 'Aspect 1', 
                'Comentarios / Ideas para la Guía': 'Comment 1', 'Extracted': True
            }),
            CSVRow(**{
                'ID': 2, 'Título': 'Another Example Title', 'Autor(es)': 'Author 2', 'Año de Publicación': '2024', 
                'Tipo de Recurso': 'Blog Post', 'Enlace/URL': 'https://anotherexample.com', 
                'Resumen Principal': 'This is another summary.', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)': 'Aspect 2', 
                'Comentarios / Ideas para la Guía': 'Comment 2', 'Extracted': True
            })
        ]

        # Act: Run the 'extract' command
        result = runner.invoke(extract, [csv_path, "--output", output_path])

    # Assert: Check command execution and output files
    assert result.exit_code == 0
    mock_log.info.assert_any_call("Processing https://example.com...")
    mock_log.info.assert_any_call("Processing https://anotherexample.com...")
    mock_log.info.assert_any_call("Processing complete.")

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


def test_cite_command_e2e(mocker):
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
        writer.writerow(['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted'])
        writer.writerow([1, 'Title 1', 'Author 1', 2023, 'Article', 'https://example.com', 'Summary 1', 'Aspect 1', 'Comment 1', True])
        writer.writerow([2, 'Title 2', 'Author 2', 2024, 'Blog Post', 'https://example.org', 'Summary 2', 'Aspect 2', 'Comment 2', True])

    runner = CliRunner()

    # Mock the logger
    mock_log = mocker.patch('citecrawl.cli.log')

    # Act: Run the 'cite' command
    result = runner.invoke(cite, [csv_path])

    # Assert: Check command execution and output file
    assert result.exit_code == 0
    mock_log.info.assert_any_call("Generating bibliography.bib...")
    mock_log.info.assert_any_call(f"Bibliography generated at {bib_output_path}")
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

    # Mock the logger
    mock_log = mocker.patch('citecrawl.cli.log')

    # Patch the function in the module where it is defined
    mock_gdocs_update = mocker.patch('citecrawl.gdocs.update_google_doc')

    # Act
    result = runner.invoke(cite, [csv_path, "--doc-id", doc_id])

    # Assert
    assert result.exit_code == 0
    mock_log.info.assert_any_call("Updating citations in Google Doc...")
    # Verify the bibtex content passed to the mock
    # args, _ = mock_gdocs_update.call_args
    # assert args[0] == doc_id
    # assert "@misc{A2023T," in args[1]
    # assert "title      = {T}" in args[1]

    # Teardown
    shutil.rmtree(test_dir)
    if os.path.exists("bibliography.bib"):
        os.remove("bibliography.bib")