#!/usr/bin/env python3
"""Remove ui_metadata from all law content files."""

import yaml
from pathlib import Path


def remove_ui_metadata(content: dict) -> dict:
    """Remove ui_metadata section from content."""
    if 'ui_metadata' in content:
        del content['ui_metadata']
    return content


def main():
    """Process all law content files."""
    content_dir = Path(__file__).parent.parent / "laws" / "content"

    # Find all YAML files (excluding template and backups)
    yaml_files = [f for f in content_dir.glob("*.yaml")
                  if f.name != "template.yaml" and not f.name.endswith(".bak")]

    print(f"Found {len(yaml_files)} law files to clean\n")

    for yaml_file in yaml_files:
        print(f"Processing {yaml_file.name}...")

        # Read the file
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        # Remove ui_metadata
        content = remove_ui_metadata(content)

        # Write back
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, allow_unicode=True, sort_keys=False,
                      default_flow_style=False, width=120)

        print(f"  ✅ Cleaned {yaml_file.name}")

    print(f"\n✅ Removed ui_metadata from {len(yaml_files)} files!")


if __name__ == "__main__":
    main()
