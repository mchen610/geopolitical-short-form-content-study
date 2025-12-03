"""
Phase 2: Home feed measurement - observe what YouTube shows without engagement.
"""
import json
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


def get_home_session_files(account_id: str) -> list:
    """Get all home feed session files for account, sorted by name."""
    pattern = f"{account_id}_home_*.json"
    files = list(config.OUTPUT_DIR.glob(pattern))
    return sorted(files)


def is_home_session_complete(session_file) -> bool:
    """Check if a home session file has HOME_SHORTS_PER_SESSION shorts."""
    with open(session_file) as f:
        data = json.load(f)
    return len(data) >= config.HOME_SHORTS_PER_SESSION


def get_home_session_count(account_id: str) -> int:
    """Count how many COMPLETE home feed sessions have been run for this account."""
    files = get_home_session_files(account_id)
    return sum(1 for f in files if is_home_session_complete(f))


def get_incomplete_home_session(account_id: str) -> tuple | None:
    """Get the most recent incomplete home session (file_path, existing_data, session_id), if any."""
    files = get_home_session_files(account_id)
    if not files:
        return None
    
    last_file = files[-1]
    with open(last_file) as f:
        data = json.load(f)
    
    if len(data) < config.HOME_SHORTS_PER_SESSION:
        # Extract session_id from filename: {account}_home_{session_id}.json
        session_id = last_file.stem.replace(f"{account_id}_home_", "")
        return (last_file, data, session_id)
    return None


def print_home_progress(account_id: str):
    """Print current home feed progress."""
    complete = get_home_session_count(account_id)
    incomplete = get_incomplete_home_session(account_id)
    
    print(f"\n📊 Current Progress: {complete}/{config.HOME_SESSIONS} sessions")
    if incomplete:
        _, data, _ = incomplete
        print(f"   + {len(data)}/{config.HOME_SHORTS_PER_SESSION} in progress")


def view_home_shorts(
    driver: uc.Chrome,
    count: int,
    account_id: str,
    session_id: str,
    existing_data: list[HomeShortMetadata] | None = None
) -> list[HomeShortMetadata]:
    """
    View home feed Shorts without engagement, classifying each by conflict.
    Saves after every short processed. Can resume from existing_data.
    """
    shorts_data: list[HomeShortMetadata] = existing_data if existing_data else []
    start_idx = len(shorts_data)
    
    for i in range(start_idx, count):
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
    """Run a single home feed measurement session. Resumes incomplete sessions."""
    print("\n" + "=" * 60)
    print(f"🏠 Home Feed Measurement - Account: {account_id}")
    print("=" * 60)
    
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    # Check for incomplete session to resume
    incomplete = get_incomplete_home_session(account_id)
    existing_data: list[HomeShortMetadata] | None = None
    
    if incomplete:
        _, existing_data, session_id = incomplete
        print(f"   ⏯️  Resuming incomplete session: {len(existing_data)}/{config.HOME_SHORTS_PER_SESSION} shorts done")
    else:
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
        
        # Skip ahead if resuming
        if existing_data:
            print(f"   ⏭️  Skipping {len(existing_data)} already-captured shorts...")
            for _ in range(len(existing_data)):
                swipe_to_next_short(driver)
                random_delay(0.2, 0.4)
        
        remaining = config.HOME_SHORTS_PER_SESSION - (len(existing_data) if existing_data else 0)
        print(f"\n📺 Viewing {remaining} shorts (no engagement)...")
        shorts_data = view_home_shorts(driver, config.HOME_SHORTS_PER_SESSION, account_id, session_id, existing_data)
        
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
    Automatically resumes from where it left off.
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
    
    # Show current progress
    print_home_progress(account_id)
    
    sessions_run = 0
    while get_home_session_count(account_id) < config.HOME_SESSIONS or get_incomplete_home_session(account_id):
        success = run_home_feed_session(account_id)
        sessions_run += 1
        
        if not success:
            print("⚠️  Session failed, continuing to next...")
        
        # Check if done
        if get_home_session_count(account_id) >= config.HOME_SESSIONS:
            break
        
        # Delay between sessions
        random_delay(2, 5)
    
    if sessions_run == 0:
        print("\n✅ All sessions already complete!")
    
    print("\n" + "=" * 60)
    print(f"🎉 HOME FEED MEASUREMENT COMPLETE for {account_id}")
    print("=" * 60)
    return True

