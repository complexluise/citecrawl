import json
import google.generativeai as genai
from src.models import ScrapedData, EnrichedData

def enrich_content(scraped_data: ScrapedData, user_prompt: str, api_key: str) -> EnrichedData:
    """
    Enriches the scraped content by generating a summary and extracting
    bibliographic metadata using the Gemini API.

    Args:
        scraped_data: The data scraped from a URL.
        user_prompt: The user's question to be answered by the summary.
        api_key: The API key for the Gemini service.

    Returns:
        An EnrichedData object containing the summary and bibliography.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    system_prompt = f"""
    You are a research assistant. Your task is to analyze the provided web page content
    and generate two pieces of information:
    1. A concise summary that directly answers the user's question: "{user_prompt}"
    2. Bibliographic metadata for citation purposes (Title, Author, Year).

    Analyze the following content:
    ---
    {scraped_data.content}
    ---

    Based on the content, please output a JSON object with the following structure:
    {{
        "summary": "Your concise summary here.",
        "bibliography": {{
            "title": "Extracted Title",
            "author": "Extracted Author(s)",
            "year": YYYY
        }}
    }}
    """

    response = model.generate_content(system_prompt)
    
    # Clean the response to ensure it's valid JSON
    cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        enriched_json = json.loads(cleaned_response_text)
        return EnrichedData.model_validate(enriched_json)
    except (json.JSONDecodeError, TypeError) as e:
        # Handle cases where the model's output is not valid JSON
        print(f"Error decoding JSON from model response: {e}")
        # Return a default or empty object to avoid crashing
        return EnrichedData(summary="Failed to parse AI response.", bibliography={})

