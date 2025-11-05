"""CLI commands for doc_handler"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from doc_handler.domain.parser import parse_markdown
from doc_handler.domain.exceptions import SectionNotFoundError
from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer


console = Console()


@click.group()
def cli():
    """doc_handler - Intelligent Markdown editor with AI assistance"""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.argument("section_title")
@click.option("--threshold", default=0.7, type=float, help="Similarity threshold (0.0-1.0)")
def check_redundancy_section(file_path: str, section_title: str, threshold: float):
    """Detect redundancies in a specific section.

    FILE_PATH: Path to the Markdown file
    SECTION_TITLE: Exact title of the section to analyze
    """
    file_path_obj = Path(file_path)

    # Header
    console.print(
        Panel.fit(
            f"Análisis de redundancias en \"{section_title}\"",
            border_style="blue"
        )
    )

    try:
        # Parse document
        with console.status("[bold green]Parseando documento..."):
            content = file_path_obj.read_text(encoding='utf-8')
            doc = parse_markdown(content, path=file_path_obj, generate_embeddings=True)

        console.print(f"[green]Documento parseado: {len(doc.sections)} secciones encontradas[/green]")

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
def check_redundancy(file_path: str, threshold: float):
    """Detect redundancies across entire document.

    FILE_PATH: Path to the Markdown file
    """
    file_path_obj = Path(file_path)

    # Header
    console.print(
        Panel.fit(
            "Análisis de redundancias globales",
            border_style="blue"
        )
    )

    try:
        # Parse document
        with console.status("[bold green]Parseando documento..."):
            content = file_path_obj.read_text(encoding='utf-8')
            doc = parse_markdown(content, path=file_path_obj, generate_embeddings=True)

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


if __name__ == "__main__":
    cli()
