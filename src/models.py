from pydantic import BaseModel, Field
from typing import Dict, Any

class ScrapedData(BaseModel):
    """
    Represents the data scraped from a single URL using Pydantic for validation.
    """
    url: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
