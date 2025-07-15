#!/usr/bin/env python3
"""Remove yaml_references from law content files since they're now generated at runtime."""

import yaml
from pathlib import Path


def remove_yaml_references(content: dict) -> dict:
    """Recursively remove yaml_references from the content structure."""
    if isinstance(content, dict):
        # Remove yaml_references key if it exists
        if 'yaml_references' in content:
            del content['yaml_references']

        # Recursively process all values
        for key, value in content.items():
            if isinstance(value, (dict, list)):
                remove_yaml_references(value)

    elif isinstance(content, list):
        # Process each item in the list
        for item in content:
            if isinstance(item, (dict, list)):
                remove_yaml_references(item)

    return content


def process_file(file_path: Path) -> None:
    """Process a single YAML file to remove yaml_references."""
    print(f"Processing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)

    # Remove yaml_references
    content = remove_yaml_references(content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"  Cleaned {file_path.name}")


def main():
    """Main function to process all law content files."""
    content_dir = Path(__file__).parent.parent / "laws" / "content"

    # Find all YAML files with yaml_references
    yaml_files = list(content_dir.glob("*.yaml"))

    files_with_references = []
    for yaml_file in yaml_files:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'yaml_references' in content:
                files_with_references.append(yaml_file)

    print(f"Found {len(files_with_references)} files with yaml_references:")
    for f in files_with_references:
        print(f"  - {f.name}")

    if files_with_references:
        print("\nRemoving yaml_references from files...")
        for yaml_file in files_with_references:
            process_file(yaml_file)
        print(f"\nCleaned {len(files_with_references)} files!")
    else:
        print("No files with yaml_references found.")


if __name__ == "__main__":
    main()
