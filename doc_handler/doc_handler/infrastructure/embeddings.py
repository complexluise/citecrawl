"""Embedding generation using Jina AI API"""
import os
import requests
from typing import List
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_API_URL = "https://api.jina.ai/v1/embeddings"
MODEL = "jina-embeddings-v3"
TASK = "text-matching"
DIMENSIONS = 768


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text using Jina AI API"""
    if not text.strip():
        return []

    from ..domain.exceptions import EmbeddingAPIError

    if not JINA_API_KEY:
        raise EmbeddingAPIError("JINA_API_KEY not found in environment variables")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }

    payload = {
        "model": MODEL,
        "task": TASK,
        "dimensions": DIMENSIONS,
        "input": [text]
    }

    try:
        response = requests.post(JINA_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data["data"][0]["embedding"]

    except requests.exceptions.Timeout:
        raise EmbeddingAPIError("Jina AI API timeout")
    except requests.exceptions.HTTPError as e:
        raise EmbeddingAPIError(f"Jina AI API error: {e.response.status_code} {e.response.text}")
    except Exception as e:
        raise EmbeddingAPIError(f"Unexpected error: {str(e)}")


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call (batch processing)"""
    if not texts:
        return []

    # Filter out empty texts
    non_empty_texts = [t for t in texts if t.strip()]
    if not non_empty_texts:
        return [[] for _ in texts]

    from ..domain.exceptions import EmbeddingAPIError

    if not JINA_API_KEY:
        raise EmbeddingAPIError("JINA_API_KEY not found in environment variables")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }

    payload = {
        "model": MODEL,
        "task": TASK,
        "dimensions": DIMENSIONS,
        "input": non_empty_texts
    }

    try:
        response = requests.post(JINA_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()
        embeddings = [item["embedding"] for item in data["data"]]

        # Map back to original texts (handle empty texts)
        result = []
        non_empty_idx = 0
        for text in texts:
            if text.strip():
                result.append(embeddings[non_empty_idx])
                non_empty_idx += 1
            else:
                result.append([])

        return result

    except requests.exceptions.Timeout:
        raise EmbeddingAPIError("Jina AI API timeout")
    except requests.exceptions.HTTPError as e:
        raise EmbeddingAPIError(f"Jina AI API error: {e.response.status_code} {e.response.text}")
    except Exception as e:
        raise EmbeddingAPIError(f"Unexpected error: {str(e)}")
