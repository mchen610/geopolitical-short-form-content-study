"""
Configuration for YouTube Shorts feed capture.
"""
from pathlib import Path
from typing import Literal

# === LLM SETTINGS ===
# Set your Google API key in environment variable GOOGLE_API_KEY
GEMINI_MODEL = "gemini-2.0-flash"  # Fast and cheap

# Type for the 5 conflict countries we study
ConflictCountry = Literal["Palestine", "Myanmar", "Ukraine", "Mexico", "Brazil"]

# What content should we like?
TOPIC: ConflictCountry = "Palestine"

# Conflict severity scores (ACLED Conflict Index, December 2024)
CONFLICT_SCORE_MAP: dict[ConflictCountry, float] = {
    "Palestine": 2.571,
    "Myanmar": 1.9,      # Rank 2, Extreme
    "Ukraine": 1.543,    # Rank 14, High
    "Mexico": 1.045,     # Rank 4, Extreme
    "Brazil": 0.785,     # Rank 6, Extreme
}

# Topic: [...keywords]
CONFLICT_MAP: dict[ConflictCountry, list[str]] = {
    "Palestine": [
        "gaza strip bombardment",
        "rafah invasion",
        "khan younis fighting",
        "idf gaza operation",
        "al-shifa hospital raid",
        "jabalia strikes",
        "unrwa shelters hit",
        "west bank settler attacks",
        "jenin camp raid",
        "palestinian displacement west bank"
    ],

    "Myanmar": [
        "tatmadaw offensive",
        "people’s defense force ambush",
        "arakan army advance",
        "rakhine state fighting",
        "sagaing resistance",
        "chinland defense force",
        "myanmar village airstrike",
        "karen national union clashes",
        "military junta naypyidaw",
        "rohingya villages burned"
    ],

    "Ukraine": [
        "kharkiv front",
        "bakhmut trenches",
        "avdiivka assault",
        "donetsk shelling",
        "zaporizhzhia line",
        "crimea strikes",
        "shahed drone barrage",
        "himars strikes ukraine",
        "russian mobilization ukraine",
        "black sea fleet attacks"
    ],

    "Mexico": [
        "cjng vs sinaloa clashes",
        "michoacan convoy ambush",
        "cartel roadblocks",
        "narco drone attack",
        "tamaulipas shootout",
        "gulf cartel execution",
        "plaza takeover cartel",
        "levantan a",
        "military vs cartel firefight",
        "culiacanazo operation"
    ],

    "Brazil": [
        "pcc prison uprising",
        "rio favela police raid",
        "complexo do alemao operation",
        "milicia territory dispute",
        "amazon illegal mining gangs",
        "yanomami land invasion",
        "para rural land conflict",
        "comando vermelho shootout",
        "pcc retaliation sao paulo",
        "amazon defenders attacked"
    ]
}


def generate_prompt(*, topic: ConflictCountry, **kwargs: str | None) -> str:
    """Generate an LLM prompt to determine if video content is related to a topic."""
    keywords = CONFLICT_MAP.get(topic)
    if not keywords:
        raise ValueError(f"No keywords defined for topic: {topic}")
    
    keywords_list = "\n".join(f"- {kw}" for kw in keywords)
    details = "\n".join(f"{key.capitalize()}: {value}" for key, value in kwargs.items())
    
    return f"""Analyze these video details and determine if it's related to the topic.

<topic>
{topic}
</topic>

Consider as RELATED if mentions any of the following:
{keywords_list}

{details}

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
SCROLL_DELAY_MAX = 6.0

# Number of Shorts to view per session
# Each scroll = 1 Short viewed
SHORTS_PER_SESSION = 50

# Total session time limit (seconds) - fail-safe
MAX_SESSION_DURATION = 6000

# === BROWSER SETTINGS ===
VIEWPORT_WIDTH = 800
VIEWPORT_HEIGHT = 900

# Output directory for session JSON files
OUTPUT_DIR = Path("./data")

# This is an israel v palestine conflict related short. We wanna start here
YOUTUBE_SHORTS_URL = "https://www.youtube.com/shorts/LRBvm_hQKqE"
