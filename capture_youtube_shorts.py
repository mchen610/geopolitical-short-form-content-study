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
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import undetected_chromedriver as uc  # type: ignore[import-untyped]
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

import config


# Directory for this script's dedicated Chrome profiles
SCRIPT_PROFILES_DIR = Path("./chrome_profiles")


def setup_directories():
    """Create output directories if they don't exist."""
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    config.SCREENSHOTS_DIR.mkdir(exist_ok=True)
    config.HTML_DIR.mkdir(exist_ok=True)
    config.LOGS_DIR.mkdir(exist_ok=True)


def check_rate_limit(account_id: str) -> bool:
    """
    Check if we're within rate limits for this account.
    Returns True if OK to proceed, False if we should wait.
    """
    session_log_path = config.LOGS_DIR / f"sessions_{account_id}.jsonl"
    
    if not session_log_path.exists():
        return True
    
    today = datetime.now().date()
    sessions_today = 0
    last_session_time = None
    
    with open(session_log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                session_date = datetime.fromisoformat(entry["started_at"]).date()
                session_time = datetime.fromisoformat(entry["started_at"])
                
                if session_date == today:
                    sessions_today += 1
                
                if last_session_time is None or session_time > last_session_time:
                    last_session_time = session_time
            except (json.JSONDecodeError, KeyError):
                continue
    
    # Check daily limit
    if sessions_today >= config.MAX_SESSIONS_PER_DAY:
        print(f"⚠️  Rate limit: Already ran {sessions_today} sessions today for {account_id}")
        print(f"   Max allowed: {config.MAX_SESSIONS_PER_DAY} per day")
        return False
    
    # Check time between sessions
    if last_session_time:
        hours_since_last = (datetime.now() - last_session_time).total_seconds() / 3600
        if hours_since_last < config.MIN_HOURS_BETWEEN_SESSIONS:
            print(f"⚠️  Rate limit: Only {hours_since_last:.1f} hours since last session")
            print(f"   Minimum wait: {config.MIN_HOURS_BETWEEN_SESSIONS} hours")
            return False
    
    return True


def human_delay(min_sec: float, max_sec: float):
    """Sleep for a random duration to simulate human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


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


def get_profile_path(account_id: str) -> Path:
    """Get the dedicated profile path for an account."""
    SCRIPT_PROFILES_DIR.mkdir(exist_ok=True)
    return SCRIPT_PROFILES_DIR / account_id


def create_driver(account_id: str, setup_mode: bool = False):
    """
    Create an undetected Chrome driver with the account's profile.
    
    Uses a dedicated profile directory for this script to avoid
    conflicts with your regular Chrome browser.
    """
    account = config.ACCOUNTS.get(account_id)
    if not account:
        raise ValueError(f"Unknown account: {account_id}. Check config.py")
    
    # Kill any lingering Chrome first
    kill_chrome_processes()
    
    # Use dedicated profile directory for this script
    profile_path = get_profile_path(account_id)
    
    if not profile_path.exists() and not setup_mode:
        print(f"❌ Profile not set up for account: {account_id}")
        print("   Run with --setup first to log in:")
        print(f"   python capture_youtube_shorts.py --account {account_id} --setup")
        raise ValueError("Profile not set up. Run with --setup first.")
    
    print(f"🔧 Using profile directory: {profile_path}")
    
    options = uc.ChromeOptions()
    
    # Use our dedicated profile directory (not Chrome's main one)
    options.add_argument(f"--user-data-dir={profile_path.absolute()}")
    
    # Window size for consistent screenshots
    options.add_argument(f"--window-size={config.VIEWPORT_WIDTH},{config.VIEWPORT_HEIGHT}")
    
    # Disable notifications (reduces popups)
    options.add_argument("--disable-notifications")
    
    # Disable automation flags that might be detected
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Mute audio (Shorts auto-play with sound)
    options.add_argument("--mute-audio")
    
    # Disable first run experience
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    if config.HEADLESS and not setup_mode:
        options.add_argument("--headless=new")
    
    if config.DISABLE_IMAGES:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
    
    try:
        driver = uc.Chrome(options=options, version_main=None)
        driver.set_window_size(config.VIEWPORT_WIDTH, config.VIEWPORT_HEIGHT)
        return driver
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")
        print("\n⚠️  Troubleshooting:")
        print("   1. Make sure Chrome is completely closed")
        print("   2. Check Activity Monitor for 'chrome' or 'Google Chrome' processes")
        print("   3. Try: pkill -f chrome")
        raise


def wait_for_shorts_load(driver, timeout: int = 30) -> bool:
    """
    Wait for YouTube Shorts to load.
    Returns True if loaded, False if error.
    """
    try:
        # Wait for Shorts player to appear
        # YouTube Shorts uses a specific player element
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-shorts, ytd-reel-video-renderer, #shorts-player"))
        )
        
        # Additional wait for video to actually load
        human_delay(2, 3)
        
        return True
        
    except TimeoutException:
        print("❌ Timeout waiting for Shorts to load")
        # Check if we're on a different page
        if "youtube.com" not in driver.current_url:
            print("   Not on YouTube - check if logged in")
        return False


def extract_current_short_metadata(driver) -> dict:
    """
    Extract metadata from the currently visible Short.
    """
    metadata = {
        "url": driver.current_url,
        "extracted_at": datetime.now().isoformat(),
    }
    
    try:
        # Try to get video title
        title_selectors = [
            "h2.title",
            "yt-formatted-string.title",
            "#title",
            "[id*='title']"
        ]
        for selector in title_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and len(text) > 3:
                    metadata["title"] = text
                    break
            if "title" in metadata:
                break
    except Exception:
        pass
    
    try:
        # Try to get channel name
        channel_selectors = [
            "ytd-channel-name a",
            "#channel-name a",
            ".ytd-channel-name",
            "[id*='channel'] a"
        ]
        for selector in channel_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and text.startswith("@"):
                    metadata["channel"] = text
                    break
                elif text and len(text) > 1:
                    metadata["channel"] = text
                    break
            if "channel" in metadata:
                break
    except Exception:
        pass
    
    try:
        # Try to get description/caption
        desc_selectors = [
            "yt-formatted-string#description",
            ".description",
            "#description"
        ]
        for selector in desc_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text:
                    metadata["description"] = text[:500]  # Limit length
                    break
            if "description" in metadata:
                break
    except Exception:
        pass
    
    # Extract video ID from URL
    url = driver.current_url
    if "/shorts/" in url:
        video_id = url.split("/shorts/")[-1].split("?")[0].split("/")[0]
        metadata["video_id"] = video_id
    
    return metadata


def swipe_to_next_short(driver) -> bool:
    """
    Swipe/scroll to the next Short.
    Returns True if successful.
    """
    try:
        # Method 1: Press Down arrow or J key (YouTube shortcut)
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ARROW_DOWN)
        return True
    except Exception as e:
        print(f"   Swipe failed: {e}")
        return False


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
        shorts_data.append(metadata)
        
        video_id = metadata.get("video_id", "unknown")
        channel = metadata.get("channel", "unknown")
        print(f"   Short {i + 1}/{count} - {video_id} by {channel}")
        
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


def capture_page(driver, account_id: str, session_id: str, suffix: str = "") -> dict:
    """
    Capture screenshot and HTML of the current page state.
    Returns paths to saved files.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Screenshot
    screenshot_name = f"yt_{account_id}_{session_id}_{timestamp}{suffix}.png"
    screenshot_path = config.SCREENSHOTS_DIR / screenshot_name
    driver.save_screenshot(str(screenshot_path))
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # HTML
    html_name = f"yt_{account_id}_{session_id}_{timestamp}{suffix}.html"
    html_path = config.HTML_DIR / html_name
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"   📄 HTML: {html_path}")
    
    return {
        "screenshot": str(screenshot_path),
        "html": str(html_path),
        "captured_at": datetime.now().isoformat(),
    }


