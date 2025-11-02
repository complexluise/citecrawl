# Project Overview

This project is a Python-based tool for scraping web pages, extracting bibliographic information, and generating a BibTeX file. It uses the Firecrawl API to scrape web content and pandas to process data from a CSV file. The scraped data is then saved as Markdown files, which are then processed to create a BibTeX bibliography file.

# Building and Running

## Prerequisites

- Python 3.6+
- Pip

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd scrapeAnyPage
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your Firecrawl API key:
    ```
    FIRECRAWL_API_KEY=your_api_key
    ```

## Running the scripts

1.  **Scrape web pages:**
    Run the `scraper.py` script with the path to your CSV file:
    ```bash
    python scraper.py path/to/your/file.csv
    ```
    This will scrape the URLs in the CSV file and save the content to the `output` directory as Markdown files.

2.  **Generate BibTeX file:**
    Run the `generate_bibtex.py` script:
    ```bash
    python generate_bibtex.py
    ```
    This will process the Markdown files in the `output` directory and generate a `bibliography.bib` file.

# Development Conventions

- The project uses the `click` library for creating command-line interfaces.
- The `rich` library is used for logging to provide rich, colorful output.
- The project follows standard Python conventions.
