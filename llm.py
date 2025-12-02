import os

from dotenv import load_dotenv
from google import genai
import config

# Load environment variables from .env file
load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


def is_conflict_related(*, conflict_region: config.ConflictCountry, **kwargs: str | None) -> bool:
    """
    Use LLM to determine if the Short is related to an armed conflict region.
    """
    prompt = config.build_prompt(
        conflict_region=conflict_region,
        **kwargs,
    )

    response = gemini_client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
    )
    if not response.text:
        raise Exception("No response from Gemini API")

    return response.text.strip().upper() == "YES"


def classify_conflict_region(**kwargs: str | None) -> config.ConflictCountry | None:
    """
    Use LLM to classify which conflict region (if any) a Short is about.
    Returns the conflict country name or None if not related to any conflict.
    """
    prompt = config.build_classify_prompt(**kwargs)

    response = gemini_client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
    )
    if not response.text:
        raise Exception("No response from Gemini API")

    result = response.text.strip().upper()
    
    # Map response to ConflictCountry or None
    conflict_map: dict[str, config.ConflictCountry] = {
        "PALESTINE": "Palestine",
        "MYANMAR": "Myanmar",
        "UKRAINE": "Ukraine",
        "MEXICO": "Mexico",
        "BRAZIL": "Brazil",
    }
    
    return conflict_map.get(result, None)

