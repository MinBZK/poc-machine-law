#!/usr/bin/env python3
"""Add missing schema-required fields to all law YAML files.

The regelrecht v0.5.1 schema requires certain fields depending on the
regulatory_layer. This script walks all YAML files in laws/ and adds
any missing required fields:

1. publication_date (always required) - defaults to valid_from
2. url (always required) - extracted from first article's url (strip fragment)
3. bwb_id (required for WET, AMVB, MINISTERIELE_REGELING, GRONDWET) - extracted from article URLs
4. gemeente_code (required for GEMEENTELIJKE_VERORDENING)
5. officiele_titel (required for GEMEENTELIJKE_VERORDENING)
"""

import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # Very wide to avoid rewrapping existing lines

# Rotterdam CBS municipality code
GEMEENTE_CODES = {
    "GEMEENTE_ROTTERDAM": "GM0599",
}

# Regulatory layers that require bwb_id
BWB_LAYERS = {"WET", "AMVB", "MINISTERIELE_REGELING", "GRONDWET"}

# Regulatory layers that require gemeente_code and officiele_titel
GEMEENTE_LAYERS = {"GEMEENTELIJKE_VERORDENING"}

BWB_PATTERN = re.compile(r"(BWBR\d{7})")


def extract_bwb_id(data: dict) -> str | None:
    """Extract BWB ID from the first article's URL."""
    articles = data.get("articles", [])
    for article in articles:
        url = article.get("url", "")
        match = BWB_PATTERN.search(str(url))
        if match:
            return match.group(1)
    return None


def extract_base_url(data: dict) -> str | None:
    """Extract the base URL from the first article's URL (strip fragment)."""
    articles = data.get("articles", [])
    for article in articles:
        url = article.get("url", "")
        if url:
            return str(url).split("#")[0]
    return None


def guess_gemeente_code(data: dict) -> str | None:
    """Guess the gemeente code from the service field."""
    service = str(data.get("service", ""))
    return GEMEENTE_CODES.get(service)


def insert_after_key(data: dict, after_key: str, new_key: str, new_value: str) -> None:
    """Insert a key-value pair after a specific key in a ruamel.yaml CommentedMap."""
    keys = list(data.keys())
    if after_key in keys:
        idx = keys.index(after_key) + 1
        data.insert(idx, new_key, new_value)
    else:
        # Fallback: insert before 'articles' if possible
        if "articles" in keys:
            idx = keys.index("articles")
            data.insert(idx, new_key, new_value)
        else:
            data[new_key] = new_value


def process_file(yaml_path: Path) -> list[str]:
    """Process a single YAML file and add missing fields. Returns list of changes made."""
    with open(yaml_path) as f:
        data = yaml.load(f)

    if not isinstance(data, dict):
        return []

    changes = []
    layer = str(data.get("regulatory_layer", ""))

    # 1. publication_date
    if "publication_date" not in data:
        valid_from = str(data.get("valid_from", ""))
        if valid_from:
            insert_after_key(data, "regulatory_layer", "publication_date", valid_from)
            changes.append(f"  + publication_date: {valid_from}")
        else:
            changes.append("  ! WARNING: no valid_from to use for publication_date")

    # 2. url
    if "url" not in data:
        base_url = extract_base_url(data)
        if base_url:
            insert_after_key(data, "name", "url", base_url)
            changes.append(f"  + url: {base_url}")
        else:
            changes.append("  ! WARNING: could not extract base URL from articles")

    # 3. bwb_id (conditional)
    if layer in BWB_LAYERS and "bwb_id" not in data:
        bwb_id = extract_bwb_id(data)
        if bwb_id:
            insert_after_key(data, "name", "bwb_id", bwb_id)
            changes.append(f"  + bwb_id: {bwb_id}")
        else:
            changes.append(f"  ! WARNING: regulatory_layer={layer} requires bwb_id but none found in article URLs")

    # 4. gemeente_code (conditional)
    if layer in GEMEENTE_LAYERS and "gemeente_code" not in data:
        code = guess_gemeente_code(data)
        if code:
            insert_after_key(data, "name", "gemeente_code", code)
            changes.append(f"  + gemeente_code: {code}")
        else:
            changes.append(f"  ! WARNING: regulatory_layer={layer} requires gemeente_code but could not determine it")

    # 5. officiele_titel (conditional)
    if layer in GEMEENTE_LAYERS and "officiele_titel" not in data:
        name = str(data.get("name", ""))
        if name:
            insert_after_key(data, "gemeente_code" if "gemeente_code" in data else "name", "officiele_titel", name)
            changes.append(f"  + officiele_titel: {name}")
        else:
            changes.append(f"  ! WARNING: regulatory_layer={layer} requires officiele_titel but no name field found")

    if changes:
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)

    return changes


def main() -> None:
    base_dir = Path("laws")
    if not base_dir.exists():
        print("Error: laws/ directory not found. Run from repo root.")
        sys.exit(1)

    yaml_files = sorted(base_dir.rglob("*.yaml"))
    print(f"Found {len(yaml_files)} YAML files\n")

    total_changes = 0
    files_changed = 0

    for yaml_path in yaml_files:
        changes = process_file(yaml_path)
        if changes:
            files_changed += 1
            total_changes += len(changes)
            print(f"{yaml_path}:")
            for change in changes:
                print(change)
            print()

    if total_changes == 0:
        print("All files already have the required fields.")
    else:
        print(f"\nSummary: {total_changes} field(s) added across {files_changed} file(s).")


if __name__ == "__main__":
    main()
