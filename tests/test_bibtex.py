from src.models import Publication
from src.bibtex import generate_bibliography_file

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
