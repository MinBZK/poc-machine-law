#!/usr/bin/env python3
"""Remove cross_references from all law content files."""

import yaml
from pathlib import Path


def remove_cross_references(content: dict) -> dict:
    """Remove cross_references section from content."""
    if 'cross_references' in content:
        del content['cross_references']
    return content


def process_file(file_path: Path) -> None:
    """Process a single YAML file to remove cross_references."""
    print(f"Processing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)

    # Remove cross_references
    content = remove_cross_references(content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"  ✅ Cleaned {file_path.name}")


def main():
    """Main function to process all law content files."""
    content_dir = Path(__file__).parent.parent / "laws" / "content"

    # Find all YAML files
    yaml_files = list(content_dir.glob("*.yaml"))

    # Skip template.yaml
    yaml_files = [f for f in yaml_files if f.name != "template.yaml"]

    print(f"Found {len(yaml_files)} law files to clean\n")

    for yaml_file in yaml_files:
        process_file(yaml_file)

    print(f"\n✅ Removed cross_references from {len(yaml_files)} files!")


if __name__ == "__main__":
    main()
