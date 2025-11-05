"""Tests for domain models"""
from pathlib import Path
from doc_handler.domain.models import Paragraph, Section, Document, Redundancy, RedundancyReport
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


def test_redundancy_model():
    """Test Redundancy model validates correctly"""
    p1 = Paragraph(
        text="El aprendizaje automático permite entrenar modelos.",
        index=0,
        line_number=5,
        embedding=[0.1] * 768
    )
    p2 = Paragraph(
        text="Los modelos se entrenan usando machine learning.",
        index=1,
        line_number=7,
        embedding=[0.15] * 768
    )

    redundancy = Redundancy(
        paragraph1=p1,
        paragraph2=p2,
        similarity_score=0.87
    )

    assert redundancy.paragraph1 == p1
    assert redundancy.paragraph2 == p2
    assert redundancy.similarity_score == 0.87
    assert redundancy.similarity_percentage == 87


def test_redundancy_report_model():
    """Test RedundancyReport model validates correctly"""
    p1 = Paragraph(text="Test 1", index=0, line_number=1, embedding=[0.1] * 768)
    p2 = Paragraph(text="Test 2", index=1, line_number=2, embedding=[0.2] * 768)
    p3 = Paragraph(text="Test 3", index=2, line_number=3, embedding=[0.3] * 768)
    p4 = Paragraph(text="Test 4", index=3, line_number=4, embedding=[0.4] * 768)

    redundancy1 = Redundancy(paragraph1=p1, paragraph2=p2, similarity_score=0.85)
    redundancy2 = Redundancy(paragraph1=p3, paragraph2=p4, similarity_score=0.72)

    report = RedundancyReport(
        section_title="Introducción",
        total_paragraphs=10,
        redundancies=[redundancy1, redundancy2],
        threshold=0.7
    )

    assert report.section_title == "Introducción"
    assert report.total_paragraphs == 10
    assert report.redundancy_count == 2
    assert report.has_redundancies is True
    assert report.threshold == 0.7


def test_redundancy_report_no_redundancies():
    """Test RedundancyReport with no redundancies"""
    report = RedundancyReport(
        section_title="Test",
        total_paragraphs=5,
        redundancies=[],
        threshold=0.7
    )

    assert report.has_redundancies is False
    assert report.redundancy_count == 0
