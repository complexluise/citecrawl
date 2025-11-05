"""File handling utilities for backup, diff display, and modifications"""
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from difflib import unified_diff

from doc_handler.domain.models import Paragraph


def create_backup(file_path: Path) -> Path:
    """Create a backup file with .backup extension.

    Args:
        file_path: Path to the file to backup

    Returns:
        Path to the created backup file

    The backup will overwrite any existing backup file.
    """
    backup_path = Path(str(file_path) + '.backup')
    content = file_path.read_text(encoding='utf-8')
    backup_path.write_text(content, encoding='utf-8')
    return backup_path


def apply_changes(file_path: Path, new_content: str) -> None:
    """Apply changes to a file, preserving UTF-8 encoding and formatting.

    Args:
        file_path: Path to the file to modify
        new_content: New content to write to the file

    The file is written with UTF-8 encoding, preserving all formatting
    including blank lines and spacing.
    """
    file_path.write_text(new_content, encoding='utf-8')


def show_diff(original: str, modified: str, console: Console) -> None:
    """Display a colored diff between original and modified content.

    Args:
        original: Original file content
        modified: Modified file content
        console: Rich Console for output

    Uses Rich's Syntax highlighting to display the diff in a readable format.
    """
    # Check if content is identical
    if original == modified:
        console.print("[dim]No hay cambios en el contenido.[/dim]")
        return

    # Generate unified diff
    diff_lines = list(unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile='original',
        tofile='modified',
        lineterm=''
    ))

    if not diff_lines:
        console.print("[dim]No hay cambios en el contenido.[/dim]")
        return

    # Join diff lines
    diff_text = ''.join(diff_lines)

    # Display with syntax highlighting
    console.print("\n[bold]Cambios propuestos:[/bold]\n")
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, border_style="yellow", title="Diff"))


def prompt_confirmation(console: Console) -> bool:
    """Prompt user for confirmation to apply changes.

    Args:
        console: Rich Console for input/output

    Returns:
        True if user confirms (enters 's' or 'S'), False otherwise

    The default response (pressing Enter) is No/False.
    """
    response = console.input("\n[bold yellow]¿Aplicar cambio? [s/N]:[/bold yellow] ")
    return response.strip().lower() == 's'


def remove_redundant_paragraph(content: str, paragraph: Paragraph) -> str:
    """Remove a redundant paragraph from markdown content.

    Args:
        content: Original markdown content
        paragraph: Paragraph object to remove (uses line_number and text)

    Returns:
        Modified content with the paragraph removed

    Preserves formatting by:
    - Using line_number to locate the paragraph
    - Removing the paragraph and its trailing blank line
    - Maintaining all other spacing and formatting
    """
    lines = content.split('\n')

    # Find paragraph start (line_number is 1-indexed)
    start = paragraph.line_number - 1

    # Validate start position
    if start < 0 or start >= len(lines):
        return content

    # Find paragraph end (next blank line or end of file)
    end = start
    while end < len(lines) and lines[end].strip():
        end += 1

    # Remove paragraph lines and the following blank line (if it exists)
    if end < len(lines):
        # Remove paragraph + blank line
        new_lines = lines[:start] + lines[end + 1:]
    else:
        # Last paragraph - no blank line after
        new_lines = lines[:start]

    return '\n'.join(new_lines)
