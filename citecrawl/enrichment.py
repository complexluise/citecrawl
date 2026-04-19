import json
import google.generativeai as genai
from citecrawl.models import CSVRow, ScrapedData

def enrich_content(scraped_data: ScrapedData, api_key: str) -> CSVRow:
    """
    Enriches the scraped content by generating a summary and extracting
    bibliographic metadata using the Gemini API.

    Args:
        scraped_data: A ScrapedData object containing the scraped content and metadata.
        api_key: The API key for the Gemini service.

    Returns:
        An updated CSVRow object with the enriched data.
    """
    row = scraped_data.csv_row
    scraped_content = scraped_data.content
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    guide_context = """
    The overall goal is to build a resource guide for public and community libraries in Ibero-America 
    on how to integrate artificial intelligence ethically, critically, and with a human-centered approach. 
    When extracting information, prioritize what would be most useful for a librarian or community mediator.
    """

    system_prompt = f"""
    You are a meticulous research assistant specializing in bibliographic data extraction for libraries. 
    Your task is to analyze the provided web page content and extract the information needed to complete a bibliographic record.
    {guide_context}

    Analyze the following content:
    ---
    {scraped_content}
    ---

    Based on the content, please output a JSON object with the following structure. If a field is not available, use an empty string "".

    {{
        "Título": "The full title of the article or page.",
        "Autor(es)": "The author or authors, separated by commas if multiple.",
        "Año de Publicación": "The year the content was published (YYYY).",
        "Tipo de Recurso": "The type of content (e.g., 'Article', 'Blog Post', 'Report', 'News').",
        "Resumen Principal": "A concise, neutral summary of the main points of the content.",
        "Aspectos Más Relevantes (Relacionado con Bibliotecas)": "Identify 1-3 key takeaways from the content that are specifically relevant for public or community libraries. Focus on ethical considerations, practical applications, critical perspectives, or community impact.",
        "Comentarios / Ideas para la Guía": "Suggest 1-2 brief ideas or comments inspired by the content that could be incorporated into a practical guide for librarians about AI."
    }}
    """

    response = model.generate_content(system_prompt)
    
    # Clean the response to ensure it's valid JSON
    cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        enriched_json = json.loads(cleaned_response_text)
        
        # TODO: esta logica esta muy acoplada
        if not row.title:
            row.title = enriched_json.get("Título")
        if not row.authors:
            row.authors = enriched_json.get("Autor(es)")
        if not row.publication_year:
            row.publication_year = enriched_json.get("Año de Publicación")
        if not row.resource_type:
            row.resource_type = enriched_json.get("Tipo de Recurso")
        if not row.main_summary:
            row.main_summary = enriched_json.get("Resumen Principal")
        if not row.relevant_aspects:
            relevant_aspects = enriched_json.get("Aspectos Más Relevantes (Relacionado con Bibliotecas)")
            if isinstance(relevant_aspects, list):
                row.relevant_aspects = "\n".join(relevant_aspects)
            else:
                row.relevant_aspects = relevant_aspects
        if not row.comments:
            comments = enriched_json.get("Comentarios / Ideas para la Guía")
            if isinstance(comments, list):
                row.comments = "\n".join(comments)
            else:
                row.comments = comments
        
        row.extracted = True
        return row
    except (json.JSONDecodeError, TypeError) as e:
        # Handle cases where the model's output is not valid JSON
        print(f"Error decoding JSON from model response: {e}")
        # Return the original row to avoid crashing
        return row
