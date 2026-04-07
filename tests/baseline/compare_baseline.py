#!/usr/bin/env python3
"""Compare a new BDD run against a saved baseline to detect regressions.

Usage:
    # First capture a new run:
    uv run tests/baseline/capture_baseline.py --output tests/baseline/new_results.json

    # Then compare against the baseline:
    uv run tests/baseline/compare_baseline.py tests/baseline/results.json tests/baseline/new_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_baseline(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def scenario_key(scenario: dict) -> str:
    """Unique key for a scenario."""
    return f"{scenario['feature_file']}::{scenario['scenario_name']}"


def diff_outputs(old_output: dict | None, new_output: dict | None) -> list[str]:
    """Compare two output dicts and return a list of differences."""
    if old_output is None and new_output is None:
        return []
    if old_output is None:
        return ["old had no engine result, new does"]
    if new_output is None:
        return ["old had engine result, new does not"]

    diffs = []
    old_out = old_output.get("output", {})
    new_out = new_output.get("output", {})

    all_keys = sorted(set(old_out.keys()) | set(new_out.keys()))
    for key in all_keys:
        if key not in old_out:
            diffs.append(f"  + new output key '{key}' = {new_out[key]!r}")
        elif key not in new_out:
            diffs.append(f"  - removed output key '{key}' (was {old_out[key]!r})")
        elif old_out[key] != new_out[key]:
            diffs.append(f"  ~ '{key}': {old_out[key]!r} -> {new_out[key]!r}")

    # Compare top-level flags
    for flag in ["requirements_met", "missing_required"]:
        old_val = old_output.get(flag)
        new_val = new_output.get(flag)
        if old_val != new_val:
            diffs.append(f"  ~ {flag}: {old_val!r} -> {new_val!r}")

    return diffs


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare BDD baselines")
    parser.add_argument("baseline", type=Path, help="Path to baseline results.json")
    parser.add_argument("new", type=Path, help="Path to new results.json")
    parser.add_argument("--ignore-status", action="store_true", help="Only compare output values, ignore pass/fail")
    args = parser.parse_args()

    old = load_baseline(args.baseline)
    new = load_baseline(args.new)

    old_scenarios = {scenario_key(s): s for s in old["scenarios"]}
    new_scenarios = {scenario_key(s): s for s in new["scenarios"]}

    old_keys = set(old_scenarios.keys())
    new_keys = set(new_scenarios.keys())

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    common = sorted(old_keys & new_keys)

    regressions = []
    value_changes = []

    for key in common:
        old_s = old_scenarios[key]
        new_s = new_scenarios[key]

        # Status changes
        if not args.ignore_status and old_s["status"] != new_s["status"]:
            regressions.append((key, f"status: {old_s['status']} -> {new_s['status']}"))

        # Output value changes
        diffs = diff_outputs(old_s.get("engine_result"), new_s.get("engine_result"))
        if diffs:
            value_changes.append((key, diffs))

    # Report
    print(f"Baseline:  {args.baseline} ({old['summary']['total_scenarios']} scenarios)")
    print(f"New:       {args.new} ({new['summary']['total_scenarios']} scenarios)")
    print()

    if added:
        print(f"ADDED scenarios ({len(added)}):")
        for k in added:
            print(f"  + {k}")
        print()

    if removed:
        print(f"REMOVED scenarios ({len(removed)}):")
        for k in removed:
            print(f"  - {k}")
        print()

    if regressions:
        print(f"STATUS REGRESSIONS ({len(regressions)}):")
        for key, msg in regressions:
            print(f"  {key}")
            print(f"    {msg}")
        print()

    if value_changes:
        print(f"OUTPUT VALUE CHANGES ({len(value_changes)}):")
        for key, diffs in value_changes:
            print(f"  {key}")
            for d in diffs:
                print(f"    {d}")
        print()

    if not added and not removed and not regressions and not value_changes:
        print("No differences found. Baseline matches.")
        sys.exit(0)
    else:
        total = len(added) + len(removed) + len(regressions) + len(value_changes)
        print(f"Total differences: {total}")
        sys.exit(1)


if __name__ == "__main__":
    main()
