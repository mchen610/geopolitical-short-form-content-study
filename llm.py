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

