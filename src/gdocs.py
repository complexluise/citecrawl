from bibtex2docs import update_citations_in_doc

def update_google_doc(doc_id: str, bibtex_content: str):
    """
    Updates the citations in a Google Doc using the bibtex2docs library.

    Args:
        doc_id: The ID of the Google Doc to update.
        bibtex_content: A string containing the BibTeX bibliography.
    """
    update_citations_in_doc(doc_id, bibtex_content)
