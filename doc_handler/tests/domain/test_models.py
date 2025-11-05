"""Tests for domain models"""
from pathlib import Path
from doc_handler.domain.models import Paragraph, Section, Document
from doc_handler.domain.exceptions import SectionNotFoundError
import pytest


def test_paragraph_model():
    """Test Paragraph model validates correctly"""
    p = Paragraph(text="Hello", index=0, line_number=1, embedding=[0.1, 0.2])
    assert p.text == "Hello"
    assert p.embedding == [0.1, 0.2]


def test_paragraph_without_embedding():
    """Test Paragraph works without embedding"""
    p = Paragraph(text="Hello", index=0, line_number=1)
    assert p.embedding is None


def test_section_model():
    """Test Section model validates correctly"""
    s = Section(level=1, title="Test", start_line=1, end_line=1)
    assert s.level == 1
    assert s.paragraphs == []
    assert s.subsections == []


def test_section_content_property():
    """Test Section.content reconstructs from paragraphs"""
    s = Section(
        level=1,
        title="Test",
        paragraphs=[
            Paragraph(text="Para 1", index=0, line_number=1),
            Paragraph(text="Para 2", index=1, line_number=3),
        ],
        start_line=1,
        end_line=3,
    )
    assert s.content == "Para 1\n\nPara 2"


def test_document_model():
    """Test Document model validates correctly"""
    doc = Document(raw_content="# Test", path=Path("test.md"))
    assert doc.raw_content == "# Test"
    assert doc.path == Path("test.md")
    assert doc.sections == []
