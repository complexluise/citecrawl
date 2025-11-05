"""Tests for embedding-based redundancy analyzer"""
import pytest
import numpy as np
from doc_handler.domain.models import Paragraph, Section, Document


def test_cosine_similarity_calculation():
    """Test basic cosine similarity calculation"""
    from doc_handler.infrastructure.embedding_analyzer import cosine_similarity

    # Identical vectors
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec1, vec2) == pytest.approx(1.0)

    # Perpendicular vectors
    vec3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(vec1, vec3) == pytest.approx(0.0)

    # Partially similar vectors
    vec4 = [0.5, 0.5, 0.0]
    sim = cosine_similarity(vec1, vec4)
    assert 0.5 < sim < 1.0


def test_cosine_similarity_with_none_embeddings():
    """Test cosine similarity handles None embeddings gracefully"""
    from doc_handler.infrastructure.embedding_analyzer import cosine_similarity

    vec = [0.1] * 768

    # None in first position
    assert cosine_similarity(None, vec) == 0.0

    # None in second position
    assert cosine_similarity(vec, None) == 0.0

    # Both None
    assert cosine_similarity(None, None) == 0.0


def test_cosine_similarity_opposite_vectors():
    """Test cosine similarity with opposite vectors"""
    from doc_handler.infrastructure.embedding_analyzer import cosine_similarity

    vec1 = [1.0, 0.0, 0.0]
    vec2 = [-1.0, 0.0, 0.0]  # Opposite direction

    # Opposite vectors should have similarity close to -1
    assert cosine_similarity(vec1, vec2) == pytest.approx(-1.0)


def test_cosine_similarity_with_zero_vectors():
    """Test cosine similarity with zero vectors"""
    from doc_handler.infrastructure.embedding_analyzer import cosine_similarity

    vec1 = [1.0, 2.0, 3.0]
    vec_zero = [0.0, 0.0, 0.0]

    # Zero vector should return 0.0 (avoid division by zero)
    assert cosine_similarity(vec1, vec_zero) == 0.0
    assert cosine_similarity(vec_zero, vec1) == 0.0
    assert cosine_similarity(vec_zero, vec_zero) == 0.0


# Sprint 2: Section Analysis Tests


