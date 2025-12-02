import argparse
import json
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from seleniumwire import undetected_chromedriver as uc  # type: ignore[import-untyped]

import config
from utils import random_delay
from youtube import (
    ShortMetadata,
    clear_requests,
    extract_short_metadata,
    swipe_to_next_short,
    wait_for_shorts_load,
)

# Directory for this script's dedicated Chrome profiles
CHROME_PROFILES_DIR = Path("./chrome_profiles")


def setup_directories():
    """Create output directory if it doesn't exist."""
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    CHROME_PROFILES_DIR.mkdir(exist_ok=True)



def create_driver(account_id: str, setup_mode: bool = False):
    """
    Create an undetected Chrome driver with a dedicated profile for this account.
    """
    if account_id not in config.ACCOUNTS:
        raise ValueError(f"Unknown account: {account_id}. Check config.py")
    
    
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
    
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--ignore-certificate-errors")
    
    # Selenium Wire options - only capture timedtext requests to reduce proxy load
    seleniumwire_options = {
        'disable_encoding': True,
        'include_urls': [
            '.*timedtext.*',
        ],
    }
    
    driver = uc.Chrome(
        options=options,
        seleniumwire_options=seleniumwire_options,
        version_main=None,
        window_height=config.VIEWPORT_HEIGHT,
        window_width=config.VIEWPORT_WIDTH,
    )
    return driver

def view_shorts(driver: uc.Chrome, count: int, account_id: str, session_id: str, conflict_region: config.ConflictCountry) -> list[ShortMetadata]:
    """
    View multiple Shorts, capturing metadata for each.
    Saves after every short processed.
    Returns list of Short metadata.
    """
    shorts_data = []
    for i in range(count):
        if not driver.current_url:
            print("Browser closed, exiting...")
            break
        
        # Extract full metadata
        metadata = extract_short_metadata(driver, i + 1, conflict_region)
        shorts_data.append(metadata)
        
        # Save after every short
        save_session(account_id, conflict_region, session_id, shorts_data)
        
        # Clear network requests to avoid matching old timedtext data
        clear_requests(driver)
        
        # Human-like viewing delay (watching the Short)
        if metadata["is_conflict_related"]:
            random_delay(config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX)
        
        # Swipe to next Short (except for last one)
        if i < count - 1:
            swipe_to_next_short(driver)
            random_delay(0.5, 1.5)
    
    return shorts_data


def save_session(account_id: str, region: str, session_id: str, shorts_data: list[ShortMetadata]):
    """Save session data as a simple JSON file."""
    # Clean up the shorts data to just what we need
    
    session_file = config.OUTPUT_DIR / f"{account_id}_{region}_{session_id}.json"
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(shorts_data, f, indent=2, ensure_ascii=False)


def run_capture_session(account_id: str, conflict_region: config.ConflictCountry):
    """
    Run a single Shorts capture session for the given account.
    """
    print("\n" + "=" * 60)
    print(f"🎬 YouTube Shorts Capture - Account: {account_id}")
    print("=" * 60)
    
    # Validate account
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        print(f"   Available accounts: {config.ACCOUNTS}")
        return False
    
    # Generate session ID in Eastern time with AM/PM
    eastern = ZoneInfo('America/New_York')
    session_id = datetime.now(eastern).strftime("%Y-%m-%d_%I:%M:%S%p")
    
    success = False
    driver = create_driver(account_id)


    try:
        # Setup
        setup_directories()
        
        print("Loading YouTube Shorts...")
        driver.get(config.CONFLICT_URLS[conflict_region])
        
        # Wait for page with human-like delay
        random_delay(config.PAGE_LOAD_WAIT_MIN, config.PAGE_LOAD_WAIT_MAX)
        
        wait_for_shorts_load(driver)
        print("✅ Shorts loaded!")
        
        # View Shorts (saves after each one)
        print(f"\n🎬 Viewing Shorts ({config.SHORTS_PER_SESSION} videos)...")
        shorts_data = view_shorts(driver, config.SHORTS_PER_SESSION, account_id, session_id, conflict_region)
        
        num_related = sum(1 for s in shorts_data if s["is_conflict_related"])
        print("\n" + "=" * 60)
        print("✅ Session complete!")
        print(f"   Conflict region: {conflict_region}")
        print(f"   Shorts viewed: {len(shorts_data)}")
        print(f"   Related: {num_related}")
        print(f"   Not related: {len(shorts_data) - num_related}")
        print("=" * 60)
        
        success = True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        
    finally:
        print("\n🔒 Closing browser...")
        driver.quit()

    return success


def run_setup(account_id: str):
    """Open browser for manual YouTube login. Profile is saved for future sessions."""
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    print("   1. Browser will open")
    print("   2. Log into Google")
    print("   3. Close browser when done")
    
    setup_directories()
    driver = create_driver(account_id, setup_mode=True)
    while True:
        try:
            _ = driver.current_url
        except KeyboardInterrupt:
            print("\n⚠️  Aborted")
            driver.quit()
            return False
        except Exception:
            break
    print("✅ Setup complete!")
    driver.quit()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Capture YouTube Shorts feed and like conflict-related content",
        epilog="First run: python main.py --account neutral_1 --setup"
    )
    
    parser.add_argument("--account", "-a", help="Account ID from config.py")
    parser.add_argument("--setup", "-s", action="store_true", help="Setup: log into YouTube")
    parser.add_argument("--list-accounts", "-l", action="store_true", help="List accounts")
    
    args = parser.parse_args()
    
    if args.list_accounts:
        print("\nAccounts:")
        for acc_id in config.ACCOUNTS:
            profile_path = CHROME_PROFILES_DIR / acc_id
            status = "✅" if profile_path.exists() else "❌ needs --setup"
            print(f"  {acc_id}: {status}")
        return
    
    if not args.account:
        args.account = list(config.ACCOUNTS)[1]
        print(f"Using default account: {args.account}")
    
    if args.setup:
        success = run_setup(args.account)
        sys.exit(0 if success else 1)
    
    for i in range(10):
        run_capture_session(args.account, "Mexico")
        random_delay(1, 2)


if __name__ == "__main__":
    main()

