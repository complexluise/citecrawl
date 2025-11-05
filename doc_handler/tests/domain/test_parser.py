"""Tests for Markdown parser"""
from pathlib import Path
from unittest.mock import patch
from doc_handler.domain.parser import parse_markdown
from doc_handler.domain.models import Document, Section, Paragraph
import pytest


# Ciclo 1: Documento simple con un heading
def test_parse_single_heading_no_content():
    """Test parsing a single heading with no content"""
    content = "# Introducción"
    doc = parse_markdown(content, path=Path("test.md"))

    assert isinstance(doc, Document)
    assert doc.path == Path("test.md")
    assert doc.raw_content == content
    assert len(doc.sections) == 1

    section = doc.sections[0]
    assert section.level == 1
    assert section.title == "Introducción"
    assert section.paragraphs == []
    assert section.subsections == []
    assert section.start_line == 1
    assert section.end_line == 1


# Ciclo 2: Heading con contenido simple
def test_parse_single_heading_with_one_paragraph():
    """Test parsing a heading with one paragraph"""
    content = "# Introducción\n\nEste es el primer párrafo."
    doc = parse_markdown(content)

    assert len(doc.sections) == 1
    section = doc.sections[0]
    assert section.title == "Introducción"
    assert len(section.paragraphs) == 1

    para = section.paragraphs[0]
    assert para.text == "Este es el primer párrafo."
    assert para.index == 0
    assert para.line_number == 3
    assert section.start_line == 1
    assert section.end_line == 3


# Ciclo 3: Múltiples párrafos
def test_parse_section_with_multiple_paragraphs():
    """Test parsing a section with multiple paragraphs"""
    content = """# Capítulo 1

Primer párrafo con varias líneas
que continúan aquí.

Segundo párrafo separado por línea vacía.

Tercer párrafo."""

    doc = parse_markdown(content)
    section = doc.sections[0]
    assert len(section.paragraphs) == 3

    assert section.paragraphs[0].text == "Primer párrafo con varias líneas\nque continúan aquí."
    assert section.paragraphs[0].index == 0
    assert section.paragraphs[0].line_number == 3

    assert section.paragraphs[1].text == "Segundo párrafo separado por línea vacía."
    assert section.paragraphs[1].index == 1
    assert section.paragraphs[1].line_number == 6

    assert section.paragraphs[2].text == "Tercer párrafo."
    assert section.paragraphs[2].index == 2
    assert section.paragraphs[2].line_number == 8


# Ciclo 4: Múltiples secciones de mismo nivel
def test_parse_multiple_sections_same_level():
    """Test parsing multiple sections at the same level"""
    content = """# Capítulo 1

Contenido del capítulo 1.

# Capítulo 2

Contenido del capítulo 2."""

    doc = parse_markdown(content)
    assert len(doc.sections) == 2

    assert doc.sections[0].title == "Capítulo 1"
    assert len(doc.sections[0].paragraphs) == 1
    assert doc.sections[0].paragraphs[0].text == "Contenido del capítulo 1."

    assert doc.sections[1].title == "Capítulo 2"
    assert len(doc.sections[1].paragraphs) == 1
    assert doc.sections[1].paragraphs[0].text == "Contenido del capítulo 2."


# Ciclo 5: Jerarquía de secciones (subsecciones)
def test_parse_nested_sections():
    """Test parsing nested sections (hierarchy)"""
    content = """# Capítulo 1

Introducción al capítulo.

## Sección 1.1

Contenido de la sección 1.1.

## Sección 1.2

Contenido de la sección 1.2.

# Capítulo 2

Nuevo capítulo."""

    doc = parse_markdown(content)
    assert len(doc.sections) == 2

    # Capítulo 1 con subsecciones
    cap1 = doc.sections[0]
    assert cap1.title == "Capítulo 1"
    assert cap1.level == 1
    assert len(cap1.paragraphs) == 1
    assert cap1.paragraphs[0].text == "Introducción al capítulo."
    assert len(cap1.subsections) == 2

    # Subsecciones de Capítulo 1
    assert cap1.subsections[0].title == "Sección 1.1"
    assert cap1.subsections[0].level == 2
    assert len(cap1.subsections[0].paragraphs) == 1
    assert cap1.subsections[0].paragraphs[0].text == "Contenido de la sección 1.1."

    assert cap1.subsections[1].title == "Sección 1.2"
    assert cap1.subsections[1].level == 2
    assert len(cap1.subsections[1].paragraphs) == 1
    assert cap1.subsections[1].paragraphs[0].text == "Contenido de la sección 1.2."

    # Capítulo 2 sin subsecciones
    cap2 = doc.sections[1]
    assert cap2.title == "Capítulo 2"
    assert cap2.level == 1
    assert len(cap2.subsections) == 0
    assert len(cap2.paragraphs) == 1
    assert cap2.paragraphs[0].text == "Nuevo capítulo."


# Ciclo 6: Todos los niveles de headings
def test_parse_all_heading_levels():
    """Test parsing all heading levels (1-6)"""
    content = """# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6"""

    doc = parse_markdown(content)

    # Level 1 should have Level 2 as subsection
    assert len(doc.sections) == 1
    assert doc.sections[0].level == 1
    assert doc.sections[0].title == "Level 1"

    # Navigate hierarchy
    level2 = doc.sections[0].subsections[0]
    assert level2.level == 2
    assert level2.title == "Level 2"

    level3 = level2.subsections[0]
    assert level3.level == 3
    assert level3.title == "Level 3"

    level4 = level3.subsections[0]
    assert level4.level == 4
    assert level4.title == "Level 4"

    level5 = level4.subsections[0]
    assert level5.level == 5
    assert level5.title == "Level 5"

    level6 = level5.subsections[0]
    assert level6.level == 6
    assert level6.title == "Level 6"


