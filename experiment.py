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


def get_session_files_for_country(account_id: str, conflict_region: config.ConflictCountry) -> list:
    """Get all session files for account+country, sorted by name (timestamp)."""
    pattern = f"{account_id}_{conflict_region}_*.json"
    files = list(config.OUTPUT_DIR.glob(pattern))
    return sorted(files)


def is_session_complete(session_file) -> bool:
    """Check if a session file has SHORTS_PER_SESSION shorts."""
    with open(session_file) as f:
        data = json.load(f)
    return len(data) >= config.SHORTS_PER_SESSION


def get_session_count_for_country(account_id: str, conflict_region: config.ConflictCountry) -> int:
    """Count how many COMPLETE sessions have been run for this account+country."""
    files = get_session_files_for_country(account_id, conflict_region)
    return sum(1 for f in files if is_session_complete(f))


def get_incomplete_session(account_id: str, conflict_region: config.ConflictCountry) -> tuple | None:
    """Get the most recent incomplete session (file_path, existing_data, session_id), if any."""
    files = get_session_files_for_country(account_id, conflict_region)
    if not files:
        return None
    
    last_file = files[-1]
    with open(last_file) as f:
        data = json.load(f)
    
    if len(data) < config.SHORTS_PER_SESSION:
        # Extract session_id from filename: {account}_{region}_{session_id}.json
        session_id = last_file.stem.replace(f"{account_id}_{conflict_region}_", "")
        return (last_file, data, session_id)
    return None


def print_progress(account_id: str):
    """Print current progress for an account."""
    if account_id not in config.ACCOUNT_COUNTRY_ORDER:
        return
    
    country_order = config.ACCOUNT_COUNTRY_ORDER[account_id]
    print("\n📊 Current Progress:")
    
    for country in country_order:
        complete = get_session_count_for_country(account_id, country)
        incomplete = get_incomplete_session(account_id, country)
        incomplete_str = ""
        if incomplete:
            _, data, _ = incomplete
            incomplete_str = f" + {len(data)}/{config.SHORTS_PER_SESSION} in progress"
        print(f"   {country}: {complete}/{config.SESSIONS_PER_COUNTRY} sessions{incomplete_str}")
    print()


def get_next_url_for_country(account_id: str, conflict_region: config.ConflictCountry) -> str:
    """Get the next URL to use for this account+country based on session count."""
    urls = config.CONFLICT_URLS[conflict_region]
    session_count = get_session_count_for_country(account_id, conflict_region)
    # Use modulo to wrap around if we've done more sessions than URLs
    url_index = session_count % len(urls)
    return urls[url_index]


def view_shorts(
    driver: uc.Chrome,
    count: int,
    account_id: str,
    session_id: str,
    conflict_region: config.ConflictCountry,
    existing_data: list[ShortMetadata] | None = None
) -> list[ShortMetadata]:
    """
    View multiple Shorts, capturing metadata for each.
    Saves after every short processed.
    Can resume from existing_data if provided.
    Returns list of Short metadata.
    """
    shorts_data: list[ShortMetadata] = existing_data if existing_data else []
    start_idx = len(shorts_data)
    
    for i in range(start_idx, count):
        if not driver.current_url:
            print("Browser closed, exiting...")
            break
        
        # Extract full metadata
        metadata = extract_short_metadata(driver, conflict_region)
        shorts_data.append(metadata)
        
        # Save after every short
        save_session(account_id, conflict_region, session_id, shorts_data)
        
        # Clear network requests to avoid matching old timedtext data
        clear_requests(driver)
        
        # Swipe to next Short (except for last one)
        if i < count - 1:
            swipe_to_next_short(driver)
            random_delay(0.5, 1.5)
    
    return shorts_data