def test_analyze_section_no_redundancies():
    """Test analyzer with section containing no redundancies"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    # Create section with dissimilar paragraphs
    section = Section(
        level=1,
        title="Introducción",
        paragraphs=[
            Paragraph(
                text="AI in education",
                index=0,
                line_number=1,
                embedding=[1.0, 0.0, 0.0]
            ),
            Paragraph(
                text="Relational databases",
                index=1,
                line_number=3,
                embedding=[0.0, 1.0, 0.0]
            ),
            Paragraph(
                text="Neural networks",
                index=2,
                line_number=5,
                embedding=[0.0, 0.0, 1.0]
            ),
        ],
        subsections=[],
        start_line=1,
        end_line=6
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_section(section, threshold=0.7)

    assert report.section_title == "Introducción"
    assert report.total_paragraphs == 3
    assert report.has_redundancies is False
    assert report.redundancy_count == 0
    assert report.redundancies == []


def test_analyze_section_with_redundancies():
    """Test analyzer detects redundancies above threshold"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    # Create vectors that are very similar (cosine similarity ≈ 0.87)
    vec1 = np.array([1.0, 0.5, 0.2])
    vec1 = vec1 / np.linalg.norm(vec1)
    vec2 = np.array([0.9, 0.55, 0.25])
    vec2 = vec2 / np.linalg.norm(vec2)
    vec3 = np.array([0.0, 0.0, 1.0])  # Very different

    section = Section(
        level=1,
        title="Metodología",
        paragraphs=[
            Paragraph(
                text="El enfoque cualitativo permite explorar experiencias.",
                index=0,
                line_number=1,
                embedding=vec1.tolist()
            ),
            Paragraph(
                text="La metodología cualitativa facilita la exploración.",
                index=1,
                line_number=3,
                embedding=vec2.tolist()
            ),
            Paragraph(
                text="Completely different content about databases.",
                index=2,
                line_number=5,
                embedding=vec3.tolist()
            ),
        ],
        subsections=[],
        start_line=1,
        end_line=6
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_section(section, threshold=0.7)

    assert report.has_redundancies is True
    assert report.redundancy_count == 1
    assert report.redundancies[0].paragraph1.index == 0
    assert report.redundancies[0].paragraph2.index == 1
    assert report.redundancies[0].similarity_score >= 0.7


def test_analyze_section_custom_threshold():
    """Test analyzer respects custom threshold"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    # Create vectors with similarity around 0.85 (but not too high)
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.85, 0.53, 0.0])  # Roughly 85% similar to vec1
    vec2 = vec2 / np.linalg.norm(vec2)

    section = Section(
        level=1,
        title="Test",
        paragraphs=[
            Paragraph(text="P1", index=0, line_number=1, embedding=vec1.tolist()),
            Paragraph(text="P2", index=1, line_number=2, embedding=vec2.tolist()),
        ],
        subsections=[],
        start_line=1,
        end_line=3
    )

    analyzer = EmbeddingAnalyzer()

    # With threshold 0.7, should detect redundancy
    report1 = analyzer.analyze_section(section, threshold=0.7)
    assert report1.has_redundancies is True

    # With threshold 0.95, should NOT detect redundancy
    report2 = analyzer.analyze_section(section, threshold=0.95)
    assert report2.has_redundancies is False


def test_analyze_section_multiple_redundancies():
    """Test analyzer detects multiple redundant pairs"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    # Create two pairs of similar paragraphs
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.95, 0.1, 0.0])
    vec2 = vec2 / np.linalg.norm(vec2)
    vec3 = np.array([0.0, 1.0, 0.0])
    vec4 = np.array([0.1, 0.95, 0.0])
    vec4 = vec4 / np.linalg.norm(vec4)

    section = Section(
        level=1,
        title="Resultados",
        paragraphs=[
            Paragraph(text="P1", index=0, line_number=1, embedding=vec1.tolist()),
            Paragraph(text="P2", index=1, line_number=2, embedding=vec2.tolist()),
            Paragraph(text="P3", index=2, line_number=3, embedding=vec3.tolist()),
            Paragraph(text="P4", index=3, line_number=4, embedding=vec4.tolist()),
        ],
        subsections=[],
        start_line=1,
        end_line=5
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_section(section, threshold=0.7)

    assert report.redundancy_count == 2
    # Check that we found the right pairs
    pair_indices = [(r.paragraph1.index, r.paragraph2.index) for r in report.redundancies]
    assert (0, 1) in pair_indices
    assert (2, 3) in pair_indices


def test_analyze_empty_section():
    """Test analyzer handles empty sections"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    section = Section(
        level=1,
        title="Empty Section",
        paragraphs=[],
        subsections=[],
        start_line=1,
        end_line=1
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_section(section, threshold=0.7)

    assert report.total_paragraphs == 0
    assert report.has_redundancies is False
    assert report.redundancy_count == 0


def test_analyze_section_with_missing_embeddings():
    """Test analyzer ignores paragraphs without embeddings"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    section = Section(
        level=1,
        title="Test",
        paragraphs=[
            Paragraph(text="P1", index=0, line_number=1, embedding=[1.0, 0.0, 0.0]),
            Paragraph(text="P2", index=1, line_number=2, embedding=None),  # No embedding
            Paragraph(text="P3", index=2, line_number=3, embedding=[1.0, 0.0, 0.0]),
        ],
        subsections=[],
        start_line=1,
        end_line=4
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_section(section, threshold=0.7)

    # Should still work, comparing P1 and P3 (identical vectors = redundant)
    assert report.total_paragraphs == 3
    # P1 and P3 are identical, so should be detected as redundant
    assert report.has_redundancies is True
    assert report.redundancy_count == 1


# Sprint 3: Document Analysis Tests


def test_analyze_document_no_redundancies():
    """Test document analysis with no redundancies"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    doc = Document(
        raw_content="test",
        sections=[
            Section(
                level=1,
                title="Capítulo 1",
                paragraphs=[
                    Paragraph(text="AI in education", index=0, line_number=1, embedding=[1.0, 0.0, 0.0])
                ],
                subsections=[
                    Section(
                        level=2,
                        title="Sección 1.1",
                        paragraphs=[
                            Paragraph(text="Teacher evaluation", index=0, line_number=3, embedding=[0.0, 1.0, 0.0])
                        ],
                        subsections=[],
                        start_line=3,
                        end_line=4
                    )
                ],
                start_line=1,
                end_line=4
            ),
            Section(
                level=1,
                title="Capítulo 2",
                paragraphs=[
                    Paragraph(text="NoSQL databases", index=0, line_number=6, embedding=[0.0, 0.0, 1.0])
                ],
                subsections=[],
                start_line=6,
                end_line=7
            )
        ]
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_document(doc, threshold=0.7)

    assert report.section_title is None  # Global analysis
    assert report.total_paragraphs == 3
    assert report.has_redundancies is False


def test_analyze_document_cross_section_redundancies():
    """Test document analysis detects cross-section redundancies"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    # Create similar embeddings for cross-section redundancy
    vec1 = np.array([1.0, 0.1, 0.0])
    vec1 = vec1 / np.linalg.norm(vec1)
    vec2 = np.array([0.95, 0.15, 0.0])
    vec2 = vec2 / np.linalg.norm(vec2)

    doc = Document(
        raw_content="test",
        sections=[
            Section(
                level=1,
                title="Introducción",
                paragraphs=[
                    Paragraph(
                        text="Machine learning allows training predictive models.",
                        index=0,
                        line_number=1,
                        embedding=vec1.tolist()
                    )
                ],
                subsections=[],
                start_line=1,
                end_line=2
            ),
            Section(
                level=1,
                title="Metodología",
                paragraphs=[
                    Paragraph(
                        text="Predictive models are trained using ML.",
                        index=0,
                        line_number=4,
                        embedding=vec2.tolist()
                    )
                ],
                subsections=[],
                start_line=4,
                end_line=5
            ),
            Section(
                level=1,
                title="Conclusiones",
                paragraphs=[
                    Paragraph(
                        text="Completely different content about ethics.",
                        index=0,
                        line_number=7,
                        embedding=[0.0, 0.0, 1.0]
                    )
                ],
                subsections=[],
                start_line=7,
                end_line=8
            )
        ]
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_document(doc, threshold=0.7)

    assert report.has_redundancies is True
    assert report.redundancy_count == 1
    # Verify cross-section detection
    assert "Machine learning" in report.redundancies[0].paragraph1.text
    assert "Predictive models" in report.redundancies[0].paragraph2.text


def test_analyze_document_multiple_redundancies():
    """Test document analysis with multiple redundancies"""
    from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = vec1.copy()  # Identical
    vec3 = np.array([0.0, 1.0, 0.0])
    vec4 = vec3.copy()  # Identical

    doc = Document(
        raw_content="test",
        sections=[
            Section(
                level=1,
                title="Chapter 1",
                paragraphs=[
                    Paragraph(text="P1", index=0, line_number=1, embedding=vec1.tolist()),
                    Paragraph(text="P2", index=1, line_number=2, embedding=vec2.tolist()),
                ],
                subsections=[],
                start_line=1,
                end_line=3
            ),
            Section(
                level=1,
                title="Chapter 2",
                paragraphs=[
                    Paragraph(text="P3", index=0, line_number=4, embedding=vec3.tolist()),
                    Paragraph(text="P4", index=1, line_number=5, embedding=vec4.tolist()),
                ],
                subsections=[],
                start_line=4,
                end_line=6
            )
        ]
    )

    analyzer = EmbeddingAnalyzer()
    report = analyzer.analyze_document(doc, threshold=0.7)

    # Should find 2 redundant pairs
    assert report.redundancy_count == 2
