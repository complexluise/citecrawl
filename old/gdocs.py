import subprocess
import logging

def update_gdocs_citations(doc_id: str, bib_file: str = 'bibliography.bib', creds_file: str = 'credentials.json'):
    """
    Updates citations in a Google Doc using the bibtex2docs library.

    Args:
        doc_id: The ID of the Google Doc to update.
        bib_file: The path to the BibTeX file.
        creds_file: The path to the Google API credentials file.
    """
    try:
        logging.info(f"Updating citations in Google Doc: {doc_id}")
        command = [
            'bibtex2docs.py',
            doc_id,
            bib_file,
            creds_file
        ]
        subprocess.run(command, check=True)
        logging.info("Successfully updated citations.")
    except FileNotFoundError:
        logging.error("The 'bibtex2docs.py' command was not found.")
        logging.error("Please ensure that the 'bibtex2docs' library is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running bibtex2docs.py: {e}")

