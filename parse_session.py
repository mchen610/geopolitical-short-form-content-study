"""
Parse session data and enrich with video metadata.

Usage:
  python parse_session.py                    # Parse latest session
  python parse_session.py --all              # Parse all sessions
  python parse_session.py --session <id>     # Parse specific session
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests

DATA_DIR = Path("./data")
LOGS_DIR = DATA_DIR / "logs"
OUTPUT_DIR = DATA_DIR / "parsed"


def get_video_metadata_noembed(video_id: str) -> dict:
    """
    Get video metadata using noembed.com (no API key needed).
    Returns title, author, thumbnail.
    """
    url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title"),
                "channel": data.get("author_name"),
                "thumbnail": data.get("thumbnail_url"),
            }
    except Exception as e:
        print(f"  Warning: Failed to fetch metadata for {video_id}: {e}")
    return {}


def get_video_metadata_oembed(video_id: str) -> dict:
    """
    Get video metadata using YouTube's oEmbed endpoint (no API key needed).
    """
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title"),
                "channel": data.get("author_name"),
                "channel_url": data.get("author_url"),
            }
    except Exception as e:
        print(f"  Warning: Failed to fetch metadata for {video_id}: {e}")
    return {}


def enrich_shorts_data(shorts: list[dict], delay: float = 0.5) -> list[dict]:
    """
    Enrich shorts data with metadata from YouTube.
    """
    enriched = []
    total = len(shorts)
    
    for i, short in enumerate(shorts):
        video_id = short.get("video_id")
        if not video_id:
            enriched.append(short)
            continue
        
        print(f"  [{i+1}/{total}] Fetching metadata for {video_id}...")
        
        # Try oembed first (more reliable)
        metadata = get_video_metadata_oembed(video_id)
        
        # Merge with existing data
        enriched_short = {**short, **metadata}
        enriched.append(enriched_short)
        
        # Be nice to YouTube
        time.sleep(delay)
    
    return enriched


def load_sessions(account_id: str = None) -> list[dict]:
    """Load all session logs, optionally filtered by account."""
    sessions = []
    
    pattern = f"sessions_{account_id}.jsonl" if account_id else "sessions_*.jsonl"
    
    for log_file in LOGS_DIR.glob(pattern):
        with open(log_file) as f:
            for line in f:
                try:
                    session = json.loads(line.strip())
                    sessions.append(session)
                except json.JSONDecodeError:
                    continue
    
    return sessions


def parse_session(session: dict, enrich: bool = True) -> dict:
    """
    Parse a single session, optionally enriching with metadata.
    """
    print(f"\n📊 Parsing session: {session['session_id']}")
    print(f"   Account: {session['account_id']}")
    print(f"   Shorts viewed: {session['shorts_viewed']}")
    
    shorts = session.get("shorts", [])
    
    if enrich and shorts:
        print(f"\n   Fetching metadata from YouTube...")
        shorts = enrich_shorts_data(shorts)
    
    # Create parsed output
    parsed = {
        "session_id": session["session_id"],
        "account_id": session["account_id"],
        "cohort": session["cohort"],
        "started_at": session["started_at"],
        "ended_at": session["ended_at"],
        "duration_seconds": session["duration_seconds"],
        "shorts_count": len(shorts),
        "shorts": shorts,
    }
    
    return parsed


def save_parsed_session(parsed: dict):
    """Save parsed session to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"{parsed['account_id']}_{parsed['session_id']}.json"
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)
    
    print(f"\n✅ Saved to: {output_path}")
    return output_path


def export_to_csv(parsed: dict):
    """Export shorts to CSV for easier analysis."""
    import csv
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"{parsed['account_id']}_{parsed['session_id']}.csv"
    output_path = OUTPUT_DIR / filename
    
    fieldnames = ["view_index", "video_id", "title", "channel", "url", "extracted_at"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for short in parsed["shorts"]:
            writer.writerow(short)
    
    print(f"📄 CSV saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Parse and enrich session data")
    parser.add_argument("--account", "-a", help="Account ID to parse")
    parser.add_argument("--session", "-s", help="Specific session ID to parse")
    parser.add_argument("--all", action="store_true", help="Parse all sessions")
    parser.add_argument("--no-enrich", action="store_true", help="Skip fetching metadata")
    parser.add_argument("--csv", action="store_true", help="Also export to CSV")
    
    args = parser.parse_args()
    
    sessions = load_sessions(args.account)
    
    if not sessions:
        print("❌ No sessions found")
        return
    
    # Filter by session ID if specified
    if args.session:
        sessions = [s for s in sessions if s["session_id"] == args.session]
        if not sessions:
            print(f"❌ Session not found: {args.session}")
            return
    elif not args.all:
        # Just parse the most recent session
        sessions = [max(sessions, key=lambda s: s["started_at"])]
    
    print(f"Found {len(sessions)} session(s) to parse")
    
    for session in sessions:
        parsed = parse_session(session, enrich=not args.no_enrich)
        save_parsed_session(parsed)
        
        if args.csv:
            export_to_csv(parsed)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()

