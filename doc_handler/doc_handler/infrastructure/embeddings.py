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
MAX_TOKENS_PER_BATCH = 3000  # Very conservative limit (Jina limit is 8194, but we need margin)


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text.

    Uses approximation based on XLM-RoBERTa tokenizer (used by Jina v3):
    - ~1.5 tokens per word for multilingual text (conservative estimate)
    - Spanish/multilingual text typically uses more tokens than English
    - Adds character-based buffer for safety

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    if not text.strip():
        return 0

    # Conservative estimate: 1.5 tokens per word + character/4 buffer
    # This accounts for multilingual text and special characters
    word_count = len(text.split())
    char_count = len(text)

    # Use the maximum of word-based and character-based estimates for safety
    word_estimate = int(word_count * 1.5)
    char_estimate = int(char_count / 4)  # ~4 chars per token is conservative

    return max(word_estimate, char_estimate)


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
    """Generate embeddings for multiple texts using intelligent batching.

    Splits texts into batches to avoid exceeding Jina AI's token limit (8194 tokens).
    Each batch is kept under MAX_TOKENS_PER_BATCH tokens for safety.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embeddings (same length as input), empty list for empty texts

    Raises:
        EmbeddingAPIError: If API call fails or text exceeds single-request limit
    """
    if not texts:
        return []

    from ..domain.exceptions import EmbeddingAPIError

    if not JINA_API_KEY:
        raise EmbeddingAPIError("JINA_API_KEY not found in environment variables")

    # Create batches based on token estimates
    batches = []
    current_batch = []
    current_tokens = 0

    for i, text in enumerate(texts):
        if not text.strip():
            # Keep empty texts in place
            continue

        estimated_tokens = estimate_tokens(text)

        # Check if single text exceeds limit
        if estimated_tokens > MAX_TOKENS_PER_BATCH:
            print(f"Warning: Text at index {i} (~{estimated_tokens} tokens) may exceed limit. Skipping.")
            continue

        # Start new batch if adding this text would exceed limit
        if current_tokens + estimated_tokens > MAX_TOKENS_PER_BATCH and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append((i, text))
        current_tokens += estimated_tokens

    # Add final batch
    if current_batch:
        batches.append(current_batch)

    # Process each batch
    all_embeddings = {}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }

    for batch_idx, batch in enumerate(batches):
        batch_texts = [text for _, text in batch]
        batch_indices = [idx for idx, _ in batch]

        # Calculate estimated tokens for this batch
        batch_token_estimate = sum(estimate_tokens(text) for text in batch_texts)
        print(f"Processing batch {batch_idx + 1}/{len(batches)}: {len(batch_texts)} texts, ~{batch_token_estimate} estimated tokens")

        payload = {
            "model": MODEL,
            "task": TASK,
            "dimensions": DIMENSIONS,
            "input": batch_texts
        }

        try:
            response = requests.post(JINA_API_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]

            # Store embeddings with original indices
            for idx, embedding in zip(batch_indices, embeddings):
                all_embeddings[idx] = embedding

        except requests.exceptions.Timeout:
            raise EmbeddingAPIError(f"Jina AI API timeout on batch {batch_idx + 1}/{len(batches)}")
        except requests.exceptions.HTTPError as e:
            raise EmbeddingAPIError(f"Jina AI API error on batch {batch_idx + 1}/{len(batches)}: {e.response.status_code} {e.response.text}")
        except Exception as e:
            raise EmbeddingAPIError(f"Unexpected error on batch {batch_idx + 1}/{len(batches)}: {str(e)}")

    # Map back to original order (handle empty texts and skipped texts)
    result = []
    for i, text in enumerate(texts):
        if i in all_embeddings:
            result.append(all_embeddings[i])
        else:
            result.append([])

    return result
