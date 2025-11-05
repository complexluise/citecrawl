# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CiteCrawl is a Python CLI tool that automates the process of collecting, analyzing, and citing web-based resources for research. It uses AI to extract content from URLs, enrich metadata, and generate BibTeX citations.

**Mission:** The project is specifically designed to build a resource guide for public and community libraries in Ibero-America on integrating AI ethically, critically, and with a human-centered approach.

## Project Philosophy: AI as Assistant, Not Oracle

**CRITICAL**: This project practices what it preaches. It's built to help libraries use AI responsibly, so the codebase itself must reflect this philosophy:

### Core Principles

1. **AI Limitations Are Real**:
   - LLMs can hallucinate (invent plausible-sounding but false information)
   - Paraphrasing can subtly change meanings
   - Summaries reflect the AI's interpretation, not objective truth
   - Bibliographic data may be incorrect or invented

2. **Human Verification Is Mandatory**:
   - The tool reduces tedious work but doesn't eliminate verification
   - Users must review and correct AI outputs
   - The tool positions itself as an "assistant" not an "automation"

3. **Transparency Over Marketing**:
   - README emphasizes limitations prominently
   - Uses language like "draft", "initial", "needs verification"
   - Avoids claims of "eliminating" manual work

4. **Beginner-Friendly Tone**:
   - Documentation is empathetic and clear
   - Assumes readers may be new to command-line tools
   - Explains technical concepts in simple terms
   - Provides concrete examples with real paths

### When Contributing

