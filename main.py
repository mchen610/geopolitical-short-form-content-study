import argparse
import json
import sys
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
from tests import run_test_links

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


def get_session_count_for_country(account_id: str, conflict_region: config.ConflictCountry) -> int:
    """Count how many sessions have already been run for this account+country."""
    pattern = f"{account_id}_{conflict_region}_*.json"
    existing_files = list(config.OUTPUT_DIR.glob(pattern))
    return len(existing_files)


def get_next_url_for_country(account_id: str, conflict_region: config.ConflictCountry) -> str:
    """Get the next URL to use for this account+country based on session count."""
    urls = config.CONFLICT_URLS[conflict_region]
    session_count = get_session_count_for_country(account_id, conflict_region)
    # Use modulo to wrap around if we've done more sessions than URLs
    url_index = session_count % len(urls)
    return urls[url_index]


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

    # Get the next URL in sequence for this account+country
    start_url = get_next_url_for_country(account_id, conflict_region)
    session_count = get_session_count_for_country(account_id, conflict_region)
    print(f"   Session #{session_count + 1} for {conflict_region}")
    print(f"   Starting URL: {start_url}")

    try:
        # Setup
        setup_directories()
        
        print("Loading YouTube Shorts...")
        driver.get(start_url)
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


def run_full_experiment(account_id: str):
    """
    Run the full experiment for an account:
    - Goes through all 5 countries in the pre-assigned random order
    - Runs SESSIONS_PER_COUNTRY sessions per country (5 * 15 = 75 shorts per country)
    """
    if account_id not in config.ACCOUNT_COUNTRY_ORDER:
        print(f"❌ No country order defined for account: {account_id}")
        print(f"   Available accounts: {config.ACCOUNTS}")
        return False
    
    country_order = config.ACCOUNT_COUNTRY_ORDER[account_id]
    
    print("\n" + "=" * 60)
    print(f"🔬 FULL EXPERIMENT - Account: {account_id}")
    print(f"   Country order: {' → '.join(country_order)}")
    print(f"   Sessions per country: {config.SESSIONS_PER_COUNTRY}")
    print(f"   Shorts per session: {config.SHORTS_PER_SESSION}")
    print(f"   Total shorts per country: {config.SESSIONS_PER_COUNTRY * config.SHORTS_PER_SESSION}")
    print(f"   Total shorts overall: {len(country_order) * config.SESSIONS_PER_COUNTRY * config.SHORTS_PER_SESSION}")
    print("=" * 60)
    
    for country_idx, country in enumerate(country_order, 1):
        print(f"\n{'='*60}")
        print(f"🌍 COUNTRY {country_idx}/{len(country_order)}: {country}")
        print(f"{'='*60}")
        
        for session_num in range(1, config.SESSIONS_PER_COUNTRY + 1):
            print(f"\n📺 Session {session_num}/{config.SESSIONS_PER_COUNTRY} for {country}")
            success = run_capture_session(account_id, country)
            
            if not success:
                print("⚠️  Session failed, continuing to next...")
            
            # Delay between sessions
            if session_num < config.SESSIONS_PER_COUNTRY:
                random_delay(2, 5)

        # Delay between countries
        if country_idx < len(country_order):
            print("\n⏳ Switching to next country...")
            random_delay(3, 6)
    
    print("\n" + "=" * 60)
    print(f"🎉 EXPERIMENT COMPLETE for {account_id}")
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Capture YouTube Shorts feed and like conflict-related content",
        epilog="First run: python main.py --account neutral_1 --setup"
    )
    
    parser.add_argument("--account", "-a", help="Account ID from config.py")
    parser.add_argument("--setup", "-s", action="store_true", help="Setup: log into YouTube")
    parser.add_argument("--list-accounts", "-l", action="store_true", help="List accounts")
    parser.add_argument("--run", "-r", action="store_true", help="Run full experiment for account")
    parser.add_argument("--test", "-t", nargs="?", const="ALL", metavar="COUNTRY", help="Test URLs (all countries if none specified, uses test account)")
    
    args = parser.parse_args()
    
    if args.list_accounts:
        print("\nAccounts and their country orders:")
        for acc_id in config.ACCOUNTS:
            profile_path = CHROME_PROFILES_DIR / acc_id
            status = "✅" if profile_path.exists() else "❌ needs --setup"
            order = config.ACCOUNT_COUNTRY_ORDER[acc_id]
            print(f"  {acc_id}: {status}")
            if order:
                print(f"    Order: {' → '.join(order)}")
        return
    
    if args.test:
        if args.test == "ALL":
            # Test all countries
            success = run_test_links(create_driver, setup_directories, None)
        else:
            # Validate country
            valid_countries = list(config.CONFLICT_URLS.keys())
            if args.test not in valid_countries:
                print(f"❌ Unknown country: {args.test}")
                print(f"   Valid countries: {valid_countries}")
                sys.exit(1)
            success = run_test_links(create_driver, setup_directories, args.test)
        sys.exit(0 if success else 1)
    
    if not args.account:
        print("❌ Please specify an account with --account")
        print("   Use --list-accounts to see available accounts")
        sys.exit(1)
    
    if args.setup:
        success = run_setup(args.account)
        sys.exit(0 if success else 1)
    
    if args.run:
        success = run_full_experiment(args.account)
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()

