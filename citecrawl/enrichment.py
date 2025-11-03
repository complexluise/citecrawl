import json
import google.generativeai as genai
from citecrawl.models import CSVRow

def enrich_content(row: CSVRow, scraped_content: str, api_key: str) -> CSVRow:
    """
    Enriches the scraped content by generating a summary and extracting
    bibliographic metadata using the Gemini API.

    Args:
        row: A CSVRow object representing a row from the CSV file.
        scraped_content: The content scraped from the URL.
        api_key: The API key for the Gemini service.

    Returns:
        An updated CSVRow object with the enriched data.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    system_prompt = f"""
    You are a research assistant. Your task is to analyze the provided web page content
    and generate two pieces of information:
    1. A concise summary.
    2. The title of the page.

    Analyze the following content:
    ---
    {scraped_content}
    ---

    Based on the content, please output a JSON object with the following structure:
    {{
        "Resumen Principal": "Your concise summary here.",
        "Título": "Extracted Title"
    }}
    """

    response = model.generate_content(system_prompt)
    
    # Clean the response to ensure it's valid JSON
    cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        enriched_json = json.loads(cleaned_response_text)
        row.main_summary = enriched_json.get("Resumen Principal")
        row.title = enriched_json.get("Título")
        row.extracted = True
        return row
    except (json.JSONDecodeError, TypeError) as e:
        # Handle cases where the model's output is not valid JSON
        print(f"Error decoding JSON from model response: {e}")
        # Return the original row to avoid crashing
        return row
