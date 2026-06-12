#!/usr/bin/env python3
"""Capture baseline BDD test results for regression comparison.

Runs every BDD scenario (excluding @ui scenarios) through
the Python engine and records the full engine output for each scenario.
The result is a JSON file that serves as a regression baseline: any future
engine change can be diffed against it.

Usage:
    uv run tests/baseline/capture_baseline.py [--output FILE] [--features DIR...]

The output JSON has this structure:
    {
        "metadata": { "timestamp": "...", "python_version": "...", "git_sha": "..." },
        "scenarios": [
            {
                "feature_file": "features/toeslagen/...",
                "feature_name": "Berekening Zorgtoeslag 2025",
                "scenario_name": "Persoon onder 18 ...",
                "status": "passed",
                "engine_result": {
                    "output": { ... },
                    "requirements_met": true,
                    "missing_required": false,
                    "input": { ... }
                },
                "error": null
            },
            ...
        ]
    }
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import textwrap
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = REPO_ROOT / "features"

# Feature subdirectories to scan (excludes web/ which needs Playwright)
DEFAULT_FEATURE_DIRS = [
    "toeslagen",
    "sociale_zekerheid",
    "burgerlijk_wetboek",
    "bestuursrecht",
    "kernenergiewet",
    "belastingen",
    "overig",
    "integratie",
]


def git_sha() -> str:
    """Return short git SHA of HEAD, or 'unknown'."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO_ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def build_environment_overlay(collector_path: str) -> str:
    """Create a temporary environment.py that wraps the real one and dumps results."""
    return textwrap.dedent(f"""\
        \"\"\"Overlay environment that captures engine results after each scenario.\"\"\"
        import json
        import importlib.util
        import sys
        from pathlib import Path

        # Import the real environment module
        _real_env_path = Path(__file__).resolve().parent / "_real_environment.py"
        _spec = importlib.util.spec_from_file_location("_real_environment", _real_env_path)
        _real_env = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_real_env)

        _collector_path = {collector_path!r}
        _collected = []


        def _serialize_result(result):
            \"\"\"Serialize a RuleResult to a JSON-safe dict.\"\"\"
            if result is None:
                return None
            output = result.output
            # Make sure all output values are JSON-serializable
            safe_output = {{}}
            for k, v in (output or {{}}).items():
                try:
                    json.dumps(v)
                    safe_output[k] = v
                except (TypeError, ValueError):
                    safe_output[k] = str(v)
            return {{
                "output": safe_output,
                "requirements_met": result.requirements_met,
                "missing_required": result.missing_required,
                "input": result.input if hasattr(result, "input") else {{}},
            }}


        def before_all(context):
            _real_env.before_all(context)


        def after_all(context):
            # Write collected results before cleanup
            with open(_collector_path, "w") as f:
                json.dump(_collected, f, indent=2, default=str, ensure_ascii=False)
            _real_env.after_all(context)


        def before_scenario(context, scenario):
            _real_env.before_scenario(context, scenario)


        def after_scenario(context, scenario):
            entry = {{
                "feature_file": str(scenario.feature.filename),
                "feature_name": scenario.feature.name,
                "scenario_name": scenario.name,
                "status": scenario.status.name if hasattr(scenario.status, "name") else str(scenario.status),
                "engine_result": _serialize_result(getattr(context, "result", None)),
                "error": None,
            }}
            # Capture error info if the scenario failed
            if scenario.status.name != "passed":
                for step in scenario.steps:
                    if step.status.name == "failed" and step.error_message:
                        entry["error"] = step.error_message
                        break
            _collected.append(entry)
            _real_env.after_scenario(context, scenario)
    """)


def run_behave(feature_dirs: list[str], output_file: Path) -> tuple[list[dict], int]:
    """Run behave with the overlay environment and collect results.

    Returns (collected_scenarios, return_code).
    """
    # Paths
    env_original = FEATURES_DIR / "environment.py"
    env_backup = FEATURES_DIR / "_real_environment.py"
    env_overlay = FEATURES_DIR / "environment.py"

    # Temp file for the collector output
    collector_fd, collector_path = tempfile.mkstemp(suffix=".json", prefix="baseline_")
    os.close(collector_fd)

    # Generate overlay content
    overlay_content = build_environment_overlay(collector_path)

    # Read original environment
    original_content = env_original.read_text()

    try:
        # Swap in the overlay
        env_backup.write_text(original_content)
        env_overlay.write_text(overlay_content)

        # Build behave command
        dirs = [str(FEATURES_DIR / d) for d in feature_dirs]
        cmd = [
            sys.executable,
            "-m",
            "behave",
            *dirs,
            "--no-capture",
            "--define",
            "log_level=WARNING",
            "--tags=~@ui",
            "--format",
            "progress",
        ]

        print(f"Running: {' '.join(cmd)}")
        print(f"Scanning directories: {', '.join(feature_dirs)}")
        print()

        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            text=True,
            capture_output=False,
        )

        # Read collected results
        try:
            with open(collector_path) as f:
                collected = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            collected = []
            print("WARNING: Could not read collected results from overlay.")

        return collected, result.returncode

    finally:
        # Restore original environment
        env_overlay.write_text(original_content)
        if env_backup.exists():
            env_backup.unlink()
        # Clean up temp file
        try:
            os.unlink(collector_path)
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture BDD regression baseline")
    parser.add_argument(
        "--output",
        "-o",
        default="tests/baseline/results.json",
        help="Output JSON file (default: tests/baseline/results.json)",
    )
    parser.add_argument(
        "--features",
        nargs="*",
        default=DEFAULT_FEATURE_DIRS,
        help="Feature subdirectories to include (default: all except web/)",
    )
    args = parser.parse_args()

    output_path = (REPO_ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Capturing BDD baseline results")
    print("=" * 70)
    print()

    collected, returncode = run_behave(args.features, output_path)

    # Build metadata
    metadata = {
        "timestamp": datetime.now(UTC).isoformat(),
        "python_version": platform.python_version(),
        "git_sha": git_sha(),
        "behave_return_code": returncode,
    }

    # Compute summary
    statuses = {}
    for s in collected:
        st = s.get("status", "unknown")
        statuses[st] = statuses.get(st, 0) + 1

    baseline = {
        "metadata": metadata,
        "summary": {
            "total_scenarios": len(collected),
            **statuses,
        },
        "scenarios": collected,
    }

    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2, default=str, ensure_ascii=False)

    print()
    print("=" * 70)
    print(f"Baseline captured: {output_path}")
    print(f"  Total scenarios: {len(collected)}")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")
    print(f"  Behave exit code: {returncode}")
    print("=" * 70)

    # Exit with the same code as behave so CI can gate on it
    sys.exit(returncode)


if __name__ == "__main__":
    main()
