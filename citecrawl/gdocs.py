# from bibtex2docs import update_citations_in_doc
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os

def update_google_doc(doc_id: str, bibtex_content: str):
    """
    Updates a Google Doc with the given BibTeX content.
    """
    # TODO: Fix the bibtex2docs dependency and uncomment the following lines
    # creds = authenticate_google_docs()
    # service = build('docs', 'v1', credentials=creds)
    # update_citations_in_doc(service, doc_id, bibtex_content)
    pass
