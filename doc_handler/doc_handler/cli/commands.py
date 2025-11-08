"""CLI commands for doc_handler"""
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from doc_handler.domain.exceptions import SectionNotFoundError
from doc_handler.domain.models import Document, Section
from doc_handler.domain.parser import parse_markdown

from doc_handler.infrastructure.cache import DocumentCache
from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer
from doc_handler.infrastructure.file_handler import (
    create_backup, show_diff, prompt_confirmation, apply_changes, remove_redundant_paragraph
)



console = Console()


@click.group()
def cli():
    """doc_handler - Intelligent Markdown editor with AI assistance"""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.argument("section_title")
@click.option("--threshold", default=0.7, type=float, help="Similarity threshold (0.0-1.0)")
@click.option("--reparse", is_flag=True, help="Force re-parsing and re-generation of embeddings.")
def check_redundancy_section(file_path: str, section_title: str, threshold: float, reparse: bool):
    """Detect redundancies in a specific section.

    FILE_PATH: Path to the Markdown file
    SECTION_TITLE: Exact title of the section to analyze
    """
    file_path_obj = Path(file_path)
    cache = DocumentCache()

    # Header
    console.print(
        Panel.fit(
            f"Análisis de redundancias en \"{section_title}\"",
            border_style="blue"
        )
    )

    try:
        # Attempt to load from cache
        doc = None
        if not reparse:
            with console.status("[bold cyan]Buscando en caché..."):
                doc = cache.get(file_path_obj)
            if doc:
                console.print("[green]✓ Documento cargado desde la caché.[/green]")

        # If not cached or reparse is forced, parse the document
        if doc is None:
            console.print("[yellow]Generando embeddings... (esto puede tardar un momento)[/yellow]")
            with console.status("[bold green]Parseando documento..."):
                content = file_path_obj.read_text(encoding='utf-8')
                doc = parse_markdown(content, path=file_path_obj, generate_embeddings=True)
                cache.set(file_path_obj, doc)
            console.print(f"[green]✓ Documento parseado y cacheado: {len(doc.sections)} secciones encontradas[/green]")

        # Find section
        try:
            section = doc.find_section(section_title)
        except SectionNotFoundError as e:
            console.print(f"\n[bold red]Error: Sección \"{section_title}\" no encontrada[/bold red]\n")
            console.print("[bold]Secciones disponibles:[/bold]")
            for title in e.available:
                console.print(f"  * {title}")

            # Simple suggestion (could be improved with difflib)
            if section_title.lower() in [t.lower() for t in e.available]:
                correct = [t for t in e.available if t.lower() == section_title.lower()][0]
                console.print(f"\n[yellow]¿Quisiste decir \"{correct}\"?[/yellow]")
            return

        # Analyze redundancies
        with console.status(f"[bold yellow]Analizando sección ({len(section.paragraphs)} párrafos)..."):
            analyzer = EmbeddingAnalyzer()
            report = analyzer.analyze_section(section, threshold=threshold)

        # Display results
        if not report.has_redundancies:
            console.print("\n[bold green]No se encontraron redundancias[/bold green]")
        else:
            console.print(f"\n[bold yellow]Encontradas {report.redundancy_count} redundancias:[/bold yellow]\n")

            for i, redundancy in enumerate(report.redundancies, 1):
                # Create table for each redundancy
                table = Table(title=f"Redundancia #{i} • Similitud: {redundancy.similarity_percentage}%",
                            border_style="yellow")

                table.add_column("Párrafo", style="cyan")
                table.add_column("Línea", style="magenta")
                table.add_column("Contenido", style="white", overflow="fold")

                # Add rows
                table.add_row(
                    f"#{redundancy.paragraph1.index + 1}",
                    str(redundancy.paragraph1.line_number),
                    redundancy.paragraph1.text[:100] + "..." if len(redundancy.paragraph1.text) > 100
                    else redundancy.paragraph1.text
                )
                table.add_row(
                    f"#{redundancy.paragraph2.index + 1}",
                    str(redundancy.paragraph2.line_number),
                    redundancy.paragraph2.text[:100] + "..." if len(redundancy.paragraph2.text) > 100
                    else redundancy.paragraph2.text
                )

                console.print(table)
                console.print()

    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        raise


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--threshold", default=0.7, type=float, help="Similarity threshold (0.0-1.0)")
@click.option("--reparse", is_flag=True, help="Force re-parsing and re-generation of embeddings.")
def check_redundancy(file_path: str, threshold: float, reparse: bool):
    """Detect redundancies across entire document.

    FILE_PATH: Path to the Markdown file
    """
    file_path_obj = Path(file_path)
    cache = DocumentCache()

    # Header
    console.print(
        Panel.fit(
            "Análisis de redundancias globales",
            border_style="blue"
        )
    )

    try:
        # Attempt to load from cache
        doc = None
        if not reparse:
            with console.status("[bold cyan]Buscando en caché..."):
                doc = cache.get(file_path_obj)
            if doc:
                console.print("[green]✓ Documento cargado desde la caché.[/green]")

        # If not cached or reparse is forced, parse the document
        if doc is None:
            console.print("[yellow]Generando embeddings... (esto puede tardar un momento)[/yellow]")
            with console.status("[bold green]Parseando documento..."):
                content = file_path_obj.read_text(encoding='utf-8')
                doc = parse_markdown(content, path=file_path_obj, generate_embeddings=True)
                cache.set(file_path_obj, doc)

        # Count total paragraphs
        def count_paragraphs(sections):
            count = 0
            for section in sections:
                count += len(section.paragraphs)
                if section.subsections:
                    count += count_paragraphs(section.subsections)
            return count

        total_paragraphs = count_paragraphs(doc.sections)
        console.print(f"[green]Documento parseado: {len(doc.sections)} secciones, {total_paragraphs} párrafos[/green]")

        # Analyze redundancies
        with console.status("[bold yellow]Analizando documento completo..."):
            analyzer = EmbeddingAnalyzer()
            report = analyzer.analyze_document(doc, threshold=threshold)

        # Display statistics
        console.print("\n[bold]Estadísticas:[/bold]")
        console.print(f"  * Total de párrafos analizados: {report.total_paragraphs}")
        comparisons = (report.total_paragraphs * (report.total_paragraphs - 1)) // 2
        console.print(f"  * Comparaciones realizadas: {comparisons}")
        console.print(f"  * Pares redundantes encontrados: {report.redundancy_count}")

        # Display results
        if not report.has_redundancies:
            console.print("\n[bold green]No se encontraron redundancias globales[/bold green]")
        else:
            console.print(f"\n[bold yellow]Top {min(report.redundancy_count, 10)} redundancias encontradas:[/bold yellow]\n")

            # Show top 10 redundancies
            for i, redundancy in enumerate(report.redundancies[:10], 1):
                table = Table(title=f"Redundancia #{i} • Similitud: {redundancy.similarity_percentage}%",
                            border_style="yellow")

                table.add_column("Párrafo", style="cyan")
                table.add_column("Línea", style="magenta")
                table.add_column("Contenido", style="white", overflow="fold")

                table.add_row(
                    f"#{redundancy.paragraph1.index + 1}",
                    str(redundancy.paragraph1.line_number),
                    redundancy.paragraph1.text[:100] + "..." if len(redundancy.paragraph1.text) > 100
                    else redundancy.paragraph1.text
                )
                table.add_row(
                    f"#{redundancy.paragraph2.index + 1}",
                    str(redundancy.paragraph2.line_number),
                    redundancy.paragraph2.text[:100] + "..." if len(redundancy.paragraph2.text) > 100
                    else redundancy.paragraph2.text
                )

                console.print(table)
                console.print()

            if report.redundancy_count > 10:
                console.print(f"... y {report.redundancy_count - 10} redundancias más", style="dim")

    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        raise


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.argument("section_title")
@click.option("--threshold", default=0.7, type=float, help="Similarity threshold (0.0-1.0)")
@click.option("--interactive", is_flag=True, help="Interactively review each redundancy")
@click.option("--reparse", is_flag=True, help="Force re-parsing and re-generation of embeddings.")
def propose_fix(file_path: str, section_title: str, threshold: float, interactive: bool, reparse: bool):
    """Propose fixes for redundancies in a section with user approval.

    FILE_PATH: Path to the Markdown file
    SECTION_TITLE: Exact title of the section to analyze

    Analyzes redundancies and proposes removing duplicates. Shows diff and
    asks for confirmation before making changes. Creates automatic backup.
    """
    file_path_obj = Path(file_path)
    cache = DocumentCache()

    # Header
    console.print(
        Panel.fit(
            f"Propuesta de cambios para \"{section_title}\"",
            border_style="blue"
        )
    )

    try:
        # Attempt to load from cache
        doc: Document = None
        if not reparse:
            with console.status("[bold cyan]Buscando en caché..."):
                doc: Document = cache.get(file_path_obj)
            if doc:
                console.print("[green]✓ Documento cargado desde la caché.[/green]")

        # If not cached or reparse is forced, parse the document
        if doc is None:
            console.print("[yellow]Generando embeddings... (esto puede tardar un momento)[/yellow]")
            with console.status("[bold green]Parseando documento..."):
                content = file_path_obj.read_text(encoding='utf-8')
                doc: Document = parse_markdown(content, path=file_path_obj, generate_embeddings=True)
                cache.set(file_path_obj, doc)
            console.print(f"[green]✓ Documento parseado y cacheado: {len(doc.sections)} secciones encontradas[/green]")
        else:
            content = file_path_obj.read_text(encoding='utf-8')

        # Find section
        try:
            section: Section = doc.find_section(section_title)
        except SectionNotFoundError as e:
            console.print(f"\n[bold red]Error: Sección \"{section_title}\" no encontrada[/bold red]\n")
            console.print("[bold]Secciones disponibles:[/bold]")
            for title in e.available:
                console.print(f"  * {title}")
            return

        # Analyze redundancies
        with console.status(f"[bold yellow]Analizando sección ({len(section.paragraphs)} párrafos)..."):
            analyzer = EmbeddingAnalyzer()
            report = analyzer.analyze_section(section, threshold=threshold)

        # Display results
        if not report.has_redundancies:
            console.print("\n[bold green]No se encontraron redundancias para corregir[/bold green]")
            return

        console.print(f"\n[bold yellow]Encontradas {report.redundancy_count} redundancias. Proponiendo correcciones:[/bold yellow]\n")

        changes_applied = 0
        current_content = content

        # Process each redundancy
        for i, redundancy in enumerate(report.redundancies, 1):
            console.print(f"\n[bold cyan]Redundancia #{i} (Similitud: {redundancy.similarity_percentage}%):[/bold cyan]")

            # Show redundant paragraphs
            table = Table(border_style="yellow")
            table.add_column("Párrafo", style="cyan")
            table.add_column("Línea", style="magenta")
            table.add_column("Contenido", style="white", overflow="fold")

            table.add_row(
                f"#{redundancy.paragraph1.index + 1}",
                str(redundancy.paragraph1.line_number),
                redundancy.paragraph1.text[:150] + "..." if len(redundancy.paragraph1.text) > 150
                else redundancy.paragraph1.text
            )
            table.add_row(
                f"#{redundancy.paragraph2.index + 1}",
                str(redundancy.paragraph2.line_number),
                redundancy.paragraph2.text[:150] + "..." if len(redundancy.paragraph2.text) > 150
                else redundancy.paragraph2.text
            )

            console.print(table)

            console.print(f"\n[yellow]Propuesta:[/yellow] Eliminar párrafo #{redundancy.paragraph2.index + 1}")

            # Generate proposed change
            new_content = remove_redundant_paragraph(current_content, redundancy.paragraph2)

            # Show diff
            show_diff(current_content, new_content, console)

            # Ask for confirmation
            if prompt_confirmation(console):
                # Create backup (only once, before first change)
                if changes_applied == 0:
                    backup_path = create_backup(file_path_obj)
                    console.print(f"\n[dim]Backup creado: {backup_path}[/dim]")

                # Apply change
                current_content = new_content
                changes_applied += 1
                console.print("[bold green]Cambio aplicado[/bold green]")
            else:
                console.print("[dim]Cambio descartado[/dim]")

            # In non-interactive mode, only process first redundancy
            if not interactive:
                break

        # Save all changes if any were applied
        if changes_applied > 0:
            apply_changes(file_path_obj, current_content)
            console.print(f"\n[bold green]✓ {changes_applied} cambio(s) aplicado(s) exitosamente[/bold green]")
            console.print(f"[dim]Backup en: {file_path_obj}.backup[/dim]")
        else:
            console.print("\n[yellow]No se aplicaron cambios[/yellow]")

    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        raise


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def cache_info(file_path: str):
    """Display cache information for a given file."""
    file_path_obj = Path(file_path)
    cache = DocumentCache()
    cache_path = cache._get_cache_path(file_path_obj)

    console.print(Panel.fit(f"Información de caché para {file_path_obj.name}", border_style="blue"))

    if not cache_path.exists():
        console.print("[yellow]No hay caché para este archivo.[/yellow]")
        return

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        table = Table(title="Metadatos de Caché")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="magenta")

        table.add_row("Ruta del archivo", str(data.get('source_path')))
        table.add_row("Fecha de modificación original", str(data.get('source_mtime')))
        table.add_row("Fecha de cacheo", str(data.get('cached_at')))
        table.add_row("Párrafos cacheados", str(len(data["document"]["sections"][0]["paragraphs"])))

        console.print(table)

    except (json.JSONDecodeError, KeyError):
        console.print("[red]Error: El archivo de caché está corrupto.[/red]")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def cache_clear(file_path: str):
    """Clear the cache for a specific file."""
    file_path_obj = Path(file_path)
    cache = DocumentCache()
    cache.clear(file_path_obj)
    console.print(f"[green]✓ Caché para {file_path_obj.name} ha sido eliminada.[/green]")


if __name__ == "__main__":
    cli()
