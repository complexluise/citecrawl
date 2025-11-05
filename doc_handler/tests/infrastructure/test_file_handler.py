"""Tests for file handler - backup, diff, and file modification"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from doc_handler.domain.models import Paragraph


# Sprint 1: Backup and File Operations

def test_create_backup_success():
    """Test backup creation with .backup extension"""
    from doc_handler.infrastructure.file_handler import create_backup

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("# Test\n\nContent here.")
        temp_path = Path(f.name)

    try:
        backup_path = create_backup(temp_path)

        # Verify backup exists
        assert backup_path.exists()
        assert str(backup_path).endswith('.md.backup')
        assert backup_path.read_text(encoding='utf-8') == "# Test\n\nContent here."
    finally:
        temp_path.unlink()
        if backup_path.exists():
            backup_path.unlink()


def test_create_backup_overwrites_existing():
    """Test that backup overwrites existing backup"""
    from doc_handler.infrastructure.file_handler import create_backup

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        file_path.write_text("New content", encoding='utf-8')

        backup_path = Path(tmpdir) / "test.md.backup"
        backup_path.write_text("Old backup content", encoding='utf-8')

        result_backup = create_backup(file_path)

        # Should overwrite old backup
        assert result_backup.read_text(encoding='utf-8') == "New content"


def test_apply_changes_preserves_utf8():
    """Test that apply_changes preserves UTF-8 encoding"""
    from doc_handler.infrastructure.file_handler import apply_changes

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        file_path.write_text("Original", encoding='utf-8')

        new_content = "Nuevo contenido con tildes: áéíóú ñ"
        apply_changes(file_path, new_content)

        result = file_path.read_text(encoding='utf-8')
        assert result == "Nuevo contenido con tildes: áéíóú ñ"


def test_apply_changes_preserves_formatting():
    """Test that apply_changes preserves blank lines and spacing"""
    from doc_handler.infrastructure.file_handler import apply_changes

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"

        original = """# Title

Paragraph 1 with spaces.

Paragraph 2.


Multiple blank lines above.
"""
        apply_changes(file_path, original)

        result = file_path.read_text(encoding='utf-8')
        assert result == original
        assert result.count('\n\n') == 3  # Blank lines preserved


# Sprint 2: Diff Display

def test_show_diff_simple_change():
    """Test diff display with simple change"""
    from doc_handler.infrastructure.file_handler import show_diff
    from rich.console import Console

    original = "Line 1\nLine 2\nLine 3"
    modified = "Line 1\nLine 2 modified\nLine 3"

    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)

    show_diff(original, modified, console)
    captured = output.getvalue()

    # Should show diff content
    assert "Line 1" in captured or "modified" in captured
    # Rich uses ANSI codes for colors
    assert "\x1b[" in captured or "diff" in captured.lower()


def test_show_diff_no_changes():
    """Test diff when content is identical"""
    from doc_handler.infrastructure.file_handler import show_diff
    from rich.console import Console

    original = "Same content"
    modified = "Same content"

    output = StringIO()
    console = Console(file=output, force_terminal=True)

    show_diff(original, modified, console)
    captured = output.getvalue()

    # Should indicate no changes
    assert "No hay cambios" in captured or "Sin diferencias" in captured or "identical" in captured.lower()


# Sprint 3: User Confirmation

def test_prompt_confirmation_user_accepts():
    """Test confirmation prompt when user accepts"""
    from doc_handler.infrastructure.file_handler import prompt_confirmation
    from rich.console import Console

    console = Console()

    with patch.object(console, 'input', return_value='s'):
        result = prompt_confirmation(console)

    assert result is True


def test_prompt_confirmation_user_rejects_default():
    """Test confirmation prompt with default (Enter = No)"""
    from doc_handler.infrastructure.file_handler import prompt_confirmation
    from rich.console import Console

    console = Console()

    with patch.object(console, 'input', return_value=''):
        result = prompt_confirmation(console)

    assert result is False


def test_prompt_confirmation_accepts_uppercase():
    """Test confirmation prompt accepts uppercase S"""
    from doc_handler.infrastructure.file_handler import prompt_confirmation
    from rich.console import Console

    console = Console()

    with patch.object(console, 'input', return_value='S'):
        result = prompt_confirmation(console)

    assert result is True


def test_prompt_confirmation_rejects_other_input():
    """Test confirmation prompt rejects anything other than s/S"""
    from doc_handler.infrastructure.file_handler import prompt_confirmation
    from rich.console import Console

    console = Console()

    with patch.object(console, 'input', return_value='n'):
        result = prompt_confirmation(console)

    assert result is False


# Sprint 4: Paragraph Removal

def test_remove_paragraph_middle():
    """Test removing a paragraph from the middle"""
    from doc_handler.infrastructure.file_handler import remove_redundant_paragraph

    content = """# Section

