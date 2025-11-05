"""Embedding-based redundancy analyzer using cosine similarity"""
import numpy as np
from doc_handler.domain.models import Section, Document, Redundancy, RedundancyReport, Paragraph


def cosine_similarity(vec1: list[float] | None, vec2: list[float] | None) -> float:
    """Calculate cosine similarity between two embedding vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Cosine similarity score between -1.0 and 1.0
        Returns 0.0 if either vector is None or zero vector
    """
    # Handle None embeddings
    if vec1 is None or vec2 is None:
        return 0.0

    # Convert to numpy arrays
    a = np.array(vec1)
    b = np.array(vec2)

    # Handle zero vectors (avoid division by zero)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    # Calculate cosine similarity
    return float(np.dot(a, b) / (norm_a * norm_b))


class EmbeddingAnalyzer:
    """Analyzes document redundancies using embedding-based cosine similarity."""

    def analyze_section(
        self,
        section: Section,
        threshold: float = 0.7
    ) -> RedundancyReport:
        """Analyze redundancies in a specific section.

        Args:
            section: Section to analyze
            threshold: Minimum similarity score to consider redundant (0.0-1.0)

        Returns:
            RedundancyReport with detected redundancies
        """
        redundancies = []
        paragraphs = section.paragraphs

        # Compare all pairs of paragraphs
        for i in range(len(paragraphs)):
            for j in range(i + 1, len(paragraphs)):
                p1 = paragraphs[i]
                p2 = paragraphs[j]

                # Skip if either paragraph has no embedding
                if p1.embedding is None or p2.embedding is None:
                    continue

                # Calculate similarity
                similarity = cosine_similarity(p1.embedding, p2.embedding)

                # Check if exceeds threshold
                if similarity >= threshold:
                    redundancies.append(Redundancy(
                        paragraph1=p1,
                        paragraph2=p2,
                        similarity_score=similarity
                    ))

        return RedundancyReport(
            section_title=section.title,
            total_paragraphs=len(paragraphs),
            redundancies=redundancies,
            threshold=threshold
        )

    def analyze_document(
        self,
        document: Document,
        threshold: float = 0.7
    ) -> RedundancyReport:
        """Analyze redundancies across entire document.

        Args:
            document: Document to analyze
            threshold: Minimum similarity score to consider redundant (0.0-1.0)

        Returns:
            RedundancyReport with detected redundancies across all sections
        """
        # Collect all paragraphs from all sections recursively
        all_paragraphs = []

        def collect_paragraphs(sections: list[Section]):
            for section in sections:
                all_paragraphs.extend(section.paragraphs)
                if section.subsections:
                    collect_paragraphs(section.subsections)

        collect_paragraphs(document.sections)

        # Compare all pairs of paragraphs
        redundancies = []
        for i in range(len(all_paragraphs)):
            for j in range(i + 1, len(all_paragraphs)):
                p1 = all_paragraphs[i]
                p2 = all_paragraphs[j]

                # Skip if either paragraph has no embedding
                if p1.embedding is None or p2.embedding is None:
                    continue

                # Calculate similarity
                similarity = cosine_similarity(p1.embedding, p2.embedding)

                # Check if exceeds threshold
                if similarity >= threshold:
                    redundancies.append(Redundancy(
                        paragraph1=p1,
                        paragraph2=p2,
                        similarity_score=similarity
                    ))

        return RedundancyReport(
            section_title=None,  # Global analysis
            total_paragraphs=len(all_paragraphs),
            redundancies=redundancies,
            threshold=threshold
        )
