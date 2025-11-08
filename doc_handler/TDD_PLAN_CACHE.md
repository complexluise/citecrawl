# TDD Plan: Document Caching System

**Feature**: Automatic caching of parsed documents with embeddings to avoid repeated API calls

**User Story**: As a user analyzing large documents, I want the tool to cache parsed documents so I don't wait for embeddings generation on every run.

**Approach**: Option 4 (Automatic) + Option 2 (JSON sidecar files)

---

## Architecture Decision

### Cache Location
- **Format**: JSON sidecar files
- **Naming**: `{filename}.doccache` (e.g., `documento.md.doccache`)
- **Location**: Same directory as source file
- **Serialization**: Pydantic models → JSON (built-in `.model_dump()`)

### Cache Validation
```python
def is_cache_valid(source_path: Path, cache_path: Path) -> bool:
    """Cache is valid if:
    1. Cache file exists
    2. Source file hasn't been modified (mtime check)
    3. Content hash matches (SHA256)
    """
```

### Module Structure
```
infrastructure/
├── cache.py              # NEW: Cache manager
│   ├── CacheManager
│   │   ├── get_cached_document()
│   │   ├── save_document_cache()
│   │   ├── is_cache_valid()
│   │   └── clear_cache()
│   └── CacheMetadata (Pydantic model)
```

---

## Sprint 1: Core Cache Functionality (5 cycles)

### Cycle 1: Cache metadata model
**Test**: `test_cache_metadata_model`
```python
def test_cache_metadata_model():
    """Cache metadata includes version, file info, and hash"""
    metadata = CacheMetadata(
        version="0.1",
        source_file="test.md",
        file_hash="abc123",
        last_modified="2025-11-05T16:30:00Z"
    )
    assert metadata.version == "0.1"
    assert metadata.source_file == "test.md"
```

**Implementation**: Create `CacheMetadata` Pydantic model in `infrastructure/cache.py`

---

### Cycle 2: Compute file hash
**Test**: `test_compute_file_hash`
```python
def test_compute_file_hash(tmp_path):
    """Compute SHA256 hash of file content"""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Test\n\nContent here.", encoding='utf-8')

    hash1 = compute_file_hash(file_path)
    assert len(hash1) == 64  # SHA256 hex digest

    # Same content = same hash
    hash2 = compute_file_hash(file_path)
    assert hash1 == hash2

    # Different content = different hash
    file_path.write_text("# Modified", encoding='utf-8')
    hash3 = compute_file_hash(file_path)
    assert hash1 != hash3
```

**Implementation**: `compute_file_hash()` function using `hashlib.sha256()`

---

### Cycle 3: Save document to cache
**Test**: `test_save_document_cache`
```python
def test_save_document_cache(tmp_path):
    """Save parsed document to JSON cache file"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    # Create document with embeddings
    doc = Document(
        path=doc_path,
        sections=[
            Section(
                level=1,
                title="Test",
                paragraphs=[
                    Paragraph(text="Paragraph.", index=0, line_number=3, embedding=[0.1, 0.2])
                ]
            )
        ]
    )

    cache_manager = CacheManager()
    cache_manager.save_document_cache(doc_path, doc)

    # Verify cache file exists
    cache_path = tmp_path / "test.md.doccache"
    assert cache_path.exists()

    # Verify JSON structure
    cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
    assert cache_data["version"] == "0.1"
    assert cache_data["source_file"] == "test.md"
    assert "file_hash" in cache_data
    assert "document" in cache_data
    assert cache_data["document"]["sections"][0]["title"] == "Test"
```

**Implementation**: `CacheManager.save_document_cache()` method

---

### Cycle 4: Load document from cache
**Test**: `test_load_document_from_cache`
```python
def test_load_document_from_cache(tmp_path):
    """Load cached document and reconstruct Document model"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    # Create and save cache
    original_doc = Document(
        path=doc_path,
        sections=[
            Section(
                level=1,
                title="Test",
                paragraphs=[
                    Paragraph(text="Paragraph.", index=0, line_number=3, embedding=[0.1, 0.2])
                ]
            )
        ]
    )

    cache_manager = CacheManager()
    cache_manager.save_document_cache(doc_path, original_doc)

    # Load from cache
    loaded_doc = cache_manager.get_cached_document(doc_path)

    assert loaded_doc is not None
    assert loaded_doc.path == doc_path
    assert len(loaded_doc.sections) == 1
    assert loaded_doc.sections[0].title == "Test"
    assert loaded_doc.sections[0].paragraphs[0].embedding == [0.1, 0.2]
```

**Implementation**: `CacheManager.get_cached_document()` method with Pydantic deserialization

---

