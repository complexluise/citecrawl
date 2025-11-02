from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ScrapedData(BaseModel):
    """
    Represents the data scraped from a single URL using Pydantic for validation.
    """
    url: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Bibliography(BaseModel):
    """
    Represents the extracted bibliographic metadata.
    """
    title: str = ""
    author: str = ""
    year: Optional[int] = None

class EnrichedData(BaseModel):
    """
    Represents the data after enrichment by the AI.
    """
    summary: str
    bibliography: Bibliography

class Publication(BaseModel):
    """
    Represents a single citable publication with its metadata.
    """
    title: str
    author: Optional[str] = None
    year: Optional[int] = None
    url: str

    def generate_bibtex_entry(self) -> str:
        """
        Generates a BibTeX entry string for the publication.
        """
        # Create a simple citation key from author, year, and title
        author_last_name = self.author.split()[-1] if self.author else "Unknown"
        year_str = str(self.year) if self.year else "ND"
        title_first_word = self.title.split()[0] if self.title else "NoTitle"
        citation_key = f"{author_last_name}{year_str}{title_first_word}"

        # Build the BibTeX entry using fixed-width formatting for alignment
        bibtex_entry = f"@misc{{{citation_key},\n"
        if self.title:
            bibtex_entry += f"  {'title':<10} = {{{self.title}}},\n"
        if self.author:
            bibtex_entry += f"  {'author':<10} = {{{self.author}}},\n"
        if self.year:
            bibtex_entry += f"  {'year':<10} = {{{self.year}}},\n"
        if self.url:
            bibtex_entry += f"  {'howpublished':<10} = {{online}},\n"
            bibtex_entry += f"  {'url':<10} = {{{self.url}}}\n"
        bibtex_entry += "}}\n"
        return bibtex_entry
