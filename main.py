"""
YouTube Shorts Feed Capture - Observation Only

SAFETY MEASURES:
- Uses undetected-chromedriver to avoid bot detection
- Uses your real, manually-logged-in Chrome profile
- Human-like random delays between swipes
- Conservative view limits
- No engagement automation whatsoever

BEFORE RUNNING:
1. pip install -r requirements.txt
2. Create a new Chrome profile and manually log into YouTube/Google
3. Update config.py with your profile directory
4. Close Chrome completely (important!)
5. Run: python capture_youtube_shorts.py --account neutral_1
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai  # type: ignore[import-untyped]
import undetected_chromedriver as uc  # type: ignore[import-untyped]
from selenium.common.exceptions import WebDriverException

import config
from utils import human_delay
from youtube import (
    extract_current_short_metadata,
    swipe_to_next_short,
    wait_for_shorts_load,
)

# Load environment variables from .env file
load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Directory for this script's dedicated Chrome profiles
CHROME_PROFILES_DIR = Path("./chrome_profiles")


def setup_directories():
    """Create output directory if it doesn't exist."""
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    CHROME_PROFILES_DIR.mkdir(exist_ok=True)


def kill_chrome_processes():
    """Kill any lingering Chrome processes that might lock profiles."""
    print("🔪 Killing any lingering Chrome processes...")
    try:
        # macOS/Linux
        subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
        subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
        time.sleep(2)  # Give processes time to die
    except Exception:
        pass  # Ignore errors on Windows or if pkill not found


def create_driver(account_id: str, setup_mode: bool = False):
    """
    Create an undetected Chrome driver with a dedicated profile for this account.
    """
    account = config.ACCOUNTS.get(account_id)
    if not account:
        raise ValueError(f"Unknown account: {account_id}. Check config.py")
    
    # Kill any lingering Chrome first
    kill_chrome_processes()
    
    # Use dedicated profile directory for this script
    profile_path = CHROME_PROFILES_DIR / account_id
    
    if not profile_path.exists() and not setup_mode:
        print(f"❌ Profile not set up for account: {account_id}")
        print(f"   Run: python main.py --account {account_id} --setup")
        raise ValueError("Profile not set up. Run with --setup first.")
    
    
    options = uc.ChromeOptions()
    
    # Use dedicated profile directory
    options.add_argument(f"--user-data-dir={profile_path.absolute()}")
    
    # Window size
    options.add_argument(f"--window-size={config.VIEWPORT_WIDTH},{config.VIEWPORT_HEIGHT}")
    
    # Disable notifications
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    try:
        driver = uc.Chrome(options=options, version_main=None)
        driver.set_window_size(config.VIEWPORT_WIDTH, config.VIEWPORT_HEIGHT)
        return driver
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")
        print("\n⚠️  Make sure Chrome is completely closed (pkill -f chrome)")
        raise