Paragraph 1.

Paragraph 2 to remove.

Paragraph 3.
"""

    paragraph = Paragraph(
        text="Paragraph 2 to remove.",
        index=1,
        line_number=5,
        embedding=None
    )

    result = remove_redundant_paragraph(content, paragraph)

    expected = """# Section

Paragraph 1.

Paragraph 3.
"""
    assert result == expected


def test_remove_paragraph_first():
    """Test removing the first paragraph"""
    from doc_handler.infrastructure.file_handler import remove_redundant_paragraph

    content = """# Section

First paragraph to remove.

Second paragraph stays.
"""

    paragraph = Paragraph(text="First paragraph to remove.", index=0, line_number=3, embedding=None)
    result = remove_redundant_paragraph(content, paragraph)

    expected = """# Section

Second paragraph stays.
"""
    assert result == expected


def test_remove_paragraph_last():
    """Test removing the last paragraph"""
    from doc_handler.infrastructure.file_handler import remove_redundant_paragraph

    content = """# Section

First paragraph.

Last paragraph to remove.
"""

    paragraph = Paragraph(text="Last paragraph to remove.", index=1, line_number=5, embedding=None)
    result = remove_redundant_paragraph(content, paragraph)

    expected = """# Section

First paragraph.
"""
    # Allow for trailing newline flexibility
    assert result.strip() == expected.strip()


# Sprint 5: Integration Tests

def test_full_workflow_user_accepts():
    """Test complete workflow when user accepts changes"""
    from doc_handler.infrastructure.file_handler import (
        create_backup, remove_redundant_paragraph, prompt_confirmation, apply_changes
    )
    from rich.console import Console

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        original_content = """# Test

Paragraph 1.

Paragraph 2 redundant.

Paragraph 3.
"""
        file_path.write_text(original_content, encoding='utf-8')

        paragraph_to_remove = Paragraph(
            text="Paragraph 2 redundant.",
            index=1,
            line_number=5,
            embedding=None
        )

        console = Console()

        # Simulate workflow
        backup = create_backup(file_path)
        new_content = remove_redundant_paragraph(original_content, paragraph_to_remove)

        with patch.object(console, 'input', return_value='s'):
            if prompt_confirmation(console):
                apply_changes(file_path, new_content)

        # Verify backup exists
        assert backup.exists()
        assert backup.read_text(encoding='utf-8') == original_content

        # Verify file modified
        result = file_path.read_text(encoding='utf-8')
        assert "Paragraph 2 redundant." not in result
        assert "Paragraph 1." in result
        assert "Paragraph 3." in result


def test_full_workflow_user_rejects():
    """Test complete workflow when user rejects changes"""
    from doc_handler.infrastructure.file_handler import (
        create_backup, remove_redundant_paragraph, prompt_confirmation, apply_changes
    )
    from rich.console import Console

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        original_content = """# Test

Paragraph 1.

Paragraph 2.
"""
        file_path.write_text(original_content, encoding='utf-8')

        paragraph_to_remove = Paragraph(text="Paragraph 2.", index=1, line_number=5, embedding=None)

        console = Console()

        backup = create_backup(file_path)
        new_content = remove_redundant_paragraph(original_content, paragraph_to_remove)

        with patch.object(console, 'input', return_value='n'):
            if prompt_confirmation(console):
                apply_changes(file_path, new_content)

        # File should NOT be modified
        assert file_path.read_text(encoding='utf-8') == original_content

        # But backup was created
        assert backup.exists()
