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

CONFLICT_URLS: dict[ConflictCountry, list[str]] = {
    "Palestine": [
        "https://www.youtube.com/shorts/N0wEdL-zqII",
        "https://www.youtube.com/shorts/UA-JQgGO8M8",
        "https://www.youtube.com/shorts/nZOyQROIh3A",
        "https://www.youtube.com/shorts/Bhj_06yu2Gw",
        "https://www.youtube.com/shorts/peBHAQNk7p4",
        "https://www.youtube.com/shorts/3VYfJMZgV3o",
        "https://www.youtube.com/shorts/Fn9vUh-yHsY",
        "https://www.youtube.com/shorts/VnKNiHm6lA0",
        "https://www.youtube.com/shorts/PEENUVaoWF8",
        "https://www.youtube.com/shorts/5MZv4TrjFr8"
    ],
    "Myanmar": [
        "https://www.youtube.com/shorts/rF2WN41oXHw",
        "https://www.youtube.com/shorts/ZdaLsOdoMTY",
        "https://www.youtube.com/shorts/9Hrff1T8o2U",
        "https://www.youtube.com/shorts/vl-sUJKpzLU",
        "https://www.youtube.com/shorts/37iWZl4r3xs",
        "https://www.youtube.com/shorts/AIyDCIGRiQ4",
        "https://www.youtube.com/shorts/N1YBMHUTA-s",
        "https://www.youtube.com/shorts/h2RRJjrsXfQ",
        "https://www.youtube.com/shorts/MYZHYvtBZ7M"
    ],
    "Ukraine": [
        "https://www.youtube.com/shorts/gmQ5T1xCdtM",
        "https://www.youtube.com/shorts/cSWy6m7fFa4",
        "https://www.youtube.com/shorts/ifcfeyjNm7U",
        "https://www.youtube.com/shorts/ooEzgr2H4UA",
        "https://www.youtube.com/shorts/RSXcoY_uORY",
        "https://www.youtube.com/shorts/wHExn_r6FaA",
        "https://www.youtube.com/shorts/tx2TA-9Hlh0",
        "https://www.youtube.com/shorts/EiEnImaMKVY",
        "https://www.youtube.com/shorts/gxYrAKfcU2g",
        "https://www.youtube.com/shorts/Lo4a7BKnwbM"
    ],
    "Mexico": [
        "https://www.youtube.com/shorts/VDhVJhSg1LA",
        "https://www.youtube.com/shorts/P-PySJSsUXQ",
        "https://www.youtube.com/shorts/QNYoxdVFnmI",
        "https://www.youtube.com/shorts/0BHWu8CzwEk",
        "https://www.youtube.com/shorts/hGOQbnt9r_o",
        "https://www.youtube.com/shorts/mUzIhnQEW90",
        "https://www.youtube.com/shorts/WzWhYgDFsJs",
        "https://www.youtube.com/shorts/oOxdW3MUKMI",
        "https://www.youtube.com/shorts/y-NZRWmhMkg"
    ],
    "Brazil": [
        "https://www.youtube.com/shorts/r4RRtBWMCXA",
        "https://www.youtube.com/shorts/r4RRtBWMCXA",
        "https://www.youtube.com/shorts/r4RRtBWMCXA",
        "https://www.youtube.com/shorts/PAqvULOfze8",
        "https://www.youtube.com/shorts/PAqvULOfze8",
        "https://www.youtube.com/shorts/PAqvULOfze8",
        "https://www.youtube.com/shorts/YJydcu2qp_8",
        "https://www.youtube.com/shorts/YJydcu2qp_8",
        "https://www.youtube.com/shorts/YJydcu2qp_8",
        "https://www.youtube.com/shorts/9kRqoe4-l8U",
        "https://www.youtube.com/shorts/9kRqoe4-l8U",
        "https://www.youtube.com/shorts/9kRqoe4-l8U",
        "https://www.youtube.com/shorts/ljB_2HESmHs",
        "https://www.youtube.com/shorts/Z5_K9FJrGrQ",
        "https://www.youtube.com/shorts/Z5_K9FJrGrQ",
        "https://www.youtube.com/shorts/Z5_K9FJrGrQ",
        "https://www.youtube.com/shorts/R-yxoWiDz8w",
        "https://www.youtube.com/shorts/RBwtXgs-NGE",
        "https://www.youtube.com/shorts/RBwtXgs-NGE",
        "https://www.youtube.com/shorts/RBwtXgs-NGE",
        "https://www.youtube.com/shorts/6ZIA5G78FuU",
        "https://www.youtube.com/shorts/6ZIA5G78FuU",
        "https://www.youtube.com/shorts/6ZIA5G78FuU",
        "https://www.youtube.com/shorts/gjKrsAprFYk",
        "https://www.youtube.com/shorts/gjKrsAprFYk",
        "https://www.youtube.com/shorts/gjKrsAprFYk"
    ],
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


def build_classify_prompt(**kwargs: str | None) -> str:
    """Build prompt for multi-class conflict classification."""
    details = "\n".join(f"{key.capitalize()}: {value}" for key, value in kwargs.items())
    
    # Build keywords section for all conflicts
    all_keywords = []
    for country, keywords in CONFLICT_KEYWORDS.items():
        kw_list = ", ".join(keywords)
        all_keywords.append(f"- {country}: {kw_list}")
    keywords_section = "\n".join(all_keywords)
    
    return f"""You are classifying which geopolitical conflict (if any) a YouTube Short is about.

<video_details>
{details}
</video_details>

<conflicts>
{keywords_section}
</conflicts>

If this video is about one of these conflicts, respond with ONLY the country name (Palestine, Myanmar, Ukraine, Mexico, or Brazil).
If this video is NOT about any of these conflicts, respond with ONLY "NONE".

Your response must be exactly one of: PALESTINE, MYANMAR, UKRAINE, MEXICO, BRAZIL, or NONE."""

# === ACCOUNT DEFINITIONS ===
# Each account gets a dedicated profile in ./chrome_profiles/
# Run --setup to log in for the first time


# Balanced Latin Square: each country appears exactly once at each position
# This eliminates order effects as a confounding variable
ACCOUNT_COUNTRY_ORDER: dict[str, list[ConflictCountry]] = {
    "test": ["Palestine", "Myanmar", "Ukraine", "Mexico", "Brazil"],
    "profile_1": ["Palestine", "Myanmar", "Ukraine", "Mexico", "Brazil"],
    "profile_2": ["Myanmar", "Ukraine", "Mexico", "Brazil", "Palestine"],
    "profile_3": ["Ukraine", "Mexico", "Brazil", "Palestine", "Myanmar"],
    "profile_4": ["Mexico", "Brazil", "Palestine", "Myanmar", "Ukraine"],
    "profile_5": ["Brazil", "Palestine", "Myanmar", "Ukraine", "Mexico"],
}

ACCOUNTS = set(ACCOUNT_COUNTRY_ORDER.keys())

# Number of sessions to run per country (5 sessions * 15 shorts = 75 shorts per country)
SESSIONS_PER_COUNTRY = 5

# === TIMING CONTROLS ===
# All times in seconds

# Number of Shorts to view per session
# Each scroll = 1 Short viewed
SHORTS_PER_SESSION = 20

# === PHASE 2: HOME FEED MEASUREMENT ===
# After training, we measure what YouTube shows in the general home feed
HOME_SESSIONS = 10
HOME_SHORTS_PER_SESSION = 50
HOME_VIEW_TIME = 3.0  # seconds per short (no engagement, just observe)

# === BROWSER SETTINGS ===
VIEWPORT_WIDTH = 800
VIEWPORT_HEIGHT = 900

# Output directory for session JSON files
OUTPUT_DIR = Path("./data")