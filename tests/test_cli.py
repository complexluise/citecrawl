import os
import shutil
import csv
from click.testing import CliRunner
from src.cli import extract, enrich
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