#!/usr/bin/env python3
"""Convert requirements blocks in YAML law files to explicit boolean output actions.

The regelrecht v0.5.1 schema does not have a `requirements` concept in `execution`.
Eligibility logic should be modeled as computed boolean outputs. This script:

1. For each YAML file with a `requirements` block in execution:
   a. Reads the requirements structure
   b. Converts it to an AND/OR operation tree
   c. Adds a new output: {name: voldoet_aan_voorwaarden, type: boolean}
   d. Adds a new action as the FIRST action
   e. Removes the requirements block from execution

2. Conversion rules:
   - requirements with `all:` blocks -> AND operation with conditions
   - requirements with `or:` / `any:` blocks -> OR operation with conditions
   - Single requirement operations -> used directly
   - legal_basis on requirements -> stripped (informal metadata, not part of the operation)

Usage:
    uv run python script/convert_requirements.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # Avoid rewrapping existing lines

LAWS_DIR = Path(__file__).parent.parent / "laws"


def strip_legal_basis(item):
    """Remove legal_basis keys from a requirement item (recursively for nested dicts)."""
    if isinstance(item, dict):
        return {k: strip_legal_basis(v) for k, v in item.items() if k != "legal_basis"}
    if isinstance(item, list):
        return [strip_legal_basis(i) for i in item]
    return item


def convert_requirement_item(item: dict) -> dict:
    """Convert a single requirement item into an operation tree.

    Requirements items can be:
    - {all: [conditions...]} -> {operation: AND, conditions: [...]}
    - {or: [conditions...]} -> {operation: OR, conditions: [...]}
    - {any: [conditions...]} -> {operation: OR, conditions: [...]}
    - {operation: ..., ...} -> pass through (strip legal_basis)
    - {subject: ..., operation: ..., value: ...} -> pass through (strip legal_basis)
    """
    # Strip legal_basis from the item first
    item = strip_legal_basis(item)

    if "all" in item:
        conditions = [convert_requirement_item(c) for c in item["all"]]
        return {"operation": "AND", "conditions": conditions}
    if "or" in item:
        conditions = [convert_requirement_item(c) for c in item["or"]]
        return {"operation": "OR", "conditions": conditions}
    if "any" in item:
        conditions = [convert_requirement_item(c) for c in item["any"]]
        return {"operation": "OR", "conditions": conditions}

    # Direct operation - already stripped of legal_basis
    return dict(item)


def convert_requirements_to_action_value(requirements: list) -> dict:
    """Convert a requirements list into a single action value (operation tree).

    The requirements list is a list of requirement items that are implicitly ANDed.
    Each item can contain all/or/any blocks or be a direct operation.
    """
    converted_items = []

    for req in requirements:
        converted = convert_requirement_item(req)
        if converted:
            converted_items.append(converted)

    if not converted_items:
        return {"operation": "EQUALS", "subject": True, "value": True}

    if len(converted_items) == 1:
        return converted_items[0]

    # Multiple top-level requirements are implicitly ANDed
    return {"operation": "AND", "conditions": converted_items}


def to_commented(obj):
    """Convert plain dicts/lists to ruamel.yaml CommentedMap/CommentedSeq for round-trip output."""
    if isinstance(obj, dict):
        cm = CommentedMap()
        for k, v in obj.items():
            cm[k] = to_commented(v)
        return cm
    if isinstance(obj, list):
        cs = CommentedSeq()
        for item in obj:
            cs.append(to_commented(item))
        return cs
    return obj


def process_yaml_file(file_path: Path, dry_run: bool = False) -> bool:
    """Process a single YAML file, converting requirements to voldoet_aan_voorwaarden action.

    Returns True if the file was modified.
    """
    with open(file_path) as f:
        data = yaml.load(f)

    if not data or "articles" not in data:
        return False

    modified = False

    for article in data.get("articles", []):
        mr = article.get("machine_readable")
        if not mr:
            continue

        execution = mr.get("execution")
        if not execution:
            continue

        requirements = execution.get("requirements")
        if not requirements:
            continue

        # Check if voldoet_aan_voorwaarden output already exists
        outputs = execution.get("output", [])
        has_vav_output = any(
            (o.get("name") if isinstance(o, dict) else None) == "voldoet_aan_voorwaarden" for o in outputs
        )

        # Check if voldoet_aan_voorwaarden action already exists
        actions = execution.get("actions", [])
        has_vav_action = any(
            (a.get("output") if isinstance(a, dict) else None) == "voldoet_aan_voorwaarden" for a in actions
        )

        if has_vav_output and has_vav_action:
            continue

        # Convert requirements list (plain Python objects) to action value
        # First, extract requirements as plain dicts (ruamel types -> plain)
        plain_reqs = _to_plain(requirements)
        action_value = convert_requirements_to_action_value(plain_reqs)

        # Add voldoet_aan_voorwaarden output (as first output)
        if not has_vav_output:
            vav_output = to_commented({"name": "voldoet_aan_voorwaarden", "type": "boolean"})
            outputs.insert(0, vav_output)

        # Add voldoet_aan_voorwaarden action (as first action)
        if not has_vav_action:
            vav_action = to_commented({"output": "voldoet_aan_voorwaarden", "value": action_value})
            actions.insert(0, vav_action)

        # Remove requirements block
        del execution["requirements"]

        modified = True

    if modified and not dry_run:
        with open(file_path, "w") as f:
            yaml.dump(data, f)

    return modified


def _to_plain(obj):
    """Convert ruamel.yaml types to plain Python types."""
    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(i) for i in obj]
    return obj


def main():
    parser = argparse.ArgumentParser(description="Convert requirements blocks to voldoet_aan_voorwaarden actions")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify files, just report what would change")
    args = parser.parse_args()

    yaml_files = sorted(LAWS_DIR.rglob("*.yaml"))
    modified_count = 0
    skipped_count = 0

    for file_path in yaml_files:
        try:
            if process_yaml_file(file_path, dry_run=args.dry_run):
                modified_count += 1
                action = "Would modify" if args.dry_run else "Modified"
                print(f"  {action}: {file_path.relative_to(LAWS_DIR.parent)}")
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  ERROR: {file_path.relative_to(LAWS_DIR.parent)}: {e}", file=sys.stderr)

    print(f"\n{'Dry run: ' if args.dry_run else ''}Modified {modified_count} files, skipped {skipped_count} files")


if __name__ == "__main__":
    main()
