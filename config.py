"""
Configuration for YouTube Shorts feed capture.
"""
from pathlib import Path

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

# === RATE LIMITS ===
# YouTube is more lenient, but still be reasonable
MAX_SESSIONS_PER_DAY = 1000
MIN_HOURS_BETWEEN_SESSIONS = 0

# === CAPTURE SETTINGS ===
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 900

# Output directories
OUTPUT_DIR = Path("./data")
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
HTML_DIR = OUTPUT_DIR / "html"
LOGS_DIR = OUTPUT_DIR / "logs"

# === YOUTUBE URLs ===
YOUTUBE_SHORTS_URL = "https://www.youtube.com/shorts/LRBvm_hQKqE"

# === SAFETY FLAGS ===
# Set to True to enable headless mode (not recommended)
HEADLESS = False

# Set to True to disable images (faster but changes layout)
DISABLE_IMAGES = False
