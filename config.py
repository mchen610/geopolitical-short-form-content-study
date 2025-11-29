"""
Configuration for YouTube Shorts feed capture.
"""
from pathlib import Path

# === LLM SETTINGS ===
# Set your Google API key in environment variable GOOGLE_API_KEY
GEMINI_MODEL = "gemini-2.0-flash"  # Fast and cheap

# What content should we like?
CONFLICT_PROMPT = """Analyze this YouTube Short and determine if it's related to the Israel-Palestine conflict.

Video Title: {title}
Channel: {channel}
Description: {description}

Consider as RELATED:
- Direct conflict content (IDF, Hamas, Gaza, West Bank, etc.)
- Israeli or Palestinian politics
- Middle East conflict news/commentary
- Pro-Israel or pro-Palestine content
- Related protests or activism

Consider as NOT RELATED:
- General Middle East content not about the conflict
- Unrelated news or entertainment
- Travel/food content from the region (unless political)

Respond with ONLY "YES" or "NO"."""

# === ACCOUNT DEFINITIONS ===
# Each account gets its own Chrome profile in ./chrome_profiles/
# 
# Setup steps:
# 1. Run: python capture_youtube_shorts.py --account <name> --setup
# 2. Log into YouTube in the browser that opens
# 3. Close the browser
# 4. Now you can run captures: python capture_youtube_shorts.py --account <name>

ACCOUNTS = {
    "neutral_1": {
        "cohort": "cold_start_neutral",
        "description": "No interests set, no engagement"
    },
    # Add more accounts:
    # "neutral_2": {
    #     "cohort": "cold_start_neutral",
    #     "description": "Second neutral account"
    # },
    # "engaged_1": {
    #     "cohort": "light_engagement",
    #     "description": "Will like some conflict-related content"
    # },
}

# === TIMING CONTROLS ===
# YouTube is less aggressive than Instagram, but still be careful
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

# Starting URL (any Shorts URL works, it will scroll from there)
YOUTUBE_SHORTS_URL = "https://www.youtube.com/shorts"