### Cycle 5: Cache validation (file modified)
**Test**: `test_cache_invalid_when_file_modified`
```python
def test_cache_invalid_when_file_modified(tmp_path):
    """Cache becomes invalid when source file is modified"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Original", encoding='utf-8')

    doc = Document(path=doc_path, sections=[])
    cache_manager = CacheManager()
    cache_manager.save_document_cache(doc_path, doc)

    # Cache is initially valid
    assert cache_manager.is_cache_valid(doc_path) is True

    # Modify source file
    time.sleep(0.1)  # Ensure different mtime
    doc_path.write_text("# Modified", encoding='utf-8')

    # Cache is now invalid
    assert cache_manager.is_cache_valid(doc_path) is False
```

**Implementation**: `CacheManager.is_cache_valid()` with hash comparison

---

## Sprint 2: CLI Integration (4 cycles)

### Cycle 6: Auto-cache in parse_markdown
**Test**: `test_parse_markdown_uses_cache_if_valid`
```python
def test_parse_markdown_uses_cache_if_valid(tmp_path, mocker):
    """parse_markdown() automatically uses cache if valid"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    # First call: generates embeddings
    mock_embeddings = mocker.patch('doc_handler.infrastructure.embeddings.generate_embeddings_batch')
    mock_embeddings.return_value = [[0.1, 0.2]]

    doc1 = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    assert mock_embeddings.call_count == 1  # Called for first parse

    # Second call: uses cache, NO API call
    doc2 = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    assert mock_embeddings.call_count == 1  # Still 1 - cache was used!

    # Documents are equivalent
    assert doc1.sections[0].title == doc2.sections[0].title
    assert doc1.sections[0].paragraphs[0].embedding == doc2.sections[0].paragraphs[0].embedding
```

**Implementation**: Modify `parse_markdown()` to check cache before generating embeddings

---

### Cycle 7: Force reparse with --reparse flag
**Test**: `test_reparse_flag_ignores_cache`
```python
def test_reparse_flag_ignores_cache(tmp_path, mocker):
    """--reparse flag forces regeneration even with valid cache"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    mock_embeddings = mocker.patch('doc_handler.infrastructure.embeddings.generate_embeddings_batch')
    mock_embeddings.return_value = [[0.1, 0.2]]

    # First parse creates cache
    doc1 = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    assert mock_embeddings.call_count == 1

    # Parse with force_reparse=True ignores cache
    doc2 = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True, force_reparse=True)
    assert mock_embeddings.call_count == 2  # API called again
```

**Implementation**: Add `force_reparse` parameter to `parse_markdown()`

---

### Cycle 8: Add --reparse option to commands
**Test**: `test_cli_reparse_option`
```python
def test_cli_reparse_option(tmp_path):
    """CLI commands accept --reparse flag"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph 1.\n\nParagraph 2.", encoding='utf-8')

    runner = CliRunner()

    # First run creates cache
    result1 = runner.invoke(cli, ['check-redundancy-section', str(doc_path), 'Test'])
    assert result1.exit_code == 0

    cache_path = doc_path.with_suffix('.md.doccache')
    assert cache_path.exists()
    original_cache_mtime = cache_path.stat().st_mtime

    time.sleep(0.1)

    # Run with --reparse creates NEW cache
    result2 = runner.invoke(cli, ['check-redundancy-section', str(doc_path), 'Test', '--reparse'])
    assert result2.exit_code == 0
    assert cache_path.stat().st_mtime > original_cache_mtime  # Cache was regenerated
```

**Implementation**: Add `--reparse` option to all analysis commands

---

### Cycle 9: Cache status messages
**Test**: `test_cache_status_messages`
```python
def test_cache_status_messages(tmp_path, capsys):
    """Show clear messages about cache usage"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    # First parse shows "Generating embeddings"
    parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    output1 = capsys.readouterr().out
    assert "Generating embeddings" in output1 or "Processing batch" in output1

    # Second parse shows "Using cached analysis"
    parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    output2 = capsys.readouterr().out
    assert "Using cached analysis" in output2 or "cache" in output2.lower()
```

**Implementation**: Add console output when using/creating cache

---

## Sprint 3: Cache Management Commands (2 cycles)

### Cycle 10: cache-clear command
**Test**: `test_cache_clear_command`
```python
def test_cache_clear_command(tmp_path):
    """Clear cache file for a document"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test", encoding='utf-8')
    cache_path = doc_path.with_suffix('.md.doccache')

    # Create cache
    doc = Document(path=doc_path, sections=[])
    cache_manager = CacheManager()
    cache_manager.save_document_cache(doc_path, doc)
    assert cache_path.exists()

    # Clear cache
    runner = CliRunner()
    result = runner.invoke(cli, ['cache-clear', str(doc_path)])
    assert result.exit_code == 0
    assert not cache_path.exists()
    assert "Cache cleared" in result.output
```

