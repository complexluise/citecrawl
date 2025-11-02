### **Product Requirements Document (PRD)**

---

#### **1. Overview**

This document outlines the requirements for the "Web Content to Citation" AI Pipeline. The tool is a command-line interface (CLI) designed to automate the process of collecting, analyzing, and citing web-based resources for research and writing.

#### **2. The User & The Problem**

*   **Who is the user?** A researcher, student, or knowledge worker who needs to process a large number of web articles.
*   **What is the problem?** The user's current workflow is manual and time-consuming. It involves:
    1.  Manually saving content from links.
    2.  Reading through each article to find answers to specific questions.
    3.  Manually finding and formatting bibliographic information for citations.
    4.  Manually updating citations in their documents.

This process is a significant bottleneck, taking time away from actual analysis and writing.

#### **3. User Stories**

*   **Story 1: Extraction:** As a user, I want to provide a CSV file with a list of URLs so that the tool can automatically scrape and save the main content of each page locally.
*   **Story 2: Enrichment:** As a user, I want to provide a specific question for each URL so that an AI can read the content and generate a concise summary that answers my question.
*   **Story 3: Metadata Generation:** As a user, I want the AI to automatically extract key bibliographic metadata (Title, Author, Year, URL) from the content to save me from having to find it myself.
*   **Story 4: Citation Management:** As a user, I want to generate a standard `bibliography.bib` file from all my processed sources so I can easily manage my citations.
*   **Story 5: Google Docs Integration:** As a user, I want to run a single command to update the citations in my Google Doc manuscript, using the generated BibTeX file.

#### **4. Proposed Architecture**

To ensure the project is maintainable, testable, and scalable, we will adopt a structured layout. All source code will reside in a `src` directory, with a separate `tests` directory.

**New File Structure:**

```
scrapeAnyPage/
├── .env
├── .gitignore
├── data/
│   └── input.csv
├── output/
│   └── article_1.md
├── results/
│   └── enriched_metadata.csv
├── src/
│   ├── __init__.py
│   ├── cli.py          # Main entry point with Click commands
│   ├── extraction.py   # Was scraper_module.py
│   ├── enrichment.py   # Was enricher_module.py
│   ├── bibtex.py       # Was bibtex_module.py
│   └── gdocs.py        # Was gdocs_module.py
├── tests/
│   ├── __init__.py
│   ├── test_extraction.py
│   └── test_enrichment.py
├── requirements.txt
├── PRD.md
└── GEMINI.md
```

#### **5. Architecture & Data Flow Diagram (Mermaid)**

This diagram illustrates the flow of data and the interaction between the different components of the pipeline.

```mermaid
graph TD
    subgraph User Input
        A[input.csv with URLs/Prompts]
    end

    subgraph "Step 1: extract"
        B(src/cli.py) -- reads --> A
        B -- calls --> C{src/extraction.py}
        C -- scrapes URL --> D{Firecrawl API}
        C -- saves --> E[output/article_1.md]
        C -- saves --> F[results/metadata.csv]
    end

    subgraph "Step 2: enrich"
        G(src/cli.py) -- reads --> F
        G -- reads --> E
        G -- calls --> H{src/enrichment.py}
        H -- sends content/prompt --> I{Gemini API}
        I -- returns enriched data --> H
        H -- prepends to --> E
        H -- saves --> J[results/enriched_metadata.csv]
    end

    subgraph "Step 3: cite"
        K(src/cli.py) -- reads --> J
        K -- calls --> L{src/bibtex.py}
        L -- generates --> M[bibliography.bib]
        K -- calls --> N{src/gdocs.py}
        N -- uses --> M
        N -- updates --> O{Google Docs API}
    end

    A --> B
    F --> G
    J --> K
```

---
