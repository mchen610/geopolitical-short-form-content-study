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
# Each account gets a dedicated profile in ./chrome_profiles/
# Run --setup to log in for the first time

ACCOUNTS = {
    "neutral_1": {
        "description": "No interests set, no engagement"
    },
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

# This is an israel v palestine conflict related short. We wanna start here
YOUTUBE_SHORTS_URL = "https://www.youtube.com/shorts/LRBvm_hQKqE"