**Implementation**: Add `cache-clear` CLI command

---

### Cycle 11: cache-info command
**Test**: `test_cache_info_command`
```python
def test_cache_info_command(tmp_path):
    """Display cache information"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test\n\nParagraph.", encoding='utf-8')

    # Create cache
    doc = Document(
        path=doc_path,
        sections=[Section(level=1, title="Test", paragraphs=[Paragraph(text="P", index=0, line_number=3)])]
    )
    cache_manager = CacheManager()
    cache_manager.save_document_cache(doc_path, doc)

    # Check cache info
    runner = CliRunner()
    result = runner.invoke(cli, ['cache-info', str(doc_path)])
    assert result.exit_code == 0
    assert "Cache valid" in result.output or "Valid" in result.output
    assert "1 sections" in result.output or "1 paragraph" in result.output
```

**Implementation**: Add `cache-info` CLI command with status and statistics

---

## Edge Cases & Error Handling

### Cycle 12: Handle missing cache file gracefully
**Test**: `test_missing_cache_file_returns_none`
```python
def test_missing_cache_file_returns_none(tmp_path):
    """get_cached_document() returns None if cache doesn't exist"""
    doc_path = tmp_path / "nonexistent.md"
    cache_manager = CacheManager()
    result = cache_manager.get_cached_document(doc_path)
    assert result is None
```

---

### Cycle 13: Handle corrupted cache file
**Test**: `test_corrupted_cache_file_handled_gracefully`
```python
def test_corrupted_cache_file_handled_gracefully(tmp_path):
    """Corrupted cache file is ignored and regenerated"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test", encoding='utf-8')
    cache_path = doc_path.with_suffix('.md.doccache')

    # Create corrupted cache
    cache_path.write_text("{ invalid json }", encoding='utf-8')

    # parse_markdown should handle gracefully
    doc = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    assert doc is not None

    # New valid cache should be created
    cache_data = json.loads(cache_path.read_text())
    assert "version" in cache_data
```

---

### Cycle 14: Handle permission errors
**Test**: `test_cache_permission_error_handled`
```python
@pytest.mark.skipif(os.name == 'nt', reason="Permissions different on Windows")
def test_cache_permission_error_handled(tmp_path):
    """Permission errors when writing cache don't crash the program"""
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test", encoding='utf-8')
    cache_path = doc_path.with_suffix('.md.doccache')

    # Make directory read-only
    tmp_path.chmod(0o444)

    # Should still parse (just no cache)
    doc = parse_markdown(doc_path.read_text(), path=doc_path, generate_embeddings=True)
    assert doc is not None
    assert not cache_path.exists()

    # Restore permissions
    tmp_path.chmod(0o755)
```

---

## Definition of Done

- [ ] All 14 test cycles pass
- [ ] `CacheManager` class in `infrastructure/cache.py`
- [ ] `parse_markdown()` automatically uses cache
- [ ] All commands support `--reparse` flag
- [ ] `cache-clear` and `cache-info` commands implemented
- [ ] Cache format documented in CLAUDE.md
- [ ] Integration tests with real documents
- [ ] README.md updated with caching documentation

---

## Success Metrics

**Performance**:
- Second run on same document: <100ms (vs 10-30s first run)
- Cache file size: ~10-50% larger than source (embeddings + metadata)

**UX**:
- Users see clear "Using cached analysis" message
- No manual cache management needed (automatic)
- `--reparse` available when needed

**Reliability**:
- Invalid cache detected automatically
- Corrupted cache handled gracefully
- No crashes on permission errors

---

## Example Usage After Implementation

```bash
# First run: slow (generates embeddings)
$ uv run python -m doc_handler check-redundancy documento.md
Processing batch 1/3: 50 texts, ~2900 tokens
Processing batch 2/3: 48 texts, ~2850 tokens
Processing batch 3/3: 22 texts, ~1200 tokens
Documento parseado: 10 secciones, 120 párrafos
...

# Second run: instant (uses cache)
$ uv run python -m doc_handler check-redundancy documento.md
Using cached analysis (documento.md.doccache)
Documento parseado: 10 secciones, 120 párrafos
...

# Force regeneration
$ uv run python -m doc_handler check-redundancy documento.md --reparse
Reparsing document (ignoring cache)
Processing batch 1/3: 50 texts, ~2900 tokens
...

# Check cache status
$ uv run python -m doc_handler cache-info documento.md
Cache file: documento.md.doccache
Status: Valid
Created: 2025-11-05 16:30:00
Source hash: abc123...
Document: 10 sections, 120 paragraphs, 120 embeddings

# Clear cache
$ uv run python -m doc_handler cache-clear documento.md
Cache cleared: documento.md.doccache
```
