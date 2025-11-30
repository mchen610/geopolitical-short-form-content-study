"""
Configuration for YouTube Shorts feed capture.
"""
from pathlib import Path

# === LLM SETTINGS ===
# Set your Google API key in environment variable GOOGLE_API_KEY
GEMINI_MODEL = "gemini-2.0-flash"  # Fast and cheap

# What content should we like?
TOPIC = "Israel-Palestine conflict"

# Topic: [...keywords]
CONFLICT_MAP = {
    "Israel-Palestine conflict": [
        "Israel",
        "Palestine",
        "West Bank",
        "Gaza",
        "Hamas",
        "IDF",
    ],
}


def generate_prompt(*, topic: str, title: str, channel: str) -> str:
    """Generate an LLM prompt to determine if video content is related to a topic."""
    keywords = CONFLICT_MAP.get(topic)
    if not keywords:
        raise ValueError(f"No keywords defined for topic: {topic}")
    
    keywords_list = "\n".join(f"- {kw}" for kw in keywords)
    
    return f"""Analyze these video details and determine if it's related to the topic.

<topic>
{topic}
</topic>

Consider as RELATED if mentions any of the following:
{keywords_list}

Video Title: {title}
Channel: {channel}

Respond with ONLY "YES" or "NO"."""

# === ACCOUNT DEFINITIONS ===
# Each account gets a dedicated profile in ./chrome_profiles/
# Run --setup to log in for the first time

ACCOUNTS = {
    "neutral_1": {
        "description": "No interests set, no engagement"
    },
}

# === TIMING CONTROLS ===
# All times in seconds

# Initial page load wait
PAGE_LOAD_WAIT_MIN = 3
PAGE_LOAD_WAIT_MAX = 5

# Delay between scrolls (simulating watching a Short)
# Shorts are typically 15-60 seconds, so we simulate partial watching
SCROLL_DELAY_MIN = 4.0
SCROLL_DELAY_MAX = 12.0

# Number of Shorts to view per session
# Each scroll = 1 Short viewed
SHORTS_PER_SESSION = 50

# Total session time limit (seconds) - fail-safe
MAX_SESSION_DURATION = 600  # 10 minutes max

# === BROWSER SETTINGS ===
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 900

# Output directory for session JSON files
OUTPUT_DIR = Path("./data")

# This is an israel v palestine conflict related short. We wanna start here
YOUTUBE_SHORTS_URL = "https://www.youtube.com/shorts/LRBvm_hQKqE"
