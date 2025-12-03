"""
Check experiment progress and generate statistics from Phase 1 training data.
"""

import json
from collections import defaultdict

import config


def load_all_training_data() -> dict[str, dict[str, list[dict]]]:
    """
    Load all Phase 1 training data.
    Returns: {profile: {country: [shorts]}}
    """
    data: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    
    for file in sorted(config.OUTPUT_DIR.glob("*.json")):
        # Skip home feed files
        if "_home_" in file.name:
            continue
        
        # Parse filename: {profile}_{country}_{session_id}.json
        parts = file.stem.split("_")
        if len(parts) < 3:
            continue
        
        profile = parts[0] + "_" + parts[1]  # e.g., "profile_1"
        country = parts[2]  # e.g., "Palestine"
        
        if country not in config.CONFLICT_KEYWORDS:
            continue
        
        with open(file) as f:
            try:
                session_data = json.load(f)
                data[profile][country].extend(session_data)
            except json.JSONDecodeError:
                print(f"   ⚠️ Could not parse: {file.name}")
    
    return dict(data)


def calculate_stats(shorts: list[dict]) -> dict:
    """Calculate statistics for a list of shorts."""
    if not shorts:
        return {
            "count": 0,
            "related": 0,
            "related_pct": 0.0,
            "avg_duration": None,
            "sessions": 0,
        }
    
    related = sum(1 for s in shorts if s.get("is_conflict_related"))
    durations = [s["duration_seconds"] for s in shorts if s.get("duration_seconds")]
    
    return {
        "count": len(shorts),
        "related": related,
        "related_pct": 100 * related / len(shorts) if shorts else 0,
        "avg_duration": sum(durations) / len(durations) if durations else None,
        "sessions": len(shorts) // config.SHORTS_PER_SESSION,
    }


def print_progress_report():
    """Print a formatted progress report."""
    print("\n" + "=" * 60)
    print("📊 EXPERIMENT PROGRESS REPORT")
    print("=" * 60)
    
    data = load_all_training_data()
    
    if not data:
        print("\n❌ No training data found in", config.OUTPUT_DIR)
        return
    
    # Overall stats
    all_shorts = []
    for profile_data in data.values():
        for country_shorts in profile_data.values():
            all_shorts.extend(country_shorts)
    
    overall = calculate_stats(all_shorts)
    
    print("\n📈 OVERALL SUMMARY")
    print(f"   Total shorts:     {overall['count']}")
    print(f"   Total related:    {overall['related']} ({overall['related_pct']:.1f}%)")
    if overall['avg_duration']:
        print(f"   Avg duration:     {overall['avg_duration']:.1f}s")
    
    # Per-profile stats
    print(f"\n{'='*60}")
    print("📱 BY PROFILE")
    print("=" * 60)
    
    for profile in sorted(data.keys()):
        profile_shorts = []
        for country_shorts in data[profile].values():
            profile_shorts.extend(country_shorts)
        
        stats = calculate_stats(profile_shorts)
        countries_done = sum(1 for c in data[profile] if len(data[profile][c]) >= config.SHORTS_PER_SESSION * config.SESSIONS_PER_COUNTRY)
        
        print(f"\n{profile}:")
        print(f"   Sessions: {stats['sessions']}/{config.SESSIONS_PER_COUNTRY * len(config.CONFLICT_KEYWORDS)}")
        print(f"   Shorts:   {stats['count']}")
        print(f"   Related:  {stats['related']} ({stats['related_pct']:.1f}%)")
        
        # Per-country breakdown for this profile
        for country in config.CONFLICT_KEYWORDS.keys():
            if country in data[profile]:
                c_stats = calculate_stats(data[profile][country])
                sessions_complete = c_stats['count'] // config.SHORTS_PER_SESSION
                status = "✅" if sessions_complete >= config.SESSIONS_PER_COUNTRY else "🔄"
                print(f"      {status} {country:<12}: {sessions_complete}/{config.SESSIONS_PER_COUNTRY} sessions, {c_stats['related_pct']:.0f}% related")
            else:
                print(f"      ⏳ {country:<12}: 0/{config.SESSIONS_PER_COUNTRY} sessions")
    
    # Per-country stats (aggregated across profiles)
    print(f"\n{'='*60}")
    print("🌍 BY COUNTRY (All Profiles)")
    print("=" * 60)
    
    country_totals: dict[str, list[dict]] = defaultdict(list)
    for profile_data in data.values():
        for country, shorts in profile_data.items():
            country_totals[country].extend(shorts)
    
    print(f"\n{'Country':<12} {'Shorts':>8} {'Related':>8} {'% Related':>10} {'Avg Duration':>14}")
    print("-" * 60)
    
    for country in config.CONFLICT_KEYWORDS.keys():
        shorts = country_totals.get(country, [])
        stats = calculate_stats(shorts)
        
        dur_str = f"{stats['avg_duration']:.1f}s" if stats['avg_duration'] else "N/A"
        print(f"{country:<12} {stats['count']:>8} {stats['related']:>8} {stats['related_pct']:>9.1f}% {dur_str:>14}")
    
    print("-" * 60)
    
    # Session timing analysis
    print(f"\n{'='*60}")
    print("⏱️ TIMING ANALYSIS")
    print("=" * 60)
    
    # Get all session files with timestamps
    sessions = []
    for file in sorted(config.OUTPUT_DIR.glob("*.json")):
        if "_home_" in file.name:
            continue
        parts = file.stem.split("_")
        if len(parts) >= 3:
            with open(file) as f:
                data = json.load(f)
                sessions.append({
                    "file": file.name,
                    "count": len(data),
                    "complete": len(data) >= config.SHORTS_PER_SESSION,
                })
    
    complete = sum(1 for s in sessions if s["complete"])
    incomplete = sum(1 for s in sessions if not s["complete"])
    
    print(f"\n   Complete sessions:   {complete}")
    print(f"   Incomplete sessions: {incomplete}")
    
    if incomplete > 0:
        print("\n   ⚠️ Incomplete sessions:")
        for s in sessions:
            if not s["complete"]:
                print(f"      {s['file']}: {s['count']}/{config.SHORTS_PER_SESSION} shorts")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_progress_report()

