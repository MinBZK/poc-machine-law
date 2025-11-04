#!/usr/bin/env python3
"""Validate DMN files for structure and content."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DMN_NS = {"dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/"}


def validate_dmn_file(filepath: Path) -> tuple[bool, list[str]]:
    """Validate a DMN file and return success status and messages."""
    messages = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Check root element
        if not root.tag.endswith("definitions"):
            messages.append(f"ERROR: Root element is not 'definitions': {root.tag}")
            return False, messages

        # Check namespace
        if "https://www.omg.org/spec/DMN/20191111/MODEL/" not in root.tag:
            messages.append(f"WARNING: DMN namespace may be incorrect: {root.tag}")

        # Find decisions
        decisions = root.findall(".//dmn:decision", DMN_NS)
        if not decisions:
            messages.append("ERROR: No decisions found in DMN file")
            return False, messages

        messages.append(f"OK: Found {len(decisions)} decision(s)")

        # Validate each decision
        for decision in decisions:
            decision_name = decision.get("name", decision.get("id", "unnamed"))
            messages.append(f"  - Decision: {decision_name}")

            # Check for decision logic
            decision_tables = decision.findall(".//dmn:decisionTable", DMN_NS)
            literal_expressions = decision.findall(".//dmn:literalExpression", DMN_NS)
            invocations = decision.findall(".//dmn:invocation", DMN_NS)

            if not (decision_tables or literal_expressions or invocations):
                messages.append(f"    WARNING: Decision '{decision_name}' has no decision logic")

        return True, messages

    except ET.ParseError as e:
        messages.append(f"ERROR: XML parsing failed: {e}")
        return False, messages
    except Exception as e:
        messages.append(f"ERROR: Validation failed: {e}")
        return False, messages


def main():
    """Validate all DMN files in the dmn/ directory."""
    dmn_dir = Path("dmn")
    if not dmn_dir.exists():
        print("ERROR: dmn/ directory not found")
        return 1

    dmn_files = list(dmn_dir.glob("*.dmn"))
    if not dmn_files:
        print("ERROR: No DMN files found in dmn/")
        return 1

    print(f"Validating {len(dmn_files)} DMN file(s)...\n")

    all_valid = True
    for dmn_file in sorted(dmn_files):
        print(f"{dmn_file.name}:")
        is_valid, messages = validate_dmn_file(dmn_file)
        for msg in messages:
            print(f"  {msg}")
        print()

        if not is_valid:
            all_valid = False

    if all_valid:
        print("All DMN files are valid!")
        return 0
    else:
        print("Some DMN files have validation errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
