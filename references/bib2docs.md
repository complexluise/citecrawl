
Working with academic references in Google Docs
August 27, 2019

    tags: bibtex academia 

We are still hoping for an era where citation management software would be free, interoperable, easy to use and nicely integrated with word processing tools.

Until this dream comes true, we need practical solutions. BibTeX is a standard format used by most citation managing systems and initially designed to work with LaTeX. Working with LaTeX allows multiple users to jointly work on a same manuscript using a version control system e.g git. In line with this, LaTeX writers may now opt for several recently emerged online real-time editing platforms (Overleaf), allowing to collaborate on the source and instantly visualize the compiled result. In parallel, other tools such as (Open/Libre/Microsoft) Office have seen developing plugins to allow inserting references from BibTeX (or other) files, offering a popular alternative for non-LaTeX non-git users.

Finally, Google Docs users do not have much option here, as the only existing plugin to work with references in Google Docs comes as a paid service with Paperpile. Hence this post describes a kind of recipe intended for Google Docs users wanting to work with BibTeX references in a shared document.

Consider for example a document including BibTeX reference ID (here preceded by @, as in @Author2019). By taking as inputs the document ID and a BibTeX bibliography source file featuring the cited references, this technique will generate a copy of the document having all reference ID replaced by, either a reference number or a mention such as First Author et al. (2019). It will also compile a full list of the used references to get included e.g. at the end of the document.

The core idea is based on making calls to the Google API from a Python app to apply the right changes to the document. Getting started takes 3 steps:

    download the Python app/script
    enable the Google API and obtain client credentials
    look up the ID of a document and pass it to the app along with the corresponding .bib file.

The app will generate a copy of the document with initial reference ID replaced by their full version as given by the .bib file.

bibtex2docs.py DOCUMENT_ID BIBTEX_FILE CREDENTIALS

example1

example2

example3

example4

More information at http://gitlab.com/xgrg/bibtex2docs.

Install with pip install bibtex2docs .

Please let me know if you liked this post by clicking the button below.

bibtex2docs: insert BibTeX references in Google Docs





Date: 2019, Aug 27 Version: 0.1
Useful links:
Binary Installers
Source Repository
Issues & Ideas

Overview
bibtex2docs finds references in a Google Docs document matching entries
from a BibTeX source file and replaces them either with the name of their first
author (with year of publication) or with numbers linked to a reference list.

Installing

Python version support
Officially Python 3.7.

Installing from PyPI
bibtex2docs can be installed via pip from [PyPI] (https://pypi.org/project/bibtex2docs)

pip install bibtex2docs

Getting started: enabling the Google API
bibtex2docs relies on calls to the Google Docs/Drive API to copy/
modify documents. Therefore it requires some credentials/permissions to run properly.
The first step is to enable the Google API and obtain credentials. This is done
following the instructions there. Follow the
link, enable the Google Docs API and download the client configuration
(credentials.json).
On first execution, access permissions will be asked to modify/create documents.
Access token will be saved on local disk as a pickle object (see example)

Including references in the manuscript
bibtex2docs looks for reference ID starting with an @. Hence to include a
reference from a BibTeX file, insert the BibTeX ID of that reference in the manuscript preceded by an @.
Example:

As suggested by @FirstAuthor2018, (...)

The ID will be replaced either by a reference number (according to the full
reference list) or by First Author et al., 2019. The full list of included references will be compiled and added to the document, only if the tag {{bibliography}} is found somewhere in the text.

Dependencies
bibtex2docs requires the following dependencies (installed by pip):


python v3.7+
google-api-python-client>=1.7.11
google-auth-httplib2>=0.0.3
google-auth-oauthlib>=0.4.0
nameparser>=1.0.4
bibtexparser>=1.1.0

For development purposes:


python-nose v1.2.1+ to run the unit tests

coverage v3.6+


Examples
Using the FirstAuthor et al., 2019 format
Use the following command:
bibtex2docs.py DOCUMENT_ID BIBTEX_FILE CREDENTIALS
A copy of the document (with prefix [BibTeX2Docs] will be created and reference IDs will be replaced as in the following figure: