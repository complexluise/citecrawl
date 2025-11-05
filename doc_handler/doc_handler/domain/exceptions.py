"""Domain exceptions"""


class SectionNotFoundError(Exception):
    """Raised when a section is not found in the document"""

    def __init__(self, title: str, available: list[str]):
        self.title = title
        self.available = available
        super().__init__(
            f"Section '{title}' not found. Available sections: {', '.join(available)}"
        )


class EmbeddingAPIError(Exception):
    """Raised when Jina AI API fails"""
    pass
