"""Markdown parser"""
import re
from pathlib import Path
from .models import Document, Section, Paragraph


def parse_markdown(content: str, path: Path | None = None, generate_embeddings: bool = False) -> Document:
    """Parse Markdown content into a hierarchical Document structure.

    Supports:
    - Headings levels 1-6 (# to ######)
    - Nested sections (subsections)
    - Code blocks (``` delimited - # inside are not treated as headings)
    - Paragraphs (text blocks separated by blank lines)
    - Optional embedding generation via Jina AI

    Args:
        content: Raw Markdown text
        path: Optional file path for metadata
        generate_embeddings: If True, generate 768-dim vectors for each paragraph using Jina AI

    Returns:
        Document with hierarchical sections and paragraphs

    Example:
        >>> content = "# Chapter 1\\n\\nFirst paragraph."
        >>> doc = parse_markdown(content, generate_embeddings=True)
        >>> doc.sections[0].title
        'Chapter 1'
        >>> len(doc.sections[0].paragraphs[0].embedding)
        768
    """
    lines = content.split('\n')
    all_sections = []  # Flat list of all sections
    current_section = None
    current_paragraph_lines = []
    paragraph_start_line = None
    paragraph_index = 0
    in_code_block = False  # Track if we're inside a code block

    def save_paragraph():
        nonlocal current_paragraph_lines, paragraph_start_line, paragraph_index
        if current_paragraph_lines and current_section is not None:
            text = '\n'.join(current_paragraph_lines).strip()
            # Ignore if paragraph is empty or just looks like a heading marker
            if text and not re.fullmatch(r'#{1,6}', text):
                para = Paragraph(
                    text=text,
                    index=paragraph_index,
                    line_number=paragraph_start_line,
                    embedding=None
                )
                current_section.paragraphs.append(para)
                paragraph_index += 1
            current_paragraph_lines = []
            paragraph_start_line = None

    for line_num, line in enumerate(lines, start=1):
        # Check for code block delimiter
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            # Treat as content
            if current_section is not None:
                if paragraph_start_line is None:
                    paragraph_start_line = line_num
                current_paragraph_lines.append(line)
            continue

        # If inside code block, treat everything as content
        if in_code_block:
            if current_section is not None:
                if paragraph_start_line is None:
                    paragraph_start_line = line_num
                current_paragraph_lines.append(line)
            continue

        # Check for heading (only outside code blocks)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if heading_match:
            # Save any pending paragraph
            save_paragraph()

            # Update end_line of previous section
            if current_section is not None:
                current_section.end_line = line_num - 1
                all_sections.append(current_section)

            # Create new section
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            current_section = Section(
                level=level,
                title=title,
                paragraphs=[],
                subsections=[],
                start_line=line_num,
                end_line=line_num
            )
            paragraph_index = 0

        elif line.strip() == '':
            # Empty line - save paragraph if exists
            save_paragraph()

        else:
            # Content line
            if current_section is not None:
                if paragraph_start_line is None:
                    paragraph_start_line = line_num
                current_paragraph_lines.append(line)

    # Save final paragraph and section
    save_paragraph()
    if current_section is not None:
        current_section.end_line = len(lines)
        all_sections.append(current_section)

    # Build hierarchy
    root_sections = _build_hierarchy(all_sections)

    # Generate embeddings if requested
    if generate_embeddings:
        _add_embeddings_to_sections(root_sections)

    return Document(
        path=path,
        sections=root_sections,
        raw_content=content
    )


def _build_hierarchy(flat_sections: list[Section]) -> list[Section]:
    """Build hierarchical structure from flat list of sections"""
    if not flat_sections:
        return []

    root = []
    stack = []  # Stack of (level, section) to track parents

    for section in flat_sections:
        # Pop stack until we find the parent (level < current)
        while stack and stack[-1][0] >= section.level:
            stack.pop()

        if not stack:
            # Top-level section
            root.append(section)
        else:
            # Add as subsection to parent
            parent = stack[-1][1]
            parent.subsections.append(section)

        # Push current section to stack
        stack.append((section.level, section))

    return root


def _add_embeddings_to_sections(sections: list[Section]) -> None:
    """Recursively add embeddings to all paragraphs in sections"""
    from ..infrastructure.embeddings import generate_embeddings_batch

    # Collect all paragraphs from all sections (including subsections)
    all_paragraphs = []

    def collect_paragraphs(secs: list[Section]):
        for section in secs:
            all_paragraphs.extend(section.paragraphs)
            if section.subsections:
                collect_paragraphs(section.subsections)

    collect_paragraphs(sections)

    if not all_paragraphs:
        return

    # Generate embeddings in batch
    texts = [p.text for p in all_paragraphs]
    embeddings = generate_embeddings_batch(texts)

    # Assign embeddings back to paragraphs
    for paragraph, embedding in zip(all_paragraphs, embeddings):
        paragraph.embedding = embedding
