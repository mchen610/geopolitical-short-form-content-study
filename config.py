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

# Conflict severity scores (ACLED Conflict Index, December 2024)
CONFLICT_SCORE_MAP: dict[ConflictCountry, float] = {
    "Palestine": 2.571,
    "Myanmar": 1.9,      # Rank 2, Extreme
    "Ukraine": 1.543,    # Rank 14, High
    "Mexico": 1.045,     # Rank 4, Extreme
    "Brazil": 0.785,     # Rank 6, Extreme
}

# Conflict region -> search keywords for identifying related content
CONFLICT_KEYWORDS: dict[ConflictCountry, list[str]] = {
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

CONFLICT_URLS: dict[ConflictCountry, str] = {
    "Palestine": "https://www.youtube.com/shorts/748bcs7b_Zk",
    "Myanmar": "https://www.youtube.com/shorts/Ero5GvpR4ng",
    "Ukraine": "https://www.youtube.com/shorts/hb1YZBBGeGY",
    "Mexico": "https://www.youtube.com/shorts/VDhVJhSg1LA",
    "Brazil": "https://www.youtube.com/shorts/9kRqoe4-l8U",

}


def build_prompt(*, conflict_region: ConflictCountry, **kwargs: str | None) -> str:
    keywords = CONFLICT_KEYWORDS[conflict_region]
    keywords_list = "\n".join(f"- {kw}" for kw in keywords)
    details = "\n".join(f"{key.capitalize()}: {value}" for key, value in kwargs.items())
    
    return f"""You are classifying whether a YouTube Short is related to a given conflict in a given region.

<video_details>
{details}
</video_details>

The video is RELATED if it covers any of these related to the conflict region {conflict_region}:
{keywords_list}


Respond with ONLY "YES" or "NO"."""

# === ACCOUNT DEFINITIONS ===
# Each account gets a dedicated profile in ./chrome_profiles/
# Run --setup to log in for the first time


# Random country order for each account (pre-generated)
# Each account sees all 5 countries in a different random order
ACCOUNT_COUNTRY_ORDER: dict[str, list[ConflictCountry]] = {
    "test": ["Brazil", "Ukraine", "Palestine", "Mexico", "Myanmar"],
    "profile_1": ["Brazil", "Ukraine", "Palestine", "Mexico", "Myanmar"],
    "profile_2": ["Myanmar", "Mexico", "Brazil", "Ukraine", "Palestine"],
    "profile_3": ["Ukraine", "Palestine", "Myanmar", "Brazil", "Mexico"],
    "profile_4": ["Mexico", "Brazil", "Ukraine", "Myanmar", "Palestine"],
    "profile_5": ["Palestine", "Myanmar", "Mexico", "Ukraine", "Brazil"],
}

ACCOUNTS = set(ACCOUNT_COUNTRY_ORDER.keys())

# Number of sessions to run per country (5 sessions * 15 shorts = 75 shorts per country)
SESSIONS_PER_COUNTRY = 5

# === TIMING CONTROLS ===
# All times in seconds

# Initial page load wait
PAGE_LOAD_WAIT_MIN = 3
PAGE_LOAD_WAIT_MAX = 5

# Delay between scrolls (simulating watching a Short)
# Shorts are typically 15-60 seconds, so we simulate partial watching
SCROLL_DELAY_MIN = 15.0
SCROLL_DELAY_MAX = 30.0

# Number of Shorts to view per session
# Each scroll = 1 Short viewed
SHORTS_PER_SESSION = 15

# === BROWSER SETTINGS ===
VIEWPORT_WIDTH = 800
VIEWPORT_HEIGHT = 900

# Output directory for session JSON files
OUTPUT_DIR = Path("./data")