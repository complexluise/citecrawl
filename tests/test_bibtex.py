import csv
from citecrawl.models import Publication
from citecrawl.bibtex import generate_bibliography_file
import os
import shutil
from click.testing import CliRunner
from citecrawl.cli import cite

def test_generate_bibliography_file():
    """
    Tests that a list of Publication objects is correctly
    converted into a single BibTeX string.
    """
    # Arrange
    publications = [
        Publication(
            title="Test Title 1",
            author="Author One",
            year=2023,
            url="https://example.com/one"
        ),
        Publication(
            title="Test Title 2",
            author="Author Two",
            year=2024,
            url="https://example.com/two"
        ),
        Publication(
            title="Another Title with no author",
            year=2021,
            url="https://example.com/three"
        )
    ]

    # Act
    bibtex_string = generate_bibliography_file(publications)

    # Assert
    # Check for key elements of each entry to be present
    assert "@misc{One2023Test," in bibtex_string
    assert "  title      = {Test Title 1}" in bibtex_string
    assert "  author     = {Author One}" in bibtex_string
    assert "  year       = {2023}" in bibtex_string
    assert "  url        = {https://example.com/one}" in bibtex_string

    assert "@misc{Two2024Test," in bibtex_string
    assert "  title      = {Test Title 2}" in bibtex_string
    assert "  author     = {Author Two}" in bibtex_string
    assert "  year       = {2024}" in bibtex_string
    assert "  url        = {https://example.com/two}" in bibtex_string

    assert "@misc{Unknown2021Another," in bibtex_string
    assert "  title      = {Another Title with no author}" in bibtex_string
    # More specific check to ensure the author *field* is missing
    assert "  author  " not in bibtex_string.split("@misc{Unknown2021Another,")[1]
    assert "  year       = {2021}" in bibtex_string
    assert "  url        = {https://example.com/three}" in bibtex_string

def test_cite_command_appends_to_bib_file(mocker):
    """
    Tests that the 'cite' command appends to an existing bibliography.bib file
    instead of overwriting it.
    """
    # Arrange
    test_dir = "test_cite_append"
    os.makedirs(test_dir, exist_ok=True)
    csv_path = os.path.join(test_dir, "input.csv")
    bib_output_path = "bibliography.bib"

    # Create a dummy CSV file
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Título', 'Autor(es)', 'Año de Publicación', 'Tipo de Recurso', 'Enlace/URL', 'Resumen Principal', 'Aspectos Más Relevantes (Relacionado con Bibliotecas)', 'Comentarios / Ideas para la Guía', 'Extracted'])
        writer.writerow([1, 'New Title', 'New Author', 2025, 'Article', 'https://new.com', '', '', '', True])

    # Create a pre-existing bibliography.bib file
    initial_bib_content = "@misc{Existing, title={Existing Entry}}"
    with open(bib_output_path, "w", encoding="utf-8") as f:
        f.write(initial_bib_content)

    runner = CliRunner()
    mocker.patch('citecrawl.cli.log')

    # Act
    result = runner.invoke(cite, [csv_path])

    # Assert
    assert result.exit_code == 0
    assert os.path.exists(bib_output_path)

    with open(bib_output_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Check that the old content is still there
        assert initial_bib_content in content
        # Check that the new content was added
        assert "@misc{Author2025New," in content
        assert "title      = {New Title}" in content

    # Teardown
    shutil.rmtree(test_dir)
    if os.path.exists(bib_output_path):
        os.remove(bib_output_path)