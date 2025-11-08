
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch

from doc_handler.cli.commands import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_md_file(tmp_path):
    md_content = """
# Introduction

This is the first paragraph.

This is the second paragraph, which is very similar to the first one.

# Chapter 1

This is a paragraph in another chapter.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path

def test_check_redundancy_command_no_redundancy(runner, tmp_path):
    """
    Test the 'check-redundancy' command when no significant redundancy is found.
    """
    md_content = """
# Title 1
First paragraph.

# Title 2
Second paragraph, completely different.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(md_content, encoding="utf-8")

    # Mock embeddings to control similarity
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        # Assign different vectors to ensure low similarity
        mock_embed.return_value = [[1.0, 0.0], [0.0, 1.0]]

        result = runner.invoke(cli, ["check-redundancy", str(file_path), "--threshold", "0.9"])

    assert result.exit_code == 0
    assert "No se encontraron redundancias globales" in result.output

def test_check_redundancy_command_with_redundancy(runner, tmp_path):
    """
    Test the 'check-redundancy' command when redundancy is found.
    """
    md_content = """
# Title 1
A paragraph that will be repeated.

# Title 2
A paragraph that will be repeated.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(md_content, encoding="utf-8")

    # Mock embeddings to be identical
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        mock_embed.return_value = [[0.5, 0.5], [0.5, 0.5]]

        result = runner.invoke(cli, ["check-redundancy", str(file_path), "--threshold", "0.9"])

    assert result.exit_code == 0
    assert "Top 1 redundancias encontradas" in result.output
    assert "Similitud: 100%" in result.output

def test_check_redundancy_section_command_success(runner, temp_md_file):
    """
    Test the 'check-redundancy-section' command for a specific section.
    """
    # Mock embeddings to control similarity
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        # Make first two paragraphs similar, the third one different
        mock_embed.return_value = [[0.1, 0.2], [0.1, 0.21], [0.9, 0.8]]

        result = runner.invoke(cli, ["check-redundancy-section", str(temp_md_file), "Introduction", "--threshold", "0.95"])

    assert result.exit_code == 0
    assert 'Análisis de redundancias en "Introduction"' in result.output
    assert "Encontradas 1 redundancias" in result.output
    assert "Similitud: 100%" in result.output # Cosine similarity is ~1.0

def test_check_redundancy_section_not_found(runner, temp_md_file):
    """
    Test the 'check-redundancy-section' command when the section does not exist.
    """
    result = runner.invoke(cli, ["check-redundancy-section", str(temp_md_file), "NonExistent Chapter"])

    assert result.exit_code == 0
    assert 'Error: Sección "NonExistent Chapter" no encontrada' in result.output
    assert "Secciones disponibles:" in result.output
    assert "* Introduction" in result.output
    assert "* Chapter 1" in result.output

def test_propose_fix_command_user_accepts(runner, tmp_path):
    """
    Test the 'propose-fix' command where the user accepts the proposed change.
    """
    md_content = """
# Introduction
This is a redundant paragraph.

This is a redundant paragraph.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(md_content, encoding="utf-8")

    # Mock embeddings to be identical
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        mock_embed.return_value = [[0.5, 0.5], [0.5, 0.5]]

        # Simulate user typing 's' for yes
        result = runner.invoke(cli, ["propose-fix", str(file_path), "Introduction"], input="s\n")

    assert result.exit_code == 0
    assert "Propuesta de cambios para \"Introduction\"" in result.output
    assert "Encontradas 1 redundancias" in result.output
    assert "Propuesta: Eliminar párrafo #2" in result.output
    assert "Cambio aplicado" in result.output
    assert "1 cambio(s) aplicado(s) exitosamente" in result.output

    # Verify backup was created
    backup_path = file_path.with_suffix(".md.backup")
    assert backup_path.exists()

    # Verify file content was changed
    final_content = file_path.read_text(encoding="utf-8")
    assert final_content.strip() == "# Introduction\nThis is a redundant paragraph."

def test_propose_fix_command_user_rejects(runner, tmp_path):
    """
    Test the 'propose-fix' command where the user rejects the proposed change.
    """
    original_content = """
# Introduction
This is a redundant paragraph.

This is a redundant paragraph.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(original_content, encoding="utf-8")

    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        mock_embed.return_value = [[0.5, 0.5], [0.5, 0.5]]

        # Simulate user typing 'n' for no
        result = runner.invoke(cli, ["propose-fix", str(file_path), "Introduction"], input="n\n")

    assert result.exit_code == 0
    assert "Cambio descartado" in result.output
    assert "No se aplicaron cambios" in result.output

    # Verify file content remains unchanged
    final_content = file_path.read_text(encoding="utf-8")
    assert final_content == original_content

def test_cache_reparse_flag(runner, temp_md_file):
    """
    Test that the --reparse flag forces re-parsing and ignores the cache.
    """
    # Run once to create the cache
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        result1 = runner.invoke(cli, ["check-redundancy", str(temp_md_file)])
        assert "Generando embeddings" in result1.output
        assert mock_embed.called

    # Run again - should use cache
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        result2 = runner.invoke(cli, ["check-redundancy", str(temp_md_file)])
        assert "Documento cargado desde la caché" in result2.output
        assert not mock_embed.called

    # Run with --reparse - should re-generate embeddings
    with patch("doc_handler.infrastructure.embeddings.generate_embeddings_batch") as mock_embed:
        result3 = runner.invoke(cli, ["check-redundancy", str(temp_md_file), "--reparse"])
        assert "Generando embeddings" in result3.output
        assert mock_embed.called

def test_cache_info_command(runner, temp_md_file):
    """
    Test the 'cache-info' command.
    """
    # First, run a command to cache the file
    runner.invoke(cli, ["check-redundancy", str(temp_md_file)])

    # Now, check the cache info
    result = runner.invoke(cli, ["cache-info", str(temp_md_file)])

    assert result.exit_code == 0
    assert "Información de caché para" in result.output
    assert "Ruta del archivo" in result.output
    assert "Fecha de modificación original" in result.output

def test_cache_clear_command(runner, temp_md_file):
    """
    Test the 'cache-clear' command.
    """
    # Cache the file first
    runner.invoke(cli, ["check-redundancy", str(temp_md_file)])

    # Make sure it's cached by running info
    info_result1 = runner.invoke(cli, ["cache-info", str(temp_md_file)])
    assert "No hay caché para este archivo" not in info_result1.output

    # Clear the cache
    clear_result = runner.invoke(cli, ["cache-clear", str(temp_md_file)])
    assert clear_result.exit_code == 0
    assert "Caché para test.md ha sido eliminada" in clear_result.output

    # Verify it's gone
    info_result2 = runner.invoke(cli, ["cache-info", str(temp_md_file)])
    assert "No hay caché para este archivo" in info_result2.output