def is_conflict_related(metadata: dict) -> bool:
    """
    Use LLM to determine if the Short is related to Israel-Palestine conflict.
    Returns (is_related, reasoning).
    """
    title = metadata.get("title")

    if not title:
        raise ValueError(f"No title found: {metadata}")

    channel = metadata.get("channel", "No channel found")
    
    prompt = config.generate_prompt(
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


def view_shorts(driver, count: int) -> list[dict]:
    """
    View multiple Shorts, capturing metadata for each.
    Returns list of Short metadata.
    """
    shorts_data = []
    start_time = time.time()
    
    for i in range(count):
        # Check session time limit
        elapsed = time.time() - start_time
        if elapsed > config.MAX_SESSION_DURATION:
            print(f"⚠️  Session time limit reached ({config.MAX_SESSION_DURATION}s)")
            break
        
        # Extract metadata for current Short
        metadata = extract_current_short_metadata(driver)
        metadata["view_index"] = i + 1
        
        title = metadata.get("title", "")[:50] or "(no title)"
        print(f"   Short {i + 1}/{count} - {title}")
        
        # Analyze with LLM and like if conflict-related
        is_related = is_conflict_related(metadata)
        metadata["is_conflict_related"] = is_related
        
        shorts_data.append(metadata)
        
        # Human-like viewing delay (watching the Short)
        human_delay(config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX)
        
        # Occasionally watch longer (like rewatching or reading comments)
        if random.random() < 0.1:  # 10% chance
            extra_delay = human_delay(3.0, 8.0)
            print(f"   ... watching longer ({extra_delay:.1f}s)")
        
        # Swipe to next Short (except for last one)
        if i < count - 1:
            if not swipe_to_next_short(driver):
                print("   Failed to swipe, retrying...")
                human_delay(1, 2)
                swipe_to_next_short(driver)
            
            # Small delay after swipe for video to load
            human_delay(0.5, 1.5)
    
    return shorts_data


def save_session(account_id: str, session_id: str, shorts_data: list[dict]):
    """Save session data as a simple JSON file."""
    # Clean up the shorts data to just what we need
    clean_data = []
    for short in shorts_data:
        clean_data.append({
            "video_id": short.get("video_id"),
            "url": short.get("url"),
            "title": short.get("title"),
            "channel": short.get("channel"),
            "is_conflict_related": short.get("is_conflict_related", False),
            "liked": short.get("liked", False),
        })
    
    session_file = config.OUTPUT_DIR / f"session_{account_id}_{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(clean_data, f, indent=2)
    print(f"📝 Session saved: {session_file}")


def run_capture_session(account_id: str, dry_run: bool = False):
    """
    Run a single Shorts capture session for the given account.
    """
    print("\n" + "=" * 60)
    print(f"🎬 YouTube Shorts Capture - Account: {account_id}")
    print("=" * 60)
    
    # Validate account
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        print(f"   Available accounts: {list(config.ACCOUNTS.keys())}")
        return False
    
    
    if dry_run:
        print("\n🧪 DRY RUN - Will open browser but not save data")
    
    # Generate session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    driver = None
    success = False
    
    try:
        # Setup
        setup_directories()
        driver = create_driver(account_id)
        
        print("\n📱 Loading YouTube Shorts...")
        driver.get(config.YOUTUBE_SHORTS_URL)
        
        # Wait for page with human-like delay
        human_delay(config.PAGE_LOAD_WAIT_MIN, config.PAGE_LOAD_WAIT_MAX)
        
        if not wait_for_shorts_load(driver):
            print("❌ Shorts failed to load properly")
            return False
        
        print("✅ Shorts loaded!")
        
        # View Shorts
        print(f"\n🎬 Viewing Shorts ({config.SHORTS_PER_SESSION} videos)...")
        shorts_data = view_shorts(driver, config.SHORTS_PER_SESSION)
        
        # Save session
        if not dry_run:
            save_session(account_id, session_id, shorts_data)
        
        # Count likes
        liked_count = sum(1 for s in shorts_data if s.get("liked"))
        
        print("\n" + "=" * 60)
        print("✅ Session complete!")
        print(f"   Shorts viewed: {len(shorts_data)}")
        print(f"   Liked: {liked_count}")
        print("=" * 60)
        
        success = True
        
    except WebDriverException as e:
        print(f"\n❌ Browser error: {e}")
        print("\n⚠️  Tips:")
        print("   - Make sure Chrome is completely closed")
        print("   - Check that the profile directory exists")
        print("   - Try running Chrome manually first to ensure profile works")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\n🔒 Closing browser...")
            print("View liked photos at: https://www.youtube.com/playlist?list=LL")
            try:
                driver.quit()
            except Exception:
                pass
    
    return success


def run_setup(account_id: str):
    """Open browser for manual YouTube login. Profile is saved for future sessions."""
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    print(f"\n🔧 SETUP: Log into YouTube for account '{account_id}'")
    print("   1. Browser will open")
    print("   2. Log into YouTube/Google")
    print("   3. Close browser when done")
    
    setup_directories()
    driver = None
    try:
        driver = create_driver(account_id, setup_mode=True)
        driver.get("https://www.youtube.com")
        
        print("\n✅ Browser open - log in now, then close the browser")
        
        # Wait for browser to close
        while True:
            try:
                _ = driver.current_url
                time.sleep(1)
            except Exception:
                break
        
        print("✅ Setup complete!")
        return True
    except KeyboardInterrupt:
        print("\n⚠️  Aborted")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Capture YouTube Shorts feed and like conflict-related content",
        epilog="First run: python main.py --account neutral_1 --setup"
    )
    
    parser.add_argument("--account", "-a", help="Account ID from config.py")
    parser.add_argument("--setup", "-s", action="store_true", help="Setup: log into YouTube")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't save data")
    parser.add_argument("--list-accounts", "-l", action="store_true", help="List accounts")
    
    args = parser.parse_args()
    
    if args.list_accounts:
        print("\nAccounts:")
        for acc_id, acc_info in config.ACCOUNTS.items():
            profile_path = CHROME_PROFILES_DIR / acc_id
            status = "✅" if profile_path.exists() else "❌ needs --setup"
            print(f"  {acc_id}: {status}")
        return
    
    if not args.account:
        parser.print_help()
        print("\n❌ --account required")
        sys.exit(1)
    
    if args.setup:
        success = run_setup(args.account)
        sys.exit(0 if success else 1)
    
    success = run_capture_session(args.account, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

