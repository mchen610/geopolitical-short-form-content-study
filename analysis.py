"""
Statistical analysis for YouTube Shorts geopolitical conflict study.

Tests whether YouTube's algorithmic visibility is proportional to conflict severity (ACLED Index).

Hypothesis:
    H₀: Visibility distribution matches ACLED severity proportions
    H₁: Visibility distribution differs from ACLED severity proportions

Method: Chi-Square Goodness of Fit Test
    - Uses raw count data (n=221 conflict shorts), not 4 aggregated proportions
    - Much more statistical power than regression on 4 points
    - Standardized residuals identify which conflicts deviate most
"""

import json
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats  # type: ignore
import matplotlib.pyplot as plt  # type: ignore

import config

# ACLED scores for our conflicts
ACLED_SCORES = {
    "Palestine": 2.571,
    "Myanmar": 1.900,
    "Ukraine": 1.543,
    "Mexico": 1.045,
}

# Normalize ACLED to sum to 1 (expected proportions under H₀)
ACLED_TOTAL = sum(ACLED_SCORES.values())
ACLED_NORMALIZED = {k: v / ACLED_TOTAL for k, v in ACLED_SCORES.items()}


def load_home_feed_data() -> dict[str, list[dict]]:
    """Load all Phase 2 (home feed) session data."""
    data_by_profile: dict[str, list[dict]] = defaultdict(list)

    for file in config.OUTPUT_DIR.glob("*_home_*.json"):
        # Parse filename: {profile}_home_{session_id}.json
        parts = file.stem.split("_home_")
        if len(parts) != 2:
            continue
        profile = parts[0]

        with open(file) as f:
            session_data = json.load(f)
            data_by_profile[profile].extend(session_data)

    return dict(data_by_profile)


def get_conflict_counts(shorts: list[dict]) -> dict[str, int]:
    """Get raw counts for each conflict from home feed shorts."""
    counts = {country: 0 for country in ACLED_SCORES}

    for short in shorts:
        country = short.get("related_country")
        if country and country in counts:
            counts[country] += 1

    return counts


def run_chi_square_analysis(observed_counts: dict[str, int]) -> dict:
    """
    Run chi-square goodness of fit test.
    
    H₀: Observed distribution matches ACLED proportions
    H₁: Observed distribution differs from ACLED proportions
    
    Returns dict with chi2, p_value, df, expected_counts, standardized_residuals
    """
    countries = list(ACLED_SCORES.keys())
    observed = np.array([observed_counts[c] for c in countries])
    total_observed = observed.sum()

    # Expected counts under H₀ (proportional to ACLED)
    expected_props = np.array([ACLED_NORMALIZED[c] for c in countries])
    expected = expected_props * total_observed

    # Chi-square test
    chi2, p_value = stats.chisquare(observed, f_exp=expected)
    df = len(countries) - 1

    # Standardized residuals: (O - E) / sqrt(E)
    # Values > |2| indicate significant deviation
    standardized_residuals = (observed - expected) / np.sqrt(expected)

    return {
        "chi2": chi2,
        "p_value": p_value,
        "df": df,
        "observed": dict(zip(countries, observed.tolist())),
        "expected": dict(zip(countries, expected.tolist())),
        "standardized_residuals": dict(zip(countries, standardized_residuals.tolist())),
    }


def print_results(
    observed_counts: dict[str, int],
    chi_square_results: dict,
    n_shorts: int,
    n_conflict_shorts: int,
):
    """Print formatted analysis results."""
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS RESULTS")
    print("=" * 70)

    print("\n📊 DATA SUMMARY")
    print(f"   Total home feed shorts: {n_shorts}")
    print(f"   Conflict-related shorts: {n_conflict_shorts} ({100*n_conflict_shorts/n_shorts:.1f}%)")

    # Raw counts table
    print("\n📈 OBSERVED vs EXPECTED COUNTS")
    print("-" * 70)
    print(f"   {'Conflict':<12} {'Observed':<10} {'Expected':<10} {'O/E Ratio':<12} {'Std Resid':<12}")
    print("-" * 70)
    
    for country in ACLED_SCORES:
        obs = observed_counts[country]
        exp = chi_square_results["expected"][country]
        ratio = obs / exp if exp > 0 else 0
        resid = chi_square_results["standardized_residuals"][country]
        
        # Flag significant residuals
        flag = "**" if abs(resid) > 2 else ("*" if abs(resid) > 1.96 else "")
        resid_str = f"{resid:+.2f}{flag}"
        
        print(f"   {country:<12} {obs:<10} {exp:<10.1f} {ratio:<12.2f} {resid_str:<12}")
    print("-" * 70)
    print("   * |residual| > 1.96 (p < 0.05),  ** |residual| > 2.58 (p < 0.01)")

    # Chi-square test: ACLED proportionality
    print("\n" + "=" * 70)
    print("🧪 HYPOTHESIS TEST: Proportionality to ACLED Severity")
    print("=" * 70)
    print("   H₀: Visibility is proportional to ACLED conflict severity")
    print("   H₁: Visibility is NOT proportional to ACLED severity")
    print()
    print(f"   χ² statistic:  {chi_square_results['chi2']:.2f}")
    print(f"   df:            {chi_square_results['df']}")
    p = chi_square_results['p_value']
    if p < 0.0001:
        print(f"   p-value:       {p:.2e}  (< 0.0001)")
    else:
        print(f"   p-value:       {p:.4f}")

    alpha = 0.05
    print(f"\n   α = {alpha}")
    if chi_square_results["p_value"] < alpha:
        print("   ❌ REJECT H₀: Visibility is NOT proportional to severity")
    else:
        print("   ✅ FAIL TO REJECT H₀: Cannot reject proportionality")

    # Interpretation
    print("\n" + "=" * 70)
    print("📝 INTERPRETATION")
    print("=" * 70)
    
    # Find over/under represented
    over_rep = []
    under_rep = []
    for country in ACLED_SCORES:
        resid = chi_square_results["standardized_residuals"][country]
        if resid > 1.96:
            over_rep.append((country, resid))
        elif resid < -1.96:
            under_rep.append((country, resid))
    
    if over_rep:
        print("\n   🔺 OVER-REPRESENTED (more visible than severity suggests):")
        for country, resid in sorted(over_rep, key=lambda x: -x[1]):
            obs = observed_counts[country]
            exp = chi_square_results["expected"][country]
            print(f"      • {country}: {obs} shown vs {exp:.0f} expected (resid: {resid:+.2f})")
    
    if under_rep:
        print("\n   🔻 UNDER-REPRESENTED (less visible than severity suggests):")
        for country, resid in sorted(under_rep, key=lambda x: x[1]):
            obs = observed_counts[country]
            exp = chi_square_results["expected"][country]
            print(f"      • {country}: {obs} shown vs {exp:.0f} expected (resid: {resid:+.2f})")

    print("\n" + "=" * 70)


