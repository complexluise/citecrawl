# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**doc_handler** is a CLI tool for intelligent Markdown editing with AI assistance. It parses Markdown documents into navigable section trees and detects redundancies using LLMs.

**Core problem**: Writing long Markdown documents is chaotic - no structural navigation, late discovery of redundancies, and manual editing of scattered sections.

**MVP goal**: A Python CLI that loads a .md file, parses it into a section tree, detects redundant paragraphs in specific sections using an LLM, and applies changes with human approval.

## Architecture

This project uses **layered architecture** to separate concerns and enable easy testing and scaling:

```
doc_handler/
├── domain/              # Business logic (no external dependencies)
│   ├── models.py        # Pydantic: Document, Section, Redundancy
│   ├── parser.py        # Markdown → Document tree
│   └── analyzer.py      # Protocol/interface for analysis
│
├── infrastructure/      # Concrete implementations
│   ├── llm_analyzer.py  # LLM-based redundancy detection
│   └── file_handler.py  # File I/O, backups, patching
│
└── cli/                 # User interface
    └── commands.py      # Click commands + Rich output
```

### Key principles:
- **Domain layer is pure**: No Click, Rich, or API clients in domain code
- **Test domain without mocks**: Business logic should be testable in isolation
- **Swap implementations easily**: Change LLM provider without touching domain
- **CLI orchestrates**: Commands call domain methods and render with Rich

## Tech Stack

- **CLI Framework**: Click
- **UI/Output**: Rich (colors, tables, progress bars, prompts)
- **Data Validation**: Pydantic (Document, Section, Redundancy models)
- **LLM**: Pluggable (Gemini, OpenAI, etc.)
- **Testing**: pytest

## Development Workflow

### Setup (when code exists)
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run CLI
python -m doc_handler check-redundancy <file.md> "<Section Title>"
```

### Expected CLI interface

```bash
python -m doc_handler check-redundancy mi_tesis.md "Capítulo 2: Metodología"

# Output uses Rich formatting:
# - Colored headers and borders
# - Progress indicators during analysis
# - Tables for redundancy results
# - Interactive prompts for confirmation
# - Diff display with syntax highlighting
```

## User Stories

See [USER_STORIES.md](./USER_STORIES.md) for detailed acceptance criteria. MVP includes:

- **US-001**: Parse Markdown into navigable section tree (5 pts)
- **US-002**: Detect redundancies using LLM (8 pts)
- **US-003**: Apply changes with human approval (3 pts)

Total: 16 story points for 1-week sprint.

## Important Implementation Details

### Markdown Parsing (US-001)
- Must handle edge cases:
  - Code blocks containing `#` (not headings)
  - Lists starting with `#`
  - Headings with special characters
- Section content includes everything until next heading of same/higher level
- Sections are case-sensitive by title

### Redundancy Detection (US-002)
- "Paragraph" = text block separated by blank lines
- Similarity threshold: ≥70%
- Uses **semantic analysis** (LLM), not just lexical similarity
- Analyzes only the specified section, not entire document

### Change Application (US-003)
- **Always creates backup**: `filename.md.backup`
- Default response is "No" - requires explicit `s` or `S`
- Preserves original formatting, encoding (UTF-8), spacing
- Shows diff before applying

## Out of Scope (MVP)

These features are deferred to future versions:
- RAG/citation suggestions (v0.2)
- Transition generation (v0.3)
- Graphical UI (v0.4)
- Linguistic analysis (future)
- Section reordering (manual is fine)

## Git Commit Convention

All commits in this project must include co-authorship attribution:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

<detailed explanation if needed>

Co-Authored-By: Lui Higuera <luise@unal.edu.co>
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Commit Message Format

- **type**: feat, fix, docs, style, refactor, test, chore
- **scope**: Module name (embeddings, parser, cli, etc.)
- **description**: Concise summary in imperative mood

### Examples

```bash
git commit -m "$(cat <<'EOF'
feat(embeddings): Implement intelligent batching to avoid token limit errors

- Add estimate_tokens() function with conservative multilingual estimation
- Split large document embeddings into batches of ~3000 tokens each
- Fixes "Input text exceeds maximum length of 8194 tokens" error

Co-Authored-By: Lui Higuera <luise@unal.edu.co>
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

```bash
git commit -m "$(cat <<'EOF'
fix(parser): Handle empty paragraphs in section detection

Co-Authored-By: Lui Higuera <luise@unal.edu.co>
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Important**: Always use HEREDOC syntax with `cat <<'EOF'` to preserve multi-line commit messages with proper attribution.

## Documentation

- **[PRD.md](./PRD.md)**: Product requirements, problem statement, solution architecture
- **[USER_STORIES.md](./USER_STORIES.md)**: Detailed acceptance criteria, story points, DoD
