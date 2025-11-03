from typing import List
from src.models import Publication

def generate_bibliography_file(publications: List[Publication]) -> str:
    """
    Generates a single BibTeX string from a list of Publication objects.

    Args:
        publications: A list of Publication objects.

    Returns:
        A string containing all the BibTeX entries.
    """
    bibtex_entries = [pub.generate_bibtex_entry() for pub in publications]
    return "\n".join(bibtex_entries)