def log_session(account_id: str, session_data: dict):
    """Append session data to the account's session log."""
    log_path = config.LOGS_DIR / f"sessions_{account_id}.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(session_data) + "\n")
    print(f"📝 Session logged: {log_path}")


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
    
    account = config.ACCOUNTS[account_id]
    print(f"   Cohort: {account['cohort']}")
    print(f"   Profile: {get_profile_path(account_id)}")
    
    # Check rate limits
    if not dry_run and not check_rate_limit(account_id):
        print("\n⛔ Skipping session due to rate limits")
        return False
    
    if dry_run:
        print("\n🧪 DRY RUN - Will open browser but not save data")
    
    # Generate session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_start = datetime.now()
    
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
        
        # Initial capture
        print("\n📸 Capturing initial state...")
        captures = []
        if not dry_run:
            captures.append(capture_page(driver, account_id, session_id, "_start"))
        
        # View Shorts
        print(f"\n🎬 Viewing Shorts ({config.SHORTS_PER_SESSION} videos)...")
        shorts_data = view_shorts(driver, config.SHORTS_PER_SESSION)
        
        # Final capture
        print("\n📸 Capturing final state...")
        if not dry_run:
            captures.append(capture_page(driver, account_id, session_id, "_end"))
        
        # Log session
        session_end = datetime.now()
        session_data = {
            "platform": "youtube_shorts",
            "account_id": account_id,
            "cohort": account["cohort"],
            "session_id": session_id,
            "started_at": session_start.isoformat(),
            "ended_at": session_end.isoformat(),
            "duration_seconds": (session_end - session_start).total_seconds(),
            "shorts_viewed": len(shorts_data),
            "captures": captures,
            "shorts": shorts_data,
            "config": {
                "scroll_delay_range": [config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX],
                "shorts_per_session": config.SHORTS_PER_SESSION,
            }
        }
        
        if not dry_run:
            log_session(account_id, session_data)
        
        print("\n" + "=" * 60)
        print("✅ Session complete!")
        print(f"   Duration: {session_data['duration_seconds']:.1f}s")
        print(f"   Shorts viewed: {len(shorts_data)}")
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
            try:
                driver.quit()
            except Exception:
                pass
    
    return success


