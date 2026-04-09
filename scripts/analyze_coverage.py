# /// script
# requires-python = ">=3.13"
# dependencies = ["pytest-cov>=6.0.0", "rich>=13.0.0"]
# ///
"""Analyze test coverage for documentation prioritization."""

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def run_coverage() -> tuple[int, str, str]:
    """Run pytest with coverage and return results."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "--cov=packages/stogger/src/stogger",
            "--cov-report=json:coverage.json",
            "-q",
            "--tb=no",
            "-x",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def analyze_coverage(coverage_file: str = "coverage.json") -> dict:
    """Parse coverage JSON and categorize modules."""
    with Path(coverage_file).open(encoding="utf-8") as f:
        data = json.load(f)

    tiers = {"tier1_full": [], "tier2_basic": [], "tier3_minimal": []}

    files = data.get("files", {})
    for file_path, file_data in files.items():
        module = file_path.replace("packages/stogger/src/stogger/", "").replace(".py", "").replace("/", ".")
        if module == "__init__":
            continue

        coverage = file_data["summary"]["percent_covered"]
        missing = file_data.get("missing_lines", [])

        entry = {
            "module": module,
            "file": file_path,
            "coverage": coverage,
            "missing_lines": len(missing),
        }

        if coverage >= 80:
            tiers["tier1_full"].append(entry)
        elif coverage >= 40:
            tiers["tier2_basic"].append(entry)
        else:
            tiers["tier3_minimal"].append(entry)

    # Sort each tier by coverage (high to low)
    for tier_list in tiers.values():
        tier_list.sort(key=lambda x: -x["coverage"])

    return tiers


def print_report(tiers: dict) -> None:
    """Print coverage report for documentation planning."""
    console.print("=" * 70, style="bold")
    console.print("COVERAGE-BASED DOCUMENTATION PRIORITIZATION", style="bold")
    console.print("=" * 70, style="bold")

    console.print("\n📊 TIER 1: Full Documentation (≥80% coverage)")
    console.print("-" * 50)
    if tiers["tier1_full"]:
        for entry in tiers["tier1_full"]:
            console.print(f"  ✅ {entry['module']:<35} {entry['coverage']:>5.1f}%")
    else:
        console.print("  (no modules)")

    console.print("\n📝 TIER 2: Basic Documentation (40-80% coverage)")
    console.print("-" * 50)
    if tiers["tier2_basic"]:
        for entry in tiers["tier2_basic"]:
            console.print(f"  ⚠️  {entry['module']:<35} {entry['coverage']:>5.1f}%")
    else:
        console.print("  (no modules)")

    console.print("\n🚨 TIER 3: Minimal Documentation (<40% coverage)")
    console.print("-" * 50)
    if tiers["tier3_minimal"]:
        for entry in tiers["tier3_minimal"]:
            console.print(f"  ❌ {entry['module']:<35} {entry['coverage']:>5.1f}%")
    else:
        console.print("  (no modules)")

    # Summary
    total = sum(len(tier_list) for tier_list in tiers.values())
    t1 = len(tiers["tier1_full"])
    t2 = len(tiers["tier2_basic"])
    t3 = len(tiers["tier3_minimal"])

    console.print("\n" + "=" * 70)
    console.print(f"SUMMARY: {total} modules | Tier 1: {t1} | Tier 2: {t2} | Tier 3: {t3}")
    console.print("=" * 70)


def generate_coverage_json_for_docs(tiers: dict, output_path: str = "docs/_data/coverage.json") -> None:
    """Generate coverage data for documentation use."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as f:
        json.dump(tiers, f, indent=2)

    console.print(f"\n📄 Coverage data written to {output_path}")


def main():
    """Main entry point."""
    # Check if coverage.json exists
    if not Path("coverage.json").exists():
        console.print("Running pytest with coverage...")
        returncode, _stdout, stderr = run_coverage()
        if returncode not in {0, 1}:  # pytest returns 1 for test failures, which is ok
            console.print(f"Warning: pytest exited with {returncode}")
            if stderr:
                console.print(f"stderr: {stderr}")

    if not Path("coverage.json").exists():
        console.print("[red]ERROR: coverage.json not found after running pytest[/red]")
        sys.exit(1)

    tiers = analyze_coverage()
    print_report(tiers)
    generate_coverage_json_for_docs(tiers)

    return tiers


if __name__ == "__main__":
    main()
