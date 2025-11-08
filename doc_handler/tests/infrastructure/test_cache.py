"""Tests for the document cache."""
import time
from pathlib import Path

import pytest
from doc_handler.domain.models import Document, Section, Paragraph
from doc_handler.infrastructure.cache import DocumentCache


@pytest.fixture
def cache(tmp_path):
    """Provides a DocumentCache instance with a temporary cache directory."""
    cache_dir = tmp_path / ".doc_cache"
    return DocumentCache(cache_dir=cache_dir)


@pytest.fixture
def temp_file(tmp_path):
    """Creates a temporary file to be cached."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Hello, world!", encoding="utf-8")
    return file_path


@pytest.fixture
def sample_document(temp_file):
    """Creates a sample Document object for caching."""
    p = Paragraph(text="A paragraph", index=0, line_number=1, embedding=[0.1, 0.2])
    s = Section(title="Title", level=1, paragraphs=[p], subsections=[], start_line=1, end_line=1)
    return Document(path=temp_file, sections=[s], raw_content="# Title\nA paragraph")

def test_cache_get_miss(cache, temp_file):
    """Test that cache returns None for a file that is not cached."""
    assert cache.get(temp_file) is None

def test_cache_set_and_get_hit(cache, temp_file, sample_document):
    """Test that a document can be cached and retrieved successfully."""
    # Set the document in the cache
    cache.set(temp_file, sample_document)

    # Get the document from the cache
    cached_doc = cache.get(temp_file)

    assert cached_doc is not None
    assert cached_doc.path == sample_document.path
    assert cached_doc.sections[0].title == "Title"
    assert cached_doc.sections[0].paragraphs[0].embedding == [0.1, 0.2]

def test_cache_invalidation_on_modification(cache, temp_file, sample_document):
    """Test that the cache is invalidated if the source file is modified."""
    cache.set(temp_file, sample_document)

    # Ensure we can get it first
    assert cache.get(temp_file) is not None

    # Modify the file (sleep to ensure mtime changes)
    time.sleep(0.1)
    temp_file.write_text("New content", encoding="utf-8")

    # Now, get should return None
    assert cache.get(temp_file) is None

def test_cache_clear(cache, temp_file, sample_document):
    """Test that the cache for a specific file can be cleared."""
    cache.set(temp_file, sample_document)
    assert cache.get(temp_file) is not None

    cache.clear(temp_file)
    assert cache.get(temp_file) is None

def test_cache_clear_all(cache, tmp_path, sample_document):
    """Test that all cache files can be cleared."""
    # Create two files and cache them
    file1 = tmp_path / "file1.md"
    file2 = tmp_path / "file2.md"
    file1.write_text("content1")
    file2.write_text("content2")

    doc1 = Document(path=file1, sections=[], raw_content="content1")
    doc2 = Document(path=file2, sections=[], raw_content="content2")

    cache.set(file1, doc1)
    cache.set(file2, doc2)

    assert cache.get(file1) is not None
    assert cache.get(file2) is not None

    cache.clear_all()

    assert cache.get(file1) is None
    assert cache.get(file2) is None
    assert not any(cache.cache_dir.iterdir())

def test_cache_corrupted_file(cache, temp_file, sample_document):
    """Test that a corrupted cache file is handled gracefully (returns None)."""
    cache.set(temp_file, sample_document)

    # Corrupt the cache file
    cache_path = cache._get_cache_path(temp_file)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write("this is not valid json")

    assert cache.get(temp_file) is None