def run_capture_session(account_id: str, conflict_region: config.ConflictCountry) -> bool:
    """
    Run a single Shorts capture session for the given account.
    Will resume an incomplete session if one exists.
    """
    print("\n" + "=" * 60)
    print(f"🎬 YouTube Shorts Capture - Account: {account_id}")
    print("=" * 60)
    
    # Validate account
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        print(f"   Available accounts: {config.ACCOUNTS}")
        return False
    
    # Check for incomplete session to resume
    incomplete = get_incomplete_session(account_id, conflict_region)
    existing_data: list[ShortMetadata] | None = None
    
    if incomplete:
        _, existing_data, session_id = incomplete
        print(f"   ⏯️  Resuming incomplete session: {len(existing_data)}/{config.SHORTS_PER_SESSION} shorts done")
    else:
        # Generate new session ID in Eastern time with AM/PM
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
        wait_for_shorts_load(driver)
        print("✅ Shorts loaded!")
        
        # Skip ahead if resuming
        if existing_data:
            print(f"   ⏭️  Skipping {len(existing_data)} already-captured shorts...")
            for _ in range(len(existing_data)):
                swipe_to_next_short(driver)
                random_delay(0.3, 0.5)
        
        # View Shorts (saves after each one)
        remaining = config.SHORTS_PER_SESSION - (len(existing_data) if existing_data else 0)
        print(f"\n🎬 Viewing Shorts ({remaining} remaining)...")
        shorts_data = view_shorts(driver, config.SHORTS_PER_SESSION, account_id, session_id, conflict_region, existing_data)
        
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
    Run the full experiment for an account using STAGGERED design:
    - Each round cycles through all countries in the pre-assigned order
    - Runs SESSIONS_PER_COUNTRY rounds total
    - This controls for temporal confounds (all countries get early + late sessions)
    - Automatically resumes from where it left off
    """
    if account_id not in config.ACCOUNT_COUNTRY_ORDER:
        print(f"❌ No country order defined for account: {account_id}")
        print(f"   Available accounts: {config.ACCOUNTS}")
        return False
    
    country_order = config.ACCOUNT_COUNTRY_ORDER[account_id]
    total_sessions = len(country_order) * config.SESSIONS_PER_COUNTRY
    
    print("\n" + "=" * 60)
    print(f"🔬 FULL EXPERIMENT (STAGGERED) - Account: {account_id}")
    print(f"   Rotation order: {' → '.join(country_order)}")
    print(f"   Rounds: {config.SESSIONS_PER_COUNTRY}")
    print(f"   Sessions per round: {len(country_order)} (one per country)")
    print(f"   Shorts per session: {config.SHORTS_PER_SESSION}")
    print(f"   Total shorts per country: {config.SESSIONS_PER_COUNTRY * config.SHORTS_PER_SESSION}")
    print(f"   Total shorts overall: {total_sessions * config.SHORTS_PER_SESSION}")
    print("=" * 60)
    
    # Show current progress
    print_progress(account_id)
    
    session_counter = 0
    skipped = 0
    
    for round_num in range(1, config.SESSIONS_PER_COUNTRY + 1):
        round_has_work = False
        
        for country_idx, country in enumerate(country_order):
            session_counter += 1
            complete_sessions = get_session_count_for_country(account_id, country)
            has_incomplete = get_incomplete_session(account_id, country) is not None
            
            # Skip if this country already has enough complete sessions for this round
            # (round_num is 1-indexed, so round 1 needs 1 session, round 2 needs 2, etc.)
            if complete_sessions >= round_num and not has_incomplete:
                skipped += 1
                continue
            
            # Only print round header if there's work to do
            if not round_has_work:
                print(f"\n{'='*60}")
                print(f"🔄 ROUND {round_num}/{config.SESSIONS_PER_COUNTRY}")
                print(f"{'='*60}")
                round_has_work = True
            
            print(f"\n📺 Session {session_counter}/{total_sessions} | {country} (#{complete_sessions + 1})")
            success = run_capture_session(account_id, country)
            
            if not success:
                print("⚠️  Session failed, continuing to next...")
            
    if skipped > 0:
        print(f"\n   (Skipped {skipped} already-completed sessions)")
    
    print("\n" + "=" * 60)
    print(f"🎉 EXPERIMENT COMPLETE for {account_id}")
    print("=" * 60)
    return True

