#!/usr/bin/env python3
"""Create law content files for laws that have YAML implementations but no content file yet."""

import yaml
from pathlib import Path
from datetime import datetime


def main():
    """Create missing law content files."""
    laws_dir = Path(__file__).parent.parent / "law"
    content_dir = Path(__file__).parent.parent / "laws" / "content"
    bwb_mapping_path = Path(__file__).parent.parent / "laws" / "bwb_mapping.yaml"

    # Load BWB mapping
    with open(bwb_mapping_path, 'r', encoding='utf-8') as f:
        bwb_mapping = yaml.safe_load(f)

    # Find all YAML files and extract their BWB IDs
    yaml_files_by_bwb = {}

    for yaml_file in laws_dir.rglob("*.yaml"):
        if "__pycache__" in str(yaml_file):
            continue

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            # Get BWB ID from legal_basis
            if 'legal_basis' in content and 'bwb_id' in content['legal_basis']:
                bwb_id = content['legal_basis']['bwb_id']
                rel_path = yaml_file.relative_to(laws_dir.parent)

                if bwb_id not in yaml_files_by_bwb:
                    yaml_files_by_bwb[bwb_id] = []

                yaml_files_by_bwb[bwb_id].append({
                    "path": str(rel_path),
                    "description": content.get('description', content.get('name', 'Regelspraak implementatie'))
                })
        except Exception as e:
            print(f"Error reading {yaml_file}: {e}")
            continue

    # Check which BWB IDs need content files
    created_count = 0

    for bwb_id, yaml_files in yaml_files_by_bwb.items():
        content_file = content_dir / f"{bwb_id}.yaml"

        if not content_file.exists() and bwb_id in bwb_mapping['laws']:
            law_info = bwb_mapping['laws'][bwb_id]

            # Create basic content file
            content = {
                "bwb_id": bwb_id,
                "title": law_info['title'],
                "url": f"https://wetten.overheid.nl/{bwb_id}",
                "valid_from": "2024-01-01",  # Default date
                "last_updated": datetime.now().isoformat(),
                "yaml_files": yaml_files,
                "structure": {
                    "chapters": []
                }
            }

            with open(content_file, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, allow_unicode=True, sort_keys=False,
                          default_flow_style=False, width=120)

            print(f"Created content file for {bwb_id} ({law_info['title']})")
            created_count += 1
        elif content_file.exists():
            # Update yaml_files if needed
            with open(content_file, 'r', encoding='utf-8') as f:
                existing_content = yaml.safe_load(f)

            # Check if yaml_files need updating
            existing_paths = {yf['path'] for yf in existing_content.get('yaml_files', [])}
            new_paths = {yf['path'] for yf in yaml_files}

            if new_paths - existing_paths:
                print(f"Updating yaml_files for {bwb_id}")
                existing_content['yaml_files'] = yaml_files
                existing_content['last_updated'] = datetime.now().isoformat()

                with open(content_file, 'w', encoding='utf-8') as f:
                    yaml.dump(existing_content, f, allow_unicode=True, sort_keys=False,
                              default_flow_style=False, width=120)

    print(f"\nCreated {created_count} new content files")
    print(f"Found {len(yaml_files_by_bwb)} laws with YAML implementations")


if __name__ == "__main__":
    main()
