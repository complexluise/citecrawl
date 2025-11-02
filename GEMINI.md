# Project Overview

This project is a Python-based tool for scraping web pages, extracting bibliographic information, and generating a BibTeX file. It uses the Firecrawl API to scrape web content and pandas to process data from a CSV file. The scraped data is then saved as Markdown files, which are then processed to create a BibTeX bibliography file.

# Development Approach: Test-Driven Development (TDD)

This project follows a strict TDD methodology using the `pytest` framework. The development process is based on the user stories outlined in the `PRD.md` file. For each feature, a failing unit test will be created first, and then the implementation code will be written to make the test pass. The previous code has been moved to the `old/` directory and will be used for reference only.

# Building and Running

## Prerequisites

- Python 3.6+
- uv

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd scrapeAnyPage
    ```

2.  **Create a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your Firecrawl and Gemini API keys:
    ```
    FIRECRAWL_API_KEY=your_firecrawl_api_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

## Running the scripts

Use `uv run` to execute the pipeline commands within the project's virtual environment without needing to activate it first.

1.  **Extract web content:**
    Run the `extract` command with the path to your CSV file:
    ```bash
    uv run python -m src.cli extract data/csv_with_links/input_links.csv
    ```
    This will scrape the URLs in the CSV file and save the content to the `output` directory as Markdown files.

2.  **Enrich content:**
    ```bash
    uv run python -m src.cli enrich
    ```
    This command reads the extracted content and uses the Gemini API to generate summaries and extract bibliographic metadata.

3.  **Generate citations:**
    ```bash
    uv run python -m src.cli cite <GOOGLE_DOC_ID>
    ```
    This command generates a `bibliography.bib` file and updates the citations in the specified Google Doc.

# Testing

To run the test suite, use the following command:

```bash
uv run pytest
```

# Development Conventions

- The project uses the `click` library for creating command-line interfaces.
- The `rich` library is used for logging to provide rich, colorful output.
- The project follows standard Python conventions.
- The project is structured with a `src` directory for the main source code and a `tests` directory for tests.
- The `firecrawl` library is used for web scraping.
- The `google-generativeai` library is for content enrichment.
- The `bibtex2docs` library is used for updating citations in Google Docs.

# Commit Message Conventions

This project uses [Semantic Commit Messages](https://www.conventionalcommits.org/en/v1.0.0/) with emojis for clear and automated versioning.

**Format:** `<type>(<scope>): <emoji> <subject>`

**Example:** `feat(extraction): ✨ Implement core domain logic`

**Common Types:**

*   `feat`: A new feature.
*   `fix`: A bug fix.
*   `docs`: Documentation only changes.
*   `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc).
*   `refactor`: A code change that neither fixes a bug nor adds a feature.
*   `test`: Adding missing tests or correcting existing tests.
*   `chore`: Changes to the build process or auxiliary tools.

**Common Emojis:**

*   ✨ `:sparkles:` when adding a new feature.
*   🐛 `:bug:` when fixing a bug.
*   📝 `:memo:` when writing docs.
*   ♻️ `:recycle:` when refactoring code.
*   ✅ `:white_check_mark:` when adding or updating tests.
*   🔧 `:wrench:` when updating configuration files.
*   🚀 `:rocket:` when deploying.