def plot_proportions(ax, observed_counts: dict[str, int]):
    """Plot observed vs expected proportions bar chart."""
    countries = list(ACLED_SCORES.keys())
    
    # Convert to proportions (sum to 1)
    total_obs = sum(observed_counts.values())
    observed_props = [observed_counts[c] / total_obs for c in countries]
    expected_props = [ACLED_NORMALIZED[c] for c in countries]

    x = np.arange(len(countries))
    width = 0.35

    bars1 = ax.bar(x - width / 2, observed_props, width, label="Observed", color="#2563eb")
    bars2 = ax.bar(x + width / 2, expected_props, width, label="Expected (ACLED)", color="#94a3b8")

    ax.set_xlabel("Conflict Region", fontsize=12)
    ax.set_ylabel("Proportion of Conflict Shorts", fontsize=12)
    ax.set_title("Observed vs Expected Conflict Visibility", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(countries)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, max(max(observed_props), max(expected_props)) * 1.15)

    # Add percentage labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1%}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1%}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#64748b",
        )


def plot_residuals(ax, chi_square_results: dict):
    """Plot standardized residuals bar chart."""
    countries = list(ACLED_SCORES.keys())
    residuals = [chi_square_results["standardized_residuals"][c] for c in countries]

    colors = ["#22c55e" if r > 0 else "#ef4444" for r in residuals]
    bars = ax.bar(countries, residuals, color=colors)

    # Add significance lines
    ax.axhline(y=1.96, color="#fbbf24", linestyle="--", linewidth=1.5, label="p=0.05")
    ax.axhline(y=-1.96, color="#fbbf24", linestyle="--", linewidth=1.5)
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    ax.set_xlabel("Conflict Region", fontsize=12)
    ax.set_ylabel("Standardized Residual", fontsize=12)
    ax.set_title("Over/Under-Representation", fontsize=14)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels
    for bar, val in zip(bars, residuals):
        height = bar.get_height()
        ax.annotate(
            f"{val:+.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3 if height >= 0 else -12),
            textcoords="offset points",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=11,
            fontweight="bold",
        )


def create_visualization(
    observed_counts: dict[str, int],
    chi_square_results: dict,
    output_path: Path | None = None,
):
    """Create visualization with proportions bar chart."""
    fig, ax = plt.subplots(figsize=(10, 6))

    plot_proportions(ax, observed_counts)

    # Add p-value annotation
    p_val = chi_square_results["p_value"]
    if p_val < 0.0001:
        p_text = f"χ² = {chi_square_results['chi2']:.1f}, p = {p_val:.2e}"
    elif p_val < 0.001:
        p_text = f"χ² = {chi_square_results['chi2']:.1f}, p < 0.001"
    else:
        p_text = f"χ² = {chi_square_results['chi2']:.1f}, p = {p_val:.4f}"

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)
    fig.text(0.5, 0.02, p_text, ha="center", fontsize=12, style="italic")

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\n📊 Figure saved to: {output_path}")

    plt.show()


def run_analysis():
    """Main analysis function."""
    print("\n🔬 Loading Phase 2 (Home Feed) Data...")

    data = load_home_feed_data()

    if not data:
        print("❌ No home feed data found!")
        print("   Looking for files matching: *_home_*.json in", config.OUTPUT_DIR)
        print("\n   Make sure you've run Phase 2 (home feed measurement) first.")
        return

    # Combine all shorts across profiles
    all_shorts = []
    for profile, shorts in data.items():
        print(f"   {profile}: {len(shorts)} shorts")
        all_shorts.extend(shorts)

    print(f"   Total: {len(all_shorts)} shorts")

    # Get raw counts
    observed_counts = get_conflict_counts(all_shorts)

    # Count conflict-related shorts
    n_conflict = sum(observed_counts.values())

    if n_conflict == 0:
        print("❌ No conflict-related shorts found in home feed data!")
        return

    # Run chi-square test
    chi_square_results = run_chi_square_analysis(observed_counts)

    # Print results
    print_results(
        observed_counts,
        chi_square_results,
        len(all_shorts),
        n_conflict,
    )

    # Create visualization
    output_fig = config.OUTPUT_DIR / "analysis_plot.png"
    create_visualization(observed_counts, chi_square_results, output_fig)

    return {
        "observed_counts": observed_counts,
        "chi_square": chi_square_results,
        "n_shorts": len(all_shorts),
        "n_conflict_shorts": n_conflict,
    }


if __name__ == "__main__":
    run_analysis()
