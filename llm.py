import os

from dotenv import load_dotenv
from google import genai
import config

# Load environment variables from .env file
load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


def is_conflict_related(*, title: str, channel: str) -> bool:
    """
    Use LLM to determine if the Short is related to Israel-Palestine conflict.
    """
    prompt = config.generate_prompt(  # noqa: F821
        topic=config.TOPIC,
        title=title,
        channel=channel,
    )

    response = gemini_client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
    )
    if not response.text:
        raise Exception("No response from Gemini API")

    return response.text.strip().upper() == "YES"

