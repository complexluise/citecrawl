import os
import shutil
import csv
from click.testing import CliRunner
from src.cli import extract
from src.models import ScrapedData
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

    # Teardown: Clean up the temporary directory
    shutil.rmtree(test_dir)
