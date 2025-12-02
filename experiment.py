"""
Phase 1: Training experiment - watch and engage with conflict content.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from seleniumwire import undetected_chromedriver as uc  # type: ignore[import-untyped]

import config
from driver import create_driver, setup_directories
from utils import random_delay
from youtube import (
    ShortMetadata,
    clear_requests,
    extract_short_metadata,
    swipe_to_next_short,
    wait_for_shorts_load,
)


def save_session(account_id: str, region: str, session_id: str, shorts_data: list[ShortMetadata]):
    """Save session data as a simple JSON file."""
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


def view_shorts(driver: uc.Chrome, count: int, account_id: str, session_id: str, conflict_region: config.ConflictCountry) -> list[ShortMetadata]:
    """
    View multiple Shorts, capturing metadata for each.
    Saves after every short processed.
    Returns list of Short metadata.
    """
    shorts_data: list[ShortMetadata] = []
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


def run_capture_session(account_id: str, conflict_region: config.ConflictCountry) -> bool:
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


def run_full_experiment(account_id: str) -> bool:
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

