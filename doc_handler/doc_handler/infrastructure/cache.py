"""Automatic caching for parsed documents with embeddings."""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional

from doc_handler.domain.models import Document


class DocumentCache:
    """Handles caching of parsed Document objects to speed up subsequent analyses."""

    def __init__(self, cache_dir: Path = Path(".doc_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, file_path: Path) -> Path:
        """Generate a unique cache path for a given file path."""
        # Create a unique filename to avoid collisions
        filename = f"{file_path.stem}_{hashlib.sha256(str(file_path).encode()).hexdigest()[:8]}.doccache"
        return self.cache_dir / filename

    def get(self, file_path: Path) -> Optional[Document]:
        """Retrieve a cached Document if it's valid."""
        cache_path = self._get_cache_path(file_path)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate cache
            original_mtime = file_path.stat().st_mtime
            if data.get("source_mtime") != original_mtime:
                return None  # Stale cache

            # Reconstruct Document object
            return Document.model_validate(data["document"])

        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # Corrupt or invalid cache, treat as miss
            return None

    def set(self, file_path: Path, document: Document):
        """Save a Document object to the cache."""
        cache_path = self._get_cache_path(file_path)

        try:
            # Get metadata from the source file
            source_mtime = file_path.stat().st_mtime

            # Prepare data for serialization
            data = {
                "source_path": str(file_path),
                "source_mtime": source_mtime,
                "cached_at": time.time(),
                "document": json.loads(document.model_dump_json()),  # Serialize Pydantic model
            }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        except (IOError, FileNotFoundError):
            # Fail silently if cache writing fails
            pass

    def clear(self, file_path: Path):
        """Remove the cache file for a specific document."""
        cache_path = self._get_cache_path(file_path)
        if cache_path.exists():
            cache_path.unlink()

    def clear_all(self):
        """Remove all cache files from the cache directory."""
        for cache_file in self.cache_dir.glob("*.doccache"):
            cache_file.unlink()
