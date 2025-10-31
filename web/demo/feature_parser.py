"""Gherkin feature file parser for demo mode."""

import re
from pathlib import Path
from typing import Any


def parse_feature_file(feature_path: Path) -> dict[str, Any]:
    """
    Parse a Gherkin feature file into structured data.

    Args:
        feature_path: Path to the .feature file

    Returns:
        Dict with feature metadata, background, and scenarios
    """
    with open(feature_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    result = {
        "path": str(feature_path),
        "feature": None,
        "background": None,
        "scenarios": [],
        "raw_content": content,
    }

    current_section = None
    current_scenario = None
    current_steps = []
    feature_tags = []  # Tags that apply to all scenarios
    pending_tags = []  # Tags for the next scenario

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Parse tags (lines starting with @)
        if stripped.startswith("@"):
            tags = [tag.strip() for tag in stripped.split() if tag.startswith("@")]
            # Remove @ prefix
            tags = [tag[1:] for tag in tags]
            pending_tags.extend(tags)
            continue

        # Feature line
        if stripped.startswith("Feature:"):
            result["feature"] = {
                "name": stripped[8:].strip(),
                "description": [],
                "line_number": i + 1,
                "tags": pending_tags.copy(),  # Store feature-level tags
            }
            feature_tags = pending_tags.copy()
            pending_tags = []
            current_section = "feature_description"
            continue

        # Background
        if stripped.startswith("Background:"):
            result["background"] = {
                "steps": [],
                "line_number": i + 1,
            }
            current_section = "background"
            current_steps = result["background"]["steps"]
            continue

        # Scenario or Scenario Outline
        if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
            # Save previous scenario if exists
            if current_scenario:
                result["scenarios"].append(current_scenario)

            scenario_type = "outline" if "Outline" in stripped else "normal"
            name_start = stripped.index(":") + 1
            # Combine feature-level tags with scenario-specific tags
            all_tags = feature_tags + pending_tags
            current_scenario = {
                "type": scenario_type,
                "name": stripped[name_start:].strip(),
                "steps": [],
                "line_number": i + 1,
                "tags": all_tags,
            }
            pending_tags = []  # Clear pending tags after using them
            current_section = "scenario"
            current_steps = current_scenario["steps"]
            continue

        # Steps (Given, When, Then, And, But)
        if current_section in ("background", "scenario"):
            step_match = re.match(r"^(Given|When|Then|And|But)\s+(.+)", stripped)
            if step_match:
                keyword, text = step_match.groups()
                current_steps.append({
                    "keyword": keyword,
                    "text": text,
                    "line_number": i + 1,
                })
                continue

            # Table rows
            if stripped.startswith("|") and current_steps:
                if "table" not in current_steps[-1]:
                    current_steps[-1]["table"] = []
                # Parse table row
                cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
                current_steps[-1]["table"].append(cells)
                continue

            # Examples for Scenario Outline
            if stripped.startswith("Examples:") and current_scenario:
                current_scenario["examples"] = {
                    "line_number": i + 1,
                    "table": [],
                }
                current_section = "examples"
                continue

        # Examples table rows
        if current_section == "examples" and stripped.startswith("|"):
            if "examples" in current_scenario:
                cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
                current_scenario["examples"]["table"].append(cells)
            continue

        # Feature description (multi-line text after Feature:)
        if current_section == "feature_description" and stripped and not stripped.startswith("@"):
            result["feature"]["description"].append(stripped)

    # Save last scenario
    if current_scenario:
        result["scenarios"].append(current_scenario)

    return result


def discover_feature_files(base_dirs: list[Path]) -> dict[str, list[dict[str, Any]]]:
    """
    Discover all .feature files in multiple directories.
    Filters out scenarios tagged with @ui or @browser.

    Args:
        base_dirs: List of directories to search

    Returns:
        Dict grouped by directory path: {"group_name": [feature_info, ...]}
    """
    from collections import defaultdict

    grouped_features = defaultdict(list)
    excluded_tags = {"ui", "browser"}

    for base_dir in base_dirs:
        if not base_dir.exists():
            continue

        for feature_file in sorted(base_dir.rglob("*.feature")):
            # Parse just enough to get the feature name
            try:
                parsed = parse_feature_file(feature_file)
                if not parsed["feature"]:
                    continue

                # Filter out scenarios with excluded tags
                runnable_scenarios = [
                    scenario
                    for scenario in parsed["scenarios"]
                    if not any(tag in excluded_tags for tag in scenario.get("tags", []))
                ]

                # Skip features with no runnable scenarios
                if not runnable_scenarios:
                    continue

                # Determine group name
                relative_path = feature_file.relative_to(base_dir)
                parent = relative_path.parent

                if str(parent) == ".":
                    group = "Root Features"
                else:
                    group = str(parent)

                feature_info = {
                    "path": str(feature_file),
                    "relative_path": str(relative_path),
                    "name": parsed["feature"]["name"],
                    "file_name": feature_file.stem,
                    "scenario_count": len(runnable_scenarios),  # Count only runnable scenarios
                    "total_scenarios": len(parsed["scenarios"]),
                    "filtered_count": len(parsed["scenarios"]) - len(runnable_scenarios),
                }

                grouped_features[group].append(feature_info)

            except Exception:
                # Skip files that can't be parsed
                continue

    return dict(sorted(grouped_features.items()))
