"""
Phase 2: Home feed measurement - observe what YouTube shows without engagement.
"""
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from seleniumwire import undetected_chromedriver as uc  # type: ignore[import-untyped]

import config
from driver import create_driver, setup_directories
from utils import random_delay
from youtube import (
    HomeShortMetadata,
    clear_requests,
    extract_home_short_metadata,
    swipe_to_next_short,
    wait_for_shorts_load,
)


def save_home_session(account_id: str, session_id: str, shorts_data: list[HomeShortMetadata]):
    """Save home feed session data as JSON file."""
    session_file = config.OUTPUT_DIR / f"{account_id}_home_{session_id}.json"
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(shorts_data, f, indent=2, ensure_ascii=False)


def get_home_session_count(account_id: str) -> int:
    """Count how many home feed sessions have been run for this account."""
    pattern = f"{account_id}_home_*.json"
    existing_files = list(config.OUTPUT_DIR.glob(pattern))
    return len(existing_files)


def view_home_shorts(driver: uc.Chrome, count: int, account_id: str, session_id: str) -> list[HomeShortMetadata]:
    """
    View home feed Shorts without engagement, classifying each by conflict.
    Saves after every short processed.
    """
    shorts_data: list[HomeShortMetadata] = []
    
    for i in range(count):
        if not driver.current_url:
            print("Browser closed, exiting...")
            break
        
        # Extract metadata and classify conflict
        metadata = extract_home_short_metadata(driver)
        shorts_data.append(metadata)
        
        # Save after every short
        save_home_session(account_id, session_id, shorts_data)
        
        # Clear network requests
        clear_requests(driver)
        
        # Swipe to next Short (except for last one)
        if i < count - 1:
            swipe_to_next_short(driver)
            random_delay(0.3, 0.7)
    
    return shorts_data


def run_home_feed_session(account_id: str) -> bool:
    """Run a single home feed measurement session."""
    print("\n" + "=" * 60)
    print(f"🏠 Home Feed Measurement - Account: {account_id}")
    print("=" * 60)
    
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    eastern = ZoneInfo('America/New_York')
    session_id = datetime.now(eastern).strftime("%Y-%m-%d_%I:%M:%S%p")
    
    session_num = get_home_session_count(account_id) + 1
    print(f"Session {session_num}/{config.HOME_SESSIONS}")
    
    success = False
    driver = create_driver(account_id)
    
    try:
        setup_directories()
        
        print("Loading YouTube Shorts home feed...")
        driver.get("https://www.youtube.com/shorts")
        wait_for_shorts_load(driver)
        print("✅ Home feed loaded!")
        
        print(f"\n📺 Viewing {config.HOME_SHORTS_PER_SESSION} shorts (no engagement)...")
        shorts_data = view_home_shorts(driver, config.HOME_SHORTS_PER_SESSION, account_id, session_id)
        
        # Summary
        conflict_counts: dict[str, int] = {}
        for s in shorts_data:
            key = s["related_country"] or "None"
            conflict_counts[key] = conflict_counts.get(key, 0) + 1
        
        print("\n" + "=" * 60)
        print("✅ Session complete!")
        print(f"   Shorts viewed: {len(shorts_data)}")
        print("   Conflicts detected:")
        for conflict_name, count in sorted(conflict_counts.items(), key=lambda x: -x[1]):
            print(f"      {conflict_name}: {count}")
        print("=" * 60)
        
        success = True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        
    finally:
        print("\n🔒 Closing browser...")
        driver.quit()
    
    return success


def run_home_feed(account_id: str) -> bool:
    """
    Run all home feed measurement sessions for an account.
    10 sessions × 50 shorts = 500 shorts total.
    """
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    print("\n" + "=" * 60)
    print(f"🏠 HOME FEED MEASUREMENT - Account: {account_id}")
    print(f"   Sessions: {config.HOME_SESSIONS}")
    print(f"   Shorts per session: {config.HOME_SHORTS_PER_SESSION}")
    print(f"   Total shorts: {config.HOME_SESSIONS * config.HOME_SHORTS_PER_SESSION}")
    print("   Engagement: None (observe only)")
    print("=" * 60)
    
    for session_num in range(1, config.HOME_SESSIONS + 1):
        success = run_home_feed_session(account_id)
        
        if not success:
            print("⚠️  Session failed, continuing to next...")
        
        # Delay between sessions
        if session_num < config.HOME_SESSIONS:
            random_delay(2, 5)
    
    print("\n" + "=" * 60)
    print(f"🎉 HOME FEED MEASUREMENT COMPLETE for {account_id}")
    print("=" * 60)
    return True

