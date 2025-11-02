import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def enrich_content(content: str, prompt: str) -> str:
    """
    Enriches content using the Gemini API.

    Args:
        content: The content to enrich.
        prompt: The prompt to use for enrichment.

    Returns:
        The enriched content, or an empty string if an error occurs.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not set.")
        return ""

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-latest')

    try:
        # Construct a more detailed prompt for the model
        full_prompt = f"""
        Based on the following text, please perform two tasks:

        1.  Extract the following bibliographic metadata:
            *   Title
            *   Author(s)
            *   Publication Year
            *   Source URL (if available)

        2.  Answer the following question: "{prompt}"

        Please format your response as follows, with "---" separating the sections:

        ---
        Title: [Extracted Title]
        Author(s): [Extracted Author(s)]
        Publication Year: [Extracted Publication Year]
        Source URL: [Extracted Source URL]
        ---

        ### AI Summary

        *Based on your prompt: "{prompt}"*

        [Your answer to the question]

        ---

        Original Text:
        {content}
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error enriching content: {e}")
        return ""
