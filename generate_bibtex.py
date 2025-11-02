import os
import re
import click
from rich.logging import RichHandler
import logging

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

def generate_citation_key(author, year, title):
    """Generate a BibTeX citation key."""
    author_part = 'unknown'
    if author and author != 'nan':
        author_part = re.split(r'[,(]', author)[0].strip().split(' ')[-1].lower()

    year_part = 'nodate'
    if year and year != 'nan':
        # Extract the year part if it's a string
        year_match = re.search(r'\d{4}', str(year))
        if year_match:
            year_part = year_match.group(0)

    title_part = 'notitle'
    if title and title != 'nan':
        title_part = title.strip().split(' ')[0].lower()

    return f"{author_part}{year_part}{title_part}"


def parse_md_file(filepath):
    """Parse the metadata from a markdown file."""
    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('# '):
                metadata['title'] = line[2:].strip()
            elif line.startswith('**'):
                parts = line.split(':**')
                if len(parts) == 2:
                    key = parts[0][2:].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    metadata[key] = value
            # Stop parsing after the metadata section
            elif line.strip() == '---':
                break
    return metadata

def get_bibtex_type(resource_type):
    """Map resource type to BibTeX entry type."""
    if not resource_type or resource_type == 'nan':
        return 'misc'
    resource_type = resource_type.lower()
    if 'artículo' in resource_type:
        return 'article'
    if 'libro' in resource_type:
        return 'book'
    return 'misc'

@click.command()
@click.option('--input-dir', default='output', help='Directory containing the markdown files.')
@click.option('--output-file', default='bibliography.bib', help='Path to the output BibTeX file.')
def main(input_dir, output_file):
    """
    Generates a BibTeX file from markdown files.
    """
    if not os.path.exists(input_dir):
        logging.error(f"Input directory '{input_dir}' not found.")
        return

    bibtex_entries = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(input_dir, filename)
            logging.info(f"Processing {filename}...")
            metadata = parse_md_file(filepath)

            if 'title' in metadata:
                author = metadata.get('autor(es)')
                year = metadata.get('año_de_publicación')
                title = metadata.get('title')
                resource_type = metadata.get('tipo_de_recurso')
                url = metadata.get('enlace/url')

                citation_key = generate_citation_key(author, year, title)
                bibtex_type = get_bibtex_type(resource_type)

                entry = f"@{bibtex_type}{{{citation_key},\n"
                if title:
                    entry += f"  title = {{{{{title}}}}},\n"
                if author:
                    entry += f"  author = {{{author}}},"
                if year:
                    # Clean up year value
                    year_clean = re.search(r'\d{4}', str(year))
                    if year_clean:
                        entry += f"  year = {{{year_clean.group(0)}}},"
                if url:
                    entry += f"  url = {{{url}}},"
                entry += "}\n"
                bibtex_entries.append(entry)
            else:
                logging.warning(f"Could not parse title from {filename}. Skipping.")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(bibtex_entries))

    logging.info(f"Successfully generated BibTeX file: {output_file}")

if __name__ == '__main__':
    main()