- Read [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidance on using AI responsibly when developing
- Maintain the honest, clear, and empathetic tone throughout documentation
- Never overstate capabilities or understate limitations
- Always prioritize user understanding over technical brevity

## Core Architecture

The project follows a **modular pipeline architecture** with two main commands:

1. **extract**: Scrapes URLs → Enriches with AI → Saves as Markdown
2. **cite**: Reads enriched data → Generates BibTeX → Optionally updates Google Docs

### Key Components

- **citecrawl/cli.py**: Main entry point using Click for command definitions. Uses Rich for colorful logging.
- **citecrawl/extraction.py**: URL scraping via Firecrawl API
- **citecrawl/enrichment.py**: Content analysis and metadata extraction via Gemini API (google-generativeai library)
- **citecrawl/models.py**: Pydantic models for data validation (`ScrapedData`, `CSVRow`, `Publication`)
- **citecrawl/bibtex.py**: BibTeX generation from publications
- **citecrawl/gdocs.py**: Google Docs integration (currently stubbed, uses bibtex2docs when implemented)

### Technology Stack

- **CLI Framework**: Click (command-line interface)
- **Logging**: Rich (colorful, formatted console output)
- **Web Scraping**: Firecrawl API (firecrawl-py)
- **AI Enrichment**: Google Gemini (google-generativeai)
- **Data Validation**: Pydantic
- **Testing**: pytest, pytest-cov, pytest-mock
- **Environment**: python-dotenv for configuration
- **Google Docs** (optional): bibtex2docs

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
- The `Extracted` column (boolean) tracks which rows have been processed to avoid reprocessing
- The CLI updates the original CSV file **in place** with enriched data - be careful with this behavior
- All Spanish column names are mapped via Pydantic Field aliases (e.g., `Título` → `title`)

### Custom Questions Feature

**Important Feature**: Users can interact with the AI enrichment in two ways:

1. **Leave fields empty** - The AI will attempt to fill them automatically based on the content
2. **Write specific questions** - Users can type questions directly in CSV fields like:
   - "¿Cómo se relaciona esto con bibliotecas?" in "Aspectos Más Relevantes"
   - "¿Qué aplicaciones prácticas tiene?" in "Comentarios / Ideas para la Guía"

The AI will read the entire article content and attempt to answer these specific questions. This makes the tool highly customizable - users aren't limited to generic extraction, they can guide the AI to extract exactly what they need.

**Example CSV with questions**:
```csv
ID,Enlace/URL,Resumen Principal,Aspectos Más Relevantes (Relacionado con Bibliotecas),Comentarios / Ideas para la Guía,Extracted
1,https://example.com,"¿De qué trata?","¿Cómo podría usarlo en mi biblioteca?","¿Qué riesgos éticos debo considerar?",FALSE
```

This is highlighted as a key feature in the README because it significantly increases the tool's utility.

### AI Enrichment Context

**Critical Understanding**: The enrichment module (citecrawl/enrichment.py:22-26) includes a specific `guide_context` that shapes the AI's behavior:

```python
guide_context = """
The overall goal is to build a resource guide for public and community libraries in Ibero-America
on how to integrate artificial intelligence ethically, critically, and with a human-centered approach.
When extracting information, prioritize what would be most useful for a librarian or community mediator.
"""
```

This context is intentional and mission-critical. It:
- Directs Gemini to prioritize ethical considerations
- Focuses on practical applications for libraries
- Emphasizes critical perspectives and community impact
- Is NOT just generic summarization - it's domain-specific extraction

**When modifying enrichment logic**: Preserve this context or the tool loses its purpose.

### BibTeX Append Behavior

**Important**: The `cite` command **appends** to bibliography.bib rather than overwriting (citecrawl/cli.py:141).

- **Why**: Preserves existing citations when processing multiple CSV files
- **Implication**: Users must manually delete bibliography.bib if they want to start fresh
- **Documented**: README.md includes a note about this behavior in the "Paso 2" section

### Error Handling Philosophy

Both scraping and enrichment functions are **defensive**:
- They return partial data rather than crashing on errors
- This allows the pipeline to continue processing other URLs even if one fails
- Failed extractions are logged but don't stop the entire batch
- Users should check logs for URLs that failed to process

### Output Structure

The `extract` command saves results as Markdown files with YAML frontmatter:
```markdown
---
ID: 1
Título: Article Title
Autor(es): Author Name
...
---

[Article content in Markdown]
```

This dual format allows:
- Easy reading of content (Markdown body)
- Machine parsing of metadata (YAML frontmatter)
- Future processing without re-scraping

## Development Approach

This project uses **Test-Driven Development (TDD)** with pytest. Write tests first, then implement features.

For detailed contribution guidelines, including AI usage philosophy and best practices, see [CONTRIBUTING.md](./CONTRIBUTING.md).

### Coverage Badge System

The project uses a **dynamic coverage badge** generated from actual test coverage:
- Badge SVG is generated locally using `coverage-badge` package
- Run `uv run coverage-badge -o coverage.svg` after running tests with coverage
- The badge in README.md references `./coverage.svg` directly
- Badge colors automatically adjust based on coverage percentage (red <50%, yellow 50-80%, green >80%)
- The coverage.svg file should be committed to the repository after updates

## Development Standards

### Code Style
- Follow [PEP 8](https://pep8.org/) for Python code style
- Use descriptive variable names (e.g., `csv_file_path` not `cfp`)
- Write docstrings for all public functions
- Keep functions small and focused on a single responsibility
- Follow standard Python conventions throughout

### Project Structure
```
CiteCrawl/
├── citecrawl/          # Main source code
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # Click commands
│   ├── extraction.py   # Scraping logic
│   ├── enrichment.py   # AI enrichment
│   ├── bibtex.py       # BibTeX generation
│   ├── gdocs.py        # Google Docs integration
│   └── models.py       # Pydantic models
└── tests/              # Test files (mirrors citecrawl/)
    ├── __init__.py
    ├── conftest.py
    ├── test_cli.py
    ├── test_extraction.py
    ├── test_enrichment.py
    ├── test_bibtex.py
    ├── test_gdocs.py
    └── test_models.py
```

## Commit Message Convention

This project uses [Semantic Commit Messages](https://www.conventionalcommits.org/) with emojis for clarity.

**Format**: `<type>(<scope>): <emoji> <subject>`

**Example**: `feat(extraction): ✨ Add PDF support`

### Common Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, dependencies, or auxiliary tools

### Common Emojis

- ✨ `:sparkles:` - New feature
- 🐛 `:bug:` - Bug fix
- 📝 `:memo:` - Documentation
- ♻️ `:recycle:` - Refactoring code
- ✅ `:white_check_mark:` - Tests
- 🔧 `:wrench:` - Configuration files
- 🚀 `:rocket:` - Deployment

### Complete Examples

```bash
feat(extraction): ✨ Add support for PDF file scraping
fix(cli): 🐛 Handle missing CSV columns gracefully
docs(readme): 📝 Update installation instructions
refactor(models): ♻️ Simplify Publication class structure
test(enrichment): ✅ Add test for empty content handling
chore(deps): 🔧 Update firecrawl-py to v2.0
```

## Common Pitfalls and Important Notes

### Command Arguments

**WRONG**:
```bash
uv run python -m citecrawl cite "data\extracted_pages\herramientas_ai_bibliotecas"
```
This passes a **directory** to the cite command, which expects a **CSV file**.

**CORRECT**:
```bash
uv run python -m citecrawl cite "data\csv_with_links\input.csv"
```
The cite command needs the same CSV file used in the extract command, not the output directory.

### Workflow Understanding

The correct flow is:
1. **extract** command: CSV → scrapes → saves Markdown to output dir → updates CSV
2. **cite** command: reads CSV → generates bibliography.bib

Users sometimes confuse the output directory (where Markdown files go) with the input CSV file (which both commands need).

### API Keys

- API keys are only needed for running the actual pipeline (extract/cite commands)
- Tests use mocks and don't require real API keys
- If `.env` is missing, the commands will fail with a clear error message
- The `.env` file should NEVER be committed to git (it's in .gitignore)

### Spanish vs English

The codebase has an intentional mix:
- **User-facing content** (README, CSV columns): Spanish (for Ibero-American libraries)
- **Code and technical docs**: English (standard in programming)
- **This is intentional** - the target users speak Spanish

### Documentation Philosophy

When writing or updating documentation:
- **Assume no prior knowledge** of command-line tools
- **Explain jargon** the first time it's used
- **Provide concrete examples** with real file paths
- **Be honest about limitations** - don't oversell AI capabilities
- **Use empathetic language** - "Si es tu primera vez..." not "Simply run..."

## Related Documentation

- **[CONTRIBUTING.md](./CONTRIBUTING.md)**: Complete contributor guide with AI usage philosophy
- **[GEMINI.md](./GEMINI.md)**: Context file for Google Gemini AI
- **[PRD.md](./PRD.md)**: Product Requirements Document with user stories
- **[README.md](./README.md)**: User-facing documentation (in Spanish)
- Use always uv so you dont need to activate venv.