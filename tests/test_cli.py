import os
import shutil
import csv
from click.testing import CliRunner
from src.cli import extract, enrich, cite
from src.models import ScrapedData, EnrichedData, Bibliography
from unittest.mock import patch

def test_extract_command_e2e():
    """
    End-to-end test for the 'extract' command.
    It simulates the user flow of providing a CSV and getting Markdown files.
    """
    # Arrange: Create a temporary directory and a dummy CSV file
    test_dir = "test_cli_output"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    output_path = os.path.join(test_dir, "output")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "prompt"])
        writer.writerow(["https://example.com", "What is this?"])
        writer.writerow(["https://anotherexample.com", "What is that?"])

    runner = CliRunner()

    # Mock the scraping function to avoid actual network calls
    with patch('src.cli.scrape_url') as mock_scrape:
        # Configure the mock to return different data for each call
        mock_scrape.side_effect = [
            ScrapedData(url="https://example.com", content="# Example Content"),
            ScrapedData(url="https://anotherexample.com", content="# Another Example")
        ]

        # Act: Run the 'extract' command
        result = runner.invoke(extract, [csv_path, "--output", output_path])

    # Assert: Check command execution and output files
    assert result.exit_code == 0
    assert "Extracting from https://example.com" in result.output
    assert "Extracting from https://anotherexample.com" in result.output
    assert "Extraction complete" in result.output

    expected_file1 = os.path.join(output_path, "example_com.md")
    expected_file2 = os.path.join(output_path, "anotherexample_com.md")
    assert os.path.exists(expected_file1)
    assert os.path.exists(expected_file2)

    with open(expected_file1, "r") as f:
        assert "# Example Content" in f.read()
    with open(expected_file2, "r") as f:
        assert "# Another Example" in f.read()

    # Assert: Check that the metadata CSV was created correctly
    expected_csv_path = os.path.join(output_path, "metadata.csv")
    assert os.path.exists(expected_csv_path)
    with open(expected_csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["url", "prompt", "filename"]
        row1 = next(reader)
        assert row1[0] == "https://example.com"
        assert row1[2] == "example_com.md"
        row2 = next(reader)
        assert row2[0] == "https://anotherexample.com"
        assert row2[2] == "anotherexample_com.md"

    # Teardown: Clean up the temporary directory
    shutil.rmtree(test_dir)

def test_enrich_command_e2e():
    """
    End-to-end test for the 'enrich' command.
    It simulates the user flow of enriching content from a metadata CSV.
    """
    # Arrange: Create a temporary directory and dummy files
    test_dir = "test_enrich_cli"
    os.makedirs(test_dir, exist_ok=True)
    metadata_csv_path = os.path.join(test_dir, "metadata.csv")
    content_filename = "example_com.md"
    content_filepath = os.path.join(test_dir, content_filename)

    # Create dummy metadata.csv
    with open(metadata_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "prompt", "filename"])
        writer.writerow(["https://example.com", "What is this?", content_filename])

    # Create dummy content file
    with open(content_filepath, "w") as f:
        f.write("# Original Content")

    runner = CliRunner()

    # Mock the enrichment function
    with patch('src.cli.enrich_content') as mock_enrich:
        mock_enrich.return_value = EnrichedData(
            summary="This is the AI summary.",
            bibliography=Bibliography(
                title="AI Title", author="AI Author", year=2025
            )
        )

        # Act: Run the 'enrich' command
        result = runner.invoke(enrich, ["--input-dir", test_dir])

    # Assert: Check command execution and output files
    assert result.exit_code == 0
    assert "Enriching content from example_com.md" in result.output
    assert "Enrichment complete" in result.output

    # Assert: Check the enriched_metadata.csv file
    enriched_csv_path = os.path.join(test_dir, "enriched_metadata.csv")
    assert os.path.exists(enriched_csv_path)
    with open(enriched_csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        data = list(reader)[0]
        assert data['url'] == "https://example.com"
        assert data['summary'] == "This is the AI summary."
        assert data['bib_title'] == "AI Title"

    # Assert: Check that the original file was prepended with the summary
    with open(content_filepath, "r") as f:
        content = f.read()
        assert "This is the AI summary." in content
        assert "# Original Content" in content

    # Teardown
    shutil.rmtree(test_dir)

def test_cite_command_e2e():
    """
    End-to-end test for the 'cite' command.
    It checks if the command correctly generates a bibliography.bib file.
    """
    # Arrange: Create a temporary directory and a dummy enriched_metadata.csv
    test_dir = "test_cite_cli"
    os.makedirs(test_dir, exist_ok=True)
    enriched_csv_path = os.path.join(test_dir, "enriched_metadata.csv")
    bib_output_path = "bibliography.bib"

    # Create dummy enriched_metadata.csv
    with open(enriched_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "summary", "bib_title", "bib_author", "bib_year"])
        writer.writerow(["https://example.com", "Summary 1", "Title 1", "Author 1", "2023"])
        writer.writerow(["https://example.org", "Summary 2", "Title 2", "Author 2", "2024"])

    runner = CliRunner()

    # Act: Run the 'cite' command
    result = runner.invoke(cite, ["--input-dir", test_dir])

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
    enriched_csv_path = os.path.join(test_dir, "enriched_metadata.csv")
    doc_id = "fake_doc_id"

    with open(enriched_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "summary", "bib_title", "bib_author", "bib_year"])
        writer.writerow(["https://example.com", "S", "T", "A", "2023"])

    runner = CliRunner()
    # Patch the function in the module where it is defined
    mock_gdocs_update = mocker.patch('src.gdocs.update_google_doc')

    # Act
    result = runner.invoke(cite, ["--input-dir", test_dir, "--doc-id", doc_id])

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
