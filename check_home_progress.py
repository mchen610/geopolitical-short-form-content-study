"""
Check Phase 2 (home feed) progress and generate statistics.
"""

import json
from collections import defaultdict

import config


def load_all_home_data() -> dict[str, list[dict]]:
    """
    Load all Phase 2 home feed data.
    Returns: {profile: [shorts]}
    """
    data: dict[str, list[dict]] = defaultdict(list)
    
    for file in sorted(config.OUTPUT_DIR.glob("*_home_*.json")):
        # Parse filename: {profile}_home_{session_id}.json
        parts = file.stem.split("_home_")
        if len(parts) != 2:
            continue
        
        profile = parts[0]
        
        with open(file) as f:
            session_data = json.load(f)
            data[profile].extend(session_data)
    
    return dict(data)


def calculate_stats(shorts: list[dict]) -> dict:
    """Calculate statistics for a list of home feed shorts."""
    if not shorts:
        return {
            "count": 0,
            "conflict_related": 0,
            "by_country": {},
            "sessions": 0,
        }
    
    by_country: dict[str, int] = defaultdict(int)
    for s in shorts:
        country = s.get("related_country")
        if country:
            by_country[country] += 1
    
    return {
        "count": len(shorts),
        "conflict_related": sum(by_country.values()),
        "by_country": dict(by_country),
        "sessions": len(shorts) // config.HOME_SHORTS_PER_SESSION,
    }


def print_home_progress_report():
    """Print a formatted progress report for home feed data."""
    print("\n" + "=" * 60)
    print("📊 HOME FEED (PHASE 2) PROGRESS REPORT")
    print("=" * 60)
    
    data = load_all_home_data()
    
    if not data:
        print("\n❌ No home feed data found!")
        print("   Looking for files matching: *_home_*.json in", config.OUTPUT_DIR)
        return
    
    # Overall stats
    all_shorts = []
    for shorts in data.values():
        all_shorts.extend(shorts)
    
    overall = calculate_stats(all_shorts)
    
    print("\n📈 OVERALL SUMMARY")
    print(f"   Total shorts:      {overall['count']}")
    print(f"   Conflict-related:  {overall['conflict_related']} ({100*overall['conflict_related']/overall['count']:.1f}%)" if overall['count'] else "   Conflict-related:  0")
    print(f"   Total sessions:    {overall['sessions']}/{config.HOME_SESSIONS * len(data)}")
    
    # Per-profile stats
    print(f"\n{'='*60}")
    print("📱 BY PROFILE")
    print("=" * 60)
    
    for profile in sorted(data.keys()):
        stats = calculate_stats(data[profile])
        status = "✅" if stats['sessions'] >= config.HOME_SESSIONS else "🔄"
        
        print(f"\n{status} {profile}:")
        print(f"   Sessions: {stats['sessions']}/{config.HOME_SESSIONS}")
        print(f"   Shorts:   {stats['count']}/{config.HOME_SESSIONS * config.HOME_SHORTS_PER_SESSION}")
        print(f"   Conflict: {stats['conflict_related']} ({100*stats['conflict_related']/stats['count']:.1f}%)" if stats['count'] else "   Conflict: 0")
        
        if stats['by_country']:
            print("   Breakdown:")
            for country, count in sorted(stats['by_country'].items(), key=lambda x: -x[1]):
                pct = 100 * count / stats['conflict_related'] if stats['conflict_related'] else 0
                print(f"      {country:<12}: {count:>3} ({pct:.0f}% of conflict)")
    
    # Aggregated country stats
    print(f"\n{'='*60}")
    print("🌍 CONFLICT VISIBILITY (All Profiles)")
    print("=" * 60)
    
    total_by_country: dict[str, int] = defaultdict(int)
    for shorts in data.values():
        for s in shorts:
            country = s.get("related_country")
            if country:
                total_by_country[country] += 1
    
    total_conflict = sum(total_by_country.values())
    
    if total_conflict:
        # ACLED scores for comparison
        acled_scores = {
            "Palestine": 2.571,
            "Myanmar": 1.900,
            "Ukraine": 1.543,
            "Mexico": 1.045,
        }
        acled_total = sum(acled_scores.values())
        
        print(f"\n{'Country':<12} {'Count':>8} {'Observed %':>12} {'Expected %':>12} {'Diff':>10}")
        print("-" * 56)
        
        for country in acled_scores.keys():
            count = total_by_country.get(country, 0)
            observed_pct = 100 * count / total_conflict if total_conflict else 0
            expected_pct = 100 * acled_scores[country] / acled_total
            diff = observed_pct - expected_pct
            diff_str = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
            
            print(f"{country:<12} {count:>8} {observed_pct:>11.1f}% {expected_pct:>11.1f}% {diff_str:>10}")
        
        print("-" * 56)
        print(f"{'Total':<12} {total_conflict:>8}")
    else:
        print("\n   No conflict-related shorts found yet.")
    
    # Session file analysis
    print(f"\n{'='*60}")
    print("📁 SESSION FILES")
    print("=" * 60)
    
    sessions = []
    for file in sorted(config.OUTPUT_DIR.glob("*_home_*.json")):
        with open(file) as f:
            file_data = json.load(f)
            sessions.append({
                "file": file.name,
                "count": len(file_data),
                "complete": len(file_data) >= config.HOME_SHORTS_PER_SESSION,
            })
    
    complete = sum(1 for s in sessions if s["complete"])
    incomplete = sum(1 for s in sessions if not s["complete"])
    
    print(f"\n   Complete sessions:   {complete}")
    print(f"   Incomplete sessions: {incomplete}")
    
    if incomplete > 0:
        print("\n   ⚠️ Incomplete sessions:")
        for s in sessions:
            if not s["complete"]:
                print(f"      {s['file']}: {s['count']}/{config.HOME_SHORTS_PER_SESSION} shorts")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_home_progress_report()

