import os
import re
import logging

def generate_citation_key(author, year, title):
    """Generate a BibTeX citation key."""
    author_part = 'unknown'
    if author and author != 'nan':
        author_part = re.split(r'[,(]', author)[0].strip().split(' ')[-1].lower()

    year_part = 'nodate'
    if year and year != 'nan':
        year_match = re.search(r'\d{4}', str(year))
        if year_match:
            year_part = year_match.group(0)

    title_part = 'notitle'
    if title and title != 'nan':
        title_part = title.strip().split(' ')[0].lower()

    return f"{author_part}{year_part}{title_part}"

def parse_enriched_md(filepath):
    """Parse metadata from the new enriched markdown file format."""
    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        # Metadata is in the first "---" block
        metadata_section = content.split('---')[1]
        for line in metadata_section.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip().lower().replace(' ', '_')] = value.strip()
    return metadata

def generate_bibtex(input_dir='output', output_file='bibliography.bib'):
    """
    Generates a BibTeX file from enriched markdown files.
    """
    if not os.path.exists(input_dir):
        logging.error(f"Input directory '{input_dir}' not found.")
        return

    bibtex_entries = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(input_dir, filename)
            logging.info(f"Processing {filename} for BibTeX generation...")
            try:
                metadata = parse_enriched_md(filepath)
                title = metadata.get('title')
                author = metadata.get('author(s)')
                year = metadata.get('publication_year')
                url = metadata.get('source_url')

                if title:
                    citation_key = generate_citation_key(author, year, title)
                    entry = f"@misc{{{citation_key},\n"
                    entry += f"  title = {{{{{title}}}}},\n"
                    if author:
                        entry += f"  author = {{{author}}},\n"
                    if year:
                        entry += f"  year = {{{year}}},\n"
                    if url:
                        entry += f"  url = {{{url}}},\n"
                    entry = entry.strip().strip(',') + "\n}"
                    bibtex_entries.append(entry)
                else:
                    logging.warning(f"Could not parse title from {filename}. Skipping.")
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")


    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(bibtex_entries))

    logging.info(f"Successfully generated BibTeX file: {output_file}")