def run_setup_mode(account_id: str):
    """
    Run setup mode - opens browser for manual YouTube login.
    The profile is saved for future capture sessions.
    """
    print("\n" + "=" * 60)
    print(f"🔧 SETUP MODE - Account: {account_id}")
    print("=" * 60)
    
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        print(f"   Available accounts: {list(config.ACCOUNTS.keys())}")
        return False
    
    profile_path = get_profile_path(account_id)
    print(f"\n📁 Profile will be saved to: {profile_path}")
    
    print("\n📋 Instructions:")
    print("   1. A browser window will open")
    print("   2. Go to youtube.com and log in with your Google account")
    print("   3. Make sure you're fully logged in (can see your avatar)")
    print("   4. Close the browser window when done")
    print("   5. The login will be saved for future sessions")
    print("\n🚀 Opening browser in 3 seconds...")
    time.sleep(3)
    
    driver = None
    try:
        driver = create_driver(account_id, setup_mode=True)
        driver.get("https://www.youtube.com")
        
        print("\n✅ Browser opened!")
        print("   → Log into YouTube now")
        print("   → Close the browser window when done")
        print("   (Or press Ctrl+C here to abort)")
        
        # Wait for user to close the browser
        while True:
            try:
                # Check if browser is still open
                _ = driver.current_url
                time.sleep(1)
            except Exception:
                # Browser was closed
                break
        
        print("\n✅ Setup complete!")
        print(f"   Profile saved to: {profile_path}")
        print("\n   Now run capture with:")
        print(f"   python capture_youtube_shorts.py --account {account_id}")
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup aborted")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Capture YouTube Shorts feed - observation only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First time: set up account (log in manually)
  python capture_youtube_shorts.py --account neutral_1 --setup
  
  # Then: run capture sessions
  python capture_youtube_shorts.py --account neutral_1
  python capture_youtube_shorts.py --account neutral_1 --dry-run
  
  # List accounts
  python capture_youtube_shorts.py --list-accounts
        """
    )
    
    parser.add_argument(
        "--account", "-a",
        help="Account ID from config.py to use"
    )
    parser.add_argument(
        "--setup", "-s",
        action="store_true",
        help="Setup mode: open browser for manual YouTube login"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Open browser but don't save data (for testing setup)"
    )
    parser.add_argument(
        "--list-accounts", "-l",
        action="store_true",
        help="List configured accounts and exit"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Bypass rate limit checks (use sparingly!)"
    )
    
    args = parser.parse_args()
    
    if args.list_accounts:
        print("\nConfigured accounts:")
        for acc_id, acc_info in config.ACCOUNTS.items():
            profile_path = get_profile_path(acc_id)
            setup_status = "✅ ready" if profile_path.exists() else "❌ needs --setup"
            print(f"  {acc_id}: {setup_status}")
            print(f"    Cohort: {acc_info['cohort']}")
            print(f"    Description: {acc_info.get('description', 'N/A')}")
        return
    
    if not args.account:
        parser.print_help()
        print("\n❌ Error: --account is required")
        sys.exit(1)
    
    # Setup mode
    if args.setup:
        success = run_setup_mode(args.account)
        sys.exit(0 if success else 1)
    
    # If force flag, temporarily increase limits
    if args.force:
        print("⚠️  Force mode: bypassing rate limits")
        config.MAX_SESSIONS_PER_DAY = 999
        config.MIN_HOURS_BETWEEN_SESSIONS = 0
    
    success = run_capture_session(args.account, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

