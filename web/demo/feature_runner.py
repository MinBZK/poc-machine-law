"""Feature file runner for demo mode."""

import io
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def run_feature_file(feature_path: Path) -> dict[str, Any]:
    """
    Run a Gherkin feature file using behave and return structured results.

    Args:
        feature_path: Path to the .feature file

    Returns:
        Dict with execution results including status, scenarios, and output
    """
    start_time = time.time()

    # Convert to absolute path
    feature_path = feature_path.absolute()

    # Run behave with JSON formatter to get structured output
    try:
        # Use behave with JSON formatter and capture output
        result = subprocess.run(
            [
                "uv",
                "run",
                "behave",
                str(feature_path),
                "--format=json",
                "--no-capture",
                "-v",
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        execution_time = time.time() - start_time

        # Parse JSON output
        import json

        try:
            behave_output = json.loads(result.stdout) if result.stdout else []
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to plain text output
            behave_output = []

        # Process behave output into our format
        scenarios = []
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for feature in behave_output:
            for element in feature.get("elements", []):
                steps = []
                for step in element.get("steps", []):
                    step_status = step.get("result", {}).get("status", "undefined")
                    steps.append({
                        "keyword": step.get("keyword", ""),
                        "name": step.get("name", ""),
                        "status": step_status,
                        "duration": step.get("result", {}).get("duration", 0),
                        "error_message": step.get("result", {}).get("error_message"),
                    })

                # Determine scenario status
                scenario_status = "passed"
                if any(s["status"] == "failed" for s in steps):
                    scenario_status = "failed"
                    total_failed += 1
                elif any(s["status"] == "skipped" for s in steps):
                    scenario_status = "skipped"
                    total_skipped += 1
                else:
                    total_passed += 1

                scenarios.append({
                    "name": element.get("name", ""),
                    "type": element.get("type", "scenario"),
                    "status": scenario_status,
                    "steps": steps,
                })

        # If we couldn't parse JSON, try to parse plain text output
        if not scenarios and result.stdout:
            scenarios = _parse_plain_text_output(result.stdout)
            total_passed = sum(1 for s in scenarios if s["status"] == "passed")
            total_failed = sum(1 for s in scenarios if s["status"] == "failed")
            total_skipped = sum(1 for s in scenarios if s["status"] == "skipped")

        # Overall status
        if result.returncode == 0:
            overall_status = "passed"
        else:
            overall_status = "failed"

        return {
            "status": overall_status,
            "execution_time": round(execution_time, 2),
            "scenarios": scenarios,
            "summary": {
                "total": total_passed + total_failed + total_skipped,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
            },
            "stdout": result.stdout if not behave_output else "",
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "execution_time": 300,
            "scenarios": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "stdout": "",
            "stderr": "Feature execution timed out after 5 minutes",
        }
    except Exception as e:
        return {
            "status": "error",
            "execution_time": time.time() - start_time,
            "scenarios": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "stdout": "",
            "stderr": f"Error running feature: {str(e)}",
        }


def _parse_plain_text_output(output: str) -> list[dict[str, Any]]:
    """
    Parse plain text behave output as fallback.

    This is a simple parser for when JSON output is not available.
    """
    scenarios = []
    current_scenario = None
    current_steps = []

    lines = output.split("\n")
    for line in lines:
        line = line.strip()

        # Detect scenario start
        if line.startswith("Scenario:"):
            if current_scenario:
                scenarios.append({
                    "name": current_scenario,
                    "type": "scenario",
                    "status": "passed",  # Default, will be updated
                    "steps": current_steps,
                })
            current_scenario = line.replace("Scenario:", "").strip()
            current_steps = []

        # Detect step
        elif any(line.startswith(kw) for kw in ["Given ", "When ", "Then ", "And ", "But "]):
            # Extract keyword and name
            for keyword in ["Given", "When", "Then", "And", "But"]:
                if line.startswith(keyword):
                    step_name = line[len(keyword) :].strip()
                    current_steps.append({
                        "keyword": keyword,
                        "name": step_name,
                        "status": "passed",
                        "duration": 0,
                        "error_message": None,
                    })
                    break

    # Add last scenario
    if current_scenario:
        scenarios.append({
            "name": current_scenario,
            "type": "scenario",
            "status": "passed",
            "steps": current_steps,
        })

    return scenarios
