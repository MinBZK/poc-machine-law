#!/usr/bin/env python3
"""Merge fetched law structures with existing content files."""

import yaml
from pathlib import Path
import shutil


def merge_law_files():
    """Merge fetched law structures with existing content files."""
    content_dir = Path(__file__).parent.parent / "laws" / "content"
    fetched_dir = Path(__file__).parent.parent / "laws" / "fetched"

    # Get all fetched files
    fetched_files = list(fetched_dir.glob("*.yaml"))

    for fetched_file in fetched_files:
        bwb_id = fetched_file.stem
        content_file = content_dir / f"{bwb_id}.yaml"

        if not content_file.exists():
            print(f"⚠️  No content file for {bwb_id}, skipping")
            continue

        print(f"Processing {bwb_id}...")

        # Load both files
        with open(content_file, 'r', encoding='utf-8') as f:
            content_data = yaml.safe_load(f)

        with open(fetched_file, 'r', encoding='utf-8') as f:
            fetched_data = yaml.safe_load(f)

        # Create backup
        backup_file = content_file.with_suffix('.yaml.bak')
        shutil.copy2(content_file, backup_file)

        # Replace structure with fetched structure
        content_data['structure'] = fetched_data['structure']

        # Clean up the fetched structure to remove duplicate articles with UI elements
        cleaned_structure = clean_structure(content_data['structure'])
        content_data['structure'] = cleaned_structure

        # Update metadata
        content_data['last_updated'] = fetched_data.get('fetched_at', '2025-01-14')

        # Write back
        with open(content_file, 'w', encoding='utf-8') as f:
            yaml.dump(content_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"✅ Updated {bwb_id}")


def clean_structure(structure):
    """Remove duplicate articles that contain UI elements."""
    if 'chapters' in structure:
        for chapter in structure['chapters']:
            if 'articles' in chapter:
                # Filter out articles that have UI elements in content
                cleaned_articles = []
                seen_ids = set()

                for article in chapter['articles']:
                    # Check if this is a duplicate with UI elements
                    is_ui_element = False
                    if 'paragraphs' in article:
                        for para in article['paragraphs']:
                            content = para.get('content', '')
                            if 'Toon relaties in LiDO' in content or 'Maak een permanente link' in content:
                                is_ui_element = True
                                break

                    # Only add if not a UI element and not already seen
                    article_id = article.get('id', '')
                    if not is_ui_element and article_id not in seen_ids:
                        cleaned_articles.append(article)
                        seen_ids.add(article_id)

                chapter['articles'] = cleaned_articles

            # Recursively clean sections
            if 'sections' in chapter:
                for section in chapter['sections']:
                    clean_section(section)

    return structure


def clean_section(section):
    """Clean a section recursively."""
    if 'articles' in section:
        # Filter out articles that have UI elements in content
        cleaned_articles = []
        seen_ids = set()

        for article in section['articles']:
            # Check if this is a duplicate with UI elements
            is_ui_element = False
            if 'paragraphs' in article:
                for para in article['paragraphs']:
                    content = para.get('content', '')
                    if 'Toon relaties in LiDO' in content or 'Maak een permanente link' in content:
                        is_ui_element = True
                        break

            # Only add if not a UI element and not already seen
            article_id = article.get('id', '')
            if not is_ui_element and article_id not in seen_ids:
                cleaned_articles.append(article)
                seen_ids.add(article_id)

        section['articles'] = cleaned_articles


if __name__ == "__main__":
    merge_law_files()
