"""Domain models for Markdown documents"""
from pathlib import Path
from pydantic import BaseModel, Field


class Paragraph(BaseModel):
    """A paragraph in a section.

    Attributes:
        text: The paragraph content
        index: Position within the section (0-indexed)
        line_number: Line number where paragraph starts in source file
        embedding: Optional 768-dimensional vector from Jina AI for semantic similarity
    """
    text: str
    index: int
    line_number: int
    embedding: list[float] | None = None


class Section(BaseModel):
    """A section in a Markdown document with hierarchical structure.

    Attributes:
        level: Heading level (1-6, where 1 is #, 2 is ##, etc.)
        title: Section heading text
        paragraphs: Content paragraphs directly under this heading
        subsections: Nested sections with higher level numbers
        start_line: Line number where section starts
        end_line: Line number where section ends
    """
    level: int = Field(ge=1, le=6)
    title: str
    paragraphs: list[Paragraph] = Field(default_factory=list)
    subsections: list["Section"] = Field(default_factory=list)
    start_line: int
    end_line: int

    @property
    def content(self) -> str:
        """Reconstruct text content from paragraphs, joined by blank lines."""
        return "\n\n".join(p.text for p in self.paragraphs)


class Document(BaseModel):
    """A parsed Markdown document with hierarchical sections.

    Attributes:
        path: Optional file path of the source document
        sections: Top-level sections (level 1 headings)
        raw_content: Original Markdown text
    """
    path: Path | None = None
    sections: list[Section] = Field(default_factory=list)
    raw_content: str

    def find_section(self, title: str) -> Section:
        """Find a section by exact title (case-sensitive).

        Args:
            title: Exact section title to search for

        Returns:
            Section with matching title

        Raises:
            SectionNotFoundError: If no section matches, includes available titles
        """
        def search(sections: list[Section]) -> Section | None:
            for section in sections:
                if section.title == title:
                    return section
                if section.subsections:
                    result = search(section.subsections)
                    if result:
                        return result
            return None

        result = search(self.sections)
        if result is None:
            from .exceptions import SectionNotFoundError
            available = self._get_all_titles()
            raise SectionNotFoundError(title=title, available=available)
        return result

    def _get_all_titles(self) -> list[str]:
        """Get all section titles recursively"""
        titles = []
        def collect(sections: list[Section]):
            for section in sections:
                titles.append(section.title)
                if section.subsections:
                    collect(section.subsections)
        collect(self.sections)
        return titles


class Redundancy(BaseModel):
    """Represents a pair of redundant paragraphs.

    Attributes:
        paragraph1: First paragraph in the redundant pair
        paragraph2: Second paragraph in the redundant pair
        similarity_score: Cosine similarity score (0.0 - 1.0)
    """
    paragraph1: Paragraph
    paragraph2: Paragraph
    similarity_score: float = Field(ge=0.0, le=1.0)

    @property
    def similarity_percentage(self) -> int:
        """Returns similarity as percentage (0-100)."""
        return round(self.similarity_score * 100)


class RedundancyReport(BaseModel):
    """Report of redundancy analysis results.

    Attributes:
        section_title: Title of analyzed section (None for full document)
        total_paragraphs: Total number of paragraphs analyzed
        redundancies: List of detected redundant paragraph pairs
        threshold: Similarity threshold used for detection (default 0.7)
    """
    section_title: str | None
    total_paragraphs: int
    redundancies: list[Redundancy] = Field(default_factory=list)
    threshold: float = 0.7

    @property
    def has_redundancies(self) -> bool:
        """Returns True if any redundancies were found."""
        return len(self.redundancies) > 0

    @property
    def redundancy_count(self) -> int:
        """Returns the number of redundant pairs found."""
        return len(self.redundancies)
