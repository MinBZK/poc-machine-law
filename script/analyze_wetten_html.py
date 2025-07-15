#!/usr/bin/env python3
"""
Analyze the HTML structure of wetten.overheid.nl to understand how to properly parse it.
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

def fetch_and_analyze(bwb_id: str):
    """Fetch a law and analyze its HTML structure."""
    url = f"https://wetten.overheid.nl/{bwb_id}"

    print(f"Fetching {url}...")
    response = requests.get(url)
    response.raise_for_status()

    # Save raw HTML for inspection
    html_path = Path(f"/Users/anneschuth/poc-machine-law/laws/fetched/{bwb_id}_raw.html")
    html_path.parent.mkdir(exist_ok=True)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"Saved raw HTML to {html_path}")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Analyze structure
    analysis = {
        'title': None,
        'main_content_selectors': [],
        'article_selectors': [],
        'chapter_selectors': [],
        'paragraph_selectors': []
    }

    # Find title
    for selector in ['h1.titel', 'h1.regeling-titel', 'h1', 'meta[property="dcterms:title"]']:
        elem = soup.select_one(selector)
        if elem:
            if elem.name == 'meta':
                analysis['title'] = elem.get('content', '').strip()
            else:
                analysis['title'] = elem.get_text(strip=True)
            break

    # Find main content area
    for selector in ['div.wettekst', 'div#wettekst', 'main', 'div[role="main"]', 'div.wet-container']:
        elem = soup.select_one(selector)
        if elem:
            analysis['main_content_selectors'].append({
                'selector': selector,
                'found': True,
                'num_children': len(elem.find_all(recursive=False))
            })

    # Find how articles are structured
    # Look for different patterns
    article_patterns = [
        'div.artikel',
        'section.artikel',
        'artikel',
        'div[class*="artikel"]',
        'div[id*="artikel"]',
        '*[data-artikel]'
    ]

    for pattern in article_patterns:
        elements = soup.select(pattern)
        if elements:
            analysis['article_selectors'].append({
                'selector': pattern,
                'count': len(elements),
                'sample': elements[0].get_text()[:200] if elements else ''
            })

    # Look for artikel text patterns
    import re
    artikel_regex = re.compile(r'Artikel\s+\d+[a-z]?', re.I)
    artikel_elements = soup.find_all(string=artikel_regex)
    print(f"\nFound {len(artikel_elements)} elements containing 'Artikel X' text")

    # Sample the first few
    for i, elem in enumerate(artikel_elements[:5]):
        parent = elem.parent
        print(f"\nArtikel text {i+1}:")
        print(f"  Text: {elem.strip()[:100]}")
        print(f"  Parent tag: {parent.name}")
        print(f"  Parent classes: {parent.get('class', [])}")
        print(f"  Parent id: {parent.get('id', 'None')}")

    # Save analysis
    analysis_path = Path(f"/Users/anneschuth/poc-machine-law/laws/fetched/{bwb_id}_analysis.json")
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nSaved analysis to {analysis_path}")

if __name__ == "__main__":
    # Analyze AOW
    fetch_and_analyze("BWBR0002221")