# Ciclo 7: Headings con caracteres especiales
def test_parse_heading_with_special_characters():
    """Test parsing headings with special characters"""
    content = """# ¿Qué es la IA?

# Título con "comillas"

# Título con @#$%&*"""

    doc = parse_markdown(content)
    assert len(doc.sections) == 3
    assert doc.sections[0].title == "¿Qué es la IA?"
    assert doc.sections[1].title == 'Título con "comillas"'
    assert doc.sections[2].title == "Título con @#$%&*"


# Ciclo 8: Bloques de código NO son headings
def test_parse_ignore_headings_in_code_blocks():
    """Test that # inside code blocks are not parsed as headings"""
    content = """# Capítulo Real

Este es contenido normal.

```python
# Este es un comentario en código
def funcion():
    # Otro comentario
    pass
```

Texto después del código."""

    doc = parse_markdown(content)
    assert len(doc.sections) == 1
    assert doc.sections[0].title == "Capítulo Real"
    assert len(doc.sections[0].paragraphs) == 3

    # Code block should be a paragraph
    assert "```python" in doc.sections[0].paragraphs[1].text
    assert "# Este es un comentario" in doc.sections[0].paragraphs[1].text


# Ciclo 9: Listas con # no son headings
def test_parse_lists_starting_with_hash():
    """Test that # without space are not headings"""
    content = """# Capítulo

Lista de items:

1. Item 1
2. Item 2
#3 esto podría confundirse
# Pero esto SÍ es un heading"""

    doc = parse_markdown(content)
    assert len(doc.sections) == 2
    assert doc.sections[0].title == "Capítulo"
    assert doc.sections[1].title == "Pero esto SÍ es un heading"

    # #3 should be in content, not a heading
    all_text = "\n".join(p.text for p in doc.sections[0].paragraphs)
    assert "#3 esto podría confundirse" in all_text


# Ciclo 10: document.find_section() - caso exitoso
def test_find_section_by_title_success():
    """Test finding a section by exact title"""
    content = """# Introducción

# Metodología"""

    doc = parse_markdown(content)
    section = doc.find_section("Metodología")

    assert section.title == "Metodología"
    assert section.level == 1


# Ciclo 11: document.find_section() - case-sensitive
def test_find_section_case_sensitive():
    """Test that find_section is case-sensitive"""
    content = "# Metodología"
    doc = parse_markdown(content)

    from doc_handler.domain.exceptions import SectionNotFoundError
    with pytest.raises(SectionNotFoundError) as exc_info:
        doc.find_section("metodología")

    assert exc_info.value.title == "metodología"


# Ciclo 12: document.find_section() - no existe con sugerencias
def test_find_section_not_found_with_suggestions():
    """Test that SectionNotFoundError includes suggestions"""
    content = """# Introducción

# Metodología

# Conclusiones"""

    doc = parse_markdown(content)

    from doc_handler.domain.exceptions import SectionNotFoundError
    with pytest.raises(SectionNotFoundError) as exc_info:
        doc.find_section("Metadología")  # typo

    assert exc_info.value.title == "Metadología"
    assert set(exc_info.value.available) == {"Introducción", "Metodología", "Conclusiones"}


# Ciclo 13: Sección vacía
def test_parse_empty_section():
    """Test parsing empty sections (heading only)"""
    content = """# Sección 1
# Sección 2

Contenido de sección 2."""

    doc = parse_markdown(content)
    assert len(doc.sections) == 2

    assert doc.sections[0].title == "Sección 1"
    assert len(doc.sections[0].paragraphs) == 0

    assert doc.sections[1].title == "Sección 2"
    assert len(doc.sections[1].paragraphs) == 1


# Ciclo 14: Document con metadata
def test_document_preserves_metadata():
    """Test that Document preserves path and raw_content"""
    content = "# Test\n\nContent."
    doc = parse_markdown(content, path=Path("test.md"))

    assert doc.raw_content == content
    assert doc.path == Path("test.md")


# Integration test: Parser with embeddings
@patch("doc_handler.infrastructure.embeddings.requests.post")
@patch("doc_handler.infrastructure.embeddings.JINA_API_KEY", "test_key")
def test_parse_with_embeddings_integration(mock_post):
    """Test parsing with embedding generation"""
    # Mock Jina AI response
    mock_response = {
        "data": [
            {"embedding": [0.1] * 768, "index": 0},
            {"embedding": [0.2] * 768, "index": 1}
        ]
    }
    mock_post.return_value.json.return_value = mock_response
    mock_post.return_value.status_code = 200

    content = """# Capítulo 1

Primer párrafo.

Segundo párrafo."""

    doc = parse_markdown(content, generate_embeddings=True)

    # Verify document structure
    assert len(doc.sections) == 1
    assert len(doc.sections[0].paragraphs) == 2

    # Verify embeddings were generated
    assert doc.sections[0].paragraphs[0].embedding == [0.1] * 768
    assert doc.sections[0].paragraphs[1].embedding == [0.2] * 768

    # Verify batch API call was made
    mock_post.assert_called_once()


def test_parse_without_embeddings():
    """Test that embeddings are None when not requested"""
    content = "# Test\n\nParagraph."
    doc = parse_markdown(content, generate_embeddings=False)

    assert doc.sections[0].paragraphs[0].embedding is None
