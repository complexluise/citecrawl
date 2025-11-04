# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CiteCrawl is a Python CLI tool that automates the process of collecting, analyzing, and citing web-based resources for research. It uses AI to extract content from URLs, enrich metadata, and generate BibTeX citations. The project is specifically designed to build a resource guide for public and community libraries in Ibero-America on integrating AI ethically.

## Core Architecture

The project follows a **modular pipeline architecture** with two main commands:

1. **extract**: Scrapes URLs → Enriches with AI → Saves as Markdown
2. **cite**: Reads enriched data → Generates BibTeX → Optionally updates Google Docs

### Key Components

- **citecrawl/cli.py**: Main entry point using Click for command definitions
- **citecrawl/extraction.py**: URL scraping via Firecrawl API
- **citecrawl/enrichment.py**: Content analysis and metadata extraction via Gemini API
- **citecrawl/models.py**: Pydantic models for data validation (`ScrapedData`, `CSVRow`, `Publication`)
- **citecrawl/bibtex.py**: BibTeX generation from publications
- **citecrawl/gdocs.py**: Google Docs integration (currently stubbed)

### Data Flow

```
CSV (with URLs)
  → Firecrawl API (scrape content)
  → Gemini API (enrich metadata, extract bibliographic info)
  → Markdown files (output/) + Updated CSV
  → BibTeX generation (bibliography.bib)
  → Optional Google Docs update
```

### Data Models

The **CSVRow** model (citecrawl/models.py:61-83) is central to the pipeline. It uses Pydantic Field aliases to map Spanish column names to Python attributes:
- Spanish columns: `Enlace/URL`, `Título`, `Autor(es)`, `Año de Publicación`, etc.
- Plus metadata fields: `description`, `language`, `keywords`, `og_title`, etc.

The `extracted` field (boolean) tracks processing status.

## Development Commands

### Setup

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Configure API keys in .env
FIRECRAWL_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### Running the Pipeline

```bash
# Extract and enrich content from CSV
uv run python -m citecrawl extract path/to/input.csv [--output output_dir]

# Generate bibliography.bib file
uv run python -m citecrawl cite path/to/input.csv [--doc-id GOOGLE_DOC_ID]

# Run full pipeline (Windows PowerShell)
.\run_pipeline.ps1
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=citecrawl

# Run specific test file
uv run pytest tests/test_extraction.py
```

Test configuration is in pyproject.toml with `pythonpath = "citecrawl"`.

## Important Implementation Details

### CSV Processing
- The CSV must have a column named `Enlace/URL` (this is the URL source)
- The `Extracted` column tracks which rows have been processed
- The CLI updates the original CSV file in place with enriched data
- All Spanish column names are mapped via Pydantic Field aliases

### AI Enrichment Context
The enrichment module (citecrawl/enrichment.py:22-26) includes a specific guide_context about building resources for Ibero-American libraries. This context shapes how the AI analyzes content - it prioritizes ethical considerations, practical applications, and community impact relevant to librarians.

### BibTeX Append Behavior
The `cite` command **appends** to bibliography.bib rather than overwriting (citecrawl/cli.py:141). This preserves existing citations.

### Error Handling
Both scraping and enrichment functions are defensive - they return partial data rather than crashing on errors, allowing the pipeline to continue processing other URLs.

## Development Approach

This project uses **Test-Driven Development (TDD)** with pytest. Write tests first, then implement features.

## Commit Message Convention

Uses Semantic Commit Messages with emojis:
- `feat(scope): ✨ description` - New feature
- `fix(scope): 🐛 description` - Bug fix
- `refactor(scope): ♻️ description` - Code refactoring
- `test(scope): ✅ description` - Test changes
- `chore(scope): 🔧 description` - Configuration changes
- `docs(scope): 📝 description` - Documentation only
