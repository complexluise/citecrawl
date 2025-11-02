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
