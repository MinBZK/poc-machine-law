#!/usr/bin/env python3
"""
Fetch real law texts from wetten.overheid.nl and generate properly structured YAML files.

This script:
1. Reads BWB IDs from existing law content files
2. Fetches the actual law text from wetten.overheid.nl
3. Parses the HTML to extract the exact article structure
4. Creates YAML files with proper paragraph structure
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import yaml
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LawFetcher:
    """Fetch and parse laws from wetten.overheid.nl"""

    BASE_URL = "https://wetten.overheid.nl"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (compatible; Machinelaw/1.0; +https://github.com/anneschuth/poc-machine-law)'
    }

    def __init__(self, delay: float = 1.0):
        """Initialize with request delay to be respectful to the server."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_law(self, bwb_id: str) -> Optional[str]:
        """Fetch the HTML content of a law from wetten.overheid.nl."""
        url = f"{self.BASE_URL}/{bwb_id}"
        logger.info(f"Fetching law from: {url}")

        try:
            response = self.session.get(url)
            response.raise_for_status()
            time.sleep(self.delay)  # Be respectful to the server
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {bwb_id}: {e}")
            return None

    def parse_law_html(self, html: str, bwb_id: str) -> Dict[str, Any]:
        """Parse the HTML to extract law structure."""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        title = self._extract_title(soup)

        # Find the main content area
        content = soup.find('div', {'class': 'wetcontent'})
        if not content:
            content = soup.find('div', {'class': 'content'}) or soup

        # Extract structure
        structure = {
            'title': title,
            'chapters': self._extract_chapters(content)
        }

        return structure

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the law title from the HTML."""
        # Try to find the title in meta tags first
        meta_title = soup.find('meta', {'property': 'dcterms:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()

        # Try various common title locations
        title_elem = (
            soup.find('h1', {'class': 'titel'}) or
            soup.find('h1', {'class': 'regeling-titel'}) or
            soup.find('h1') or
            soup.find('title')
        )

        if title_elem:
            title = title_elem.get_text(strip=True)
            # Clean up the title
            title = re.sub(r'\s+', ' ', title)
            # Remove common suffixes
            title = re.sub(r'\s*\|\s*wetten\.nl.*$', '', title, flags=re.I)
            return title

        return "Unknown Title"

    def _extract_chapters(self, content: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract chapters from the content."""
        chapters = []
        seen_articles: Set[str] = set()  # Track processed articles

        # Find all hoofdstuk (chapter) divs
        chapter_divs = content.find_all('div', {'class': 'hoofdstuk'})

        if chapter_divs:
            for chapter_div in chapter_divs:
                chapter = self._parse_chapter_div(chapter_div, seen_articles)
                if chapter:
                    chapters.append(chapter)
        else:
            # No explicit chapters, look for articles directly
            articles = self._extract_articles_from_container(content, seen_articles)
            if articles:
                chapters.append({
                    'id': 'HoofdstukI',
                    'title': 'Algemene bepalingen',
                    'articles': articles
                })

        return chapters

    def _parse_chapter_div(self, chapter_div: Tag, seen_articles: Set[str]) -> Optional[Dict[str, Any]]:
        """Parse a chapter div element."""
        # Extract chapter ID from the div's id attribute
        chapter_id = chapter_div.get('id', '')

        # Find the chapter title
        title_elem = chapter_div.find(['h3', 'h2'], {'class': 'hoofdstuktitel'})
        if not title_elem:
            # Look for title in the text
            chapter_text = chapter_div.get_text()
            match = re.search(r'Hoofdstuk\s+([IVX]+[A-Z]*)\s*[.-]?\s*(.+?)(?:\n|$)', chapter_text, re.I)
            if match:
                chapter_num = match.group(1)
                title = match.group(2).strip()
                if not chapter_id:
                    chapter_id = f'Hoofdstuk{chapter_num}'
            else:
                title = 'Algemene bepalingen'
        else:
            title_text = title_elem.get_text(strip=True)
            # Parse out the chapter number and title
            match = re.match(r'(Hoofdstuk\s+[IVX]+[A-Z]*)\s*[.-]?\s*(.+)', title_text)
            if match:
                chapter_num = match.group(1).replace(' ', '')
                title = match.group(2).strip()
            else:
                title = title_text

        # Extract articles within this chapter
        articles = self._extract_articles_from_container(chapter_div, seen_articles)

        if not articles:
            return None

        return {
            'id': chapter_id or 'HoofdstukI',
            'title': title,
            'articles': articles
        }

    def _extract_articles_from_container(self, container: Tag, seen_articles: Set[str]) -> List[Dict[str, Any]]:
        """Extract articles from a container element."""
        articles = []

        # Find all artikel divs
        artikel_divs = container.find_all('div', {'class': 'artikel'})

        for artikel_div in artikel_divs:
            article_id = artikel_div.get('id', '')

            # Skip if we've already processed this article
            if article_id and article_id in seen_articles:
                continue

            article = self._parse_article_div(artikel_div)
            if article:
                # Check for duplicate by content
                is_duplicate = False
                for existing in articles:
                    if existing['id'] == article['id']:
                        # Check if this is a real duplicate or has different content
                        if self._is_placeholder_content(article):
                            is_duplicate = True
                            break

                if not is_duplicate:
                    articles.append(article)
                    if article_id:
                        seen_articles.add(article_id)

        return articles

    def _is_placeholder_content(self, article: Dict[str, Any]) -> bool:
        """Check if article has placeholder content like '...'"""
        if not article.get('paragraphs'):
            return True

        for para in article['paragraphs']:
            content = para.get('content', '').strip()
            if content and content != '...' and len(content) > 10:
                return False

        return True

    def _parse_article_div(self, artikel_div: Tag) -> Optional[Dict[str, Any]]:
        """Parse an article div element."""
        # Find the article header
        header = artikel_div.find('h4')
        if not header:
            return None

        # Extract article number and optional title
        header_text = header.get_text(strip=True)
        match = re.match(r'Artikel\s+(\d+[a-z]?)(?:\s+(.+))?', header_text)
        if not match:
            return None

        article_number = match.group(1)
        article_id = f'Artikel{article_number}'
        title = match.group(2).strip() if match.group(2) else ''

        # Extract paragraphs
        paragraphs = self._extract_paragraphs_from_article(artikel_div)

        if not paragraphs:
            return None

        article_dict = {
            'id': article_id,
            'paragraphs': paragraphs
        }

        if title:
            article_dict['title'] = title

        return article_dict

    def _extract_paragraphs_from_article(self, artikel_div: Tag) -> List[Dict[str, Any]]:
        """Extract paragraphs from an article div."""
        paragraphs = []

        # Find the list of lids (paragraphs)
        lid_lists = artikel_div.find_all('ul', {'class': 'artikel_leden'})

        if lid_lists:
            for lid_list in lid_lists:
                # Extract paragraphs from the list
                for li in lid_list.find_all('li', recursive=False):
                    paragraph = self._parse_lid_element(li)
                    if paragraph:
                        paragraphs.append(paragraph)
        else:
            # If no explicit lid structure, look for numbered paragraphs
            content = artikel_div.get_text()
            # Remove the article header
            content = re.sub(r'^.*?Artikel\s+\d+[a-z]?.*?\n', '', content, flags=re.I | re.DOTALL)
            paragraphs = self._parse_paragraphs_from_text(content)

        return paragraphs

    def _parse_lid_element(self, lid_elem: Tag) -> Optional[Dict[str, Any]]:
        """Parse a lid (paragraph) element."""
        # Find the paragraph content
        lid_p = lid_elem.find('p', {'class': 'lid'})
        if not lid_p:
            # Sometimes the li itself contains the paragraph
            lid_p = lid_elem

        # Extract the paragraph number
        lidnr_span = lid_p.find('span', {'class': 'lidnr'})
        if lidnr_span:
            number_text = lidnr_span.get_text(strip=True)
            # Remove the span from the paragraph to get clean content
            lidnr_span.extract()
            try:
                number = int(number_text.strip())
            except ValueError:
                number = 1
        else:
            # Try to extract number from the beginning of the text
            text = lid_p.get_text()
            match = re.match(r'^\s*(\d+)\s*\.?\s*', text)
            if match:
                number = int(match.group(1))
            else:
                number = 1

        # Extract the content
        content = self._extract_clean_text(lid_p)

        # Check for sub-items (a, b, c, etc.)
        sub_list = lid_elem.find('ul', {'class': ['list--law__unordered', 'expliciet']})
        if sub_list:
            # Extract sub-items and add them to content
            sub_items = []
            for sub_li in sub_list.find_all('li', {'class': 'li'}):
                sub_text = self._extract_clean_text(sub_li)
                if sub_text:
                    sub_items.append(sub_text)

            if sub_items:
                content = content.rstrip() + '\n\n' + '\n\n'.join(sub_items)

        if not content or content.strip() == '...':
            return None

        return {
            'number': number,
            'content': content
        }

    def _extract_clean_text(self, elem: Tag) -> str:
        """Extract clean text from an element, preserving structure."""
        # Clone the element to avoid modifying the original
        elem_copy = elem.__copy__()

        # Remove navigation and UI elements
        for unwanted in elem_copy.find_all(['a'], {'class': ['popuplidorelaties', 'popuppermanentelink']}):
            unwanted.decompose()

        # Process links to avoid duplication
        for link in elem_copy.find_all('a'):
            link_text = link.get_text(strip=True)
            if link_text:
                link.replace_with(link_text)

        # Get text content
        text = elem_copy.get_text()

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Remove UI patterns
        ui_patterns = [
            r'Toon relaties in LiDO',
            r'Maak een permanente link',
            r'Toon wetstechnische informatie',
            r'Druk het regelingonderdeel af',
            r'Sla het regelingonderdeel op',
            r'\[Wijziging.*?\]',
            r'Zie het overzicht van wijzigingen',
            r'\.\.\.'  # Remove ellipsis placeholders
        ]

        for pattern in ui_patterns:
            text = re.sub(pattern, '', text, flags=re.I)

        # Clean up again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _parse_paragraphs_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Parse paragraphs from plain text content."""
        paragraphs = []

        # Pattern to match numbered paragraphs
        paragraph_pattern = re.compile(r'(?:^|\n)\s*(\d+)\s*\.?\s+(.+?)(?=(?:\n\s*\d+\s*\.?\s+)|$)', re.DOTALL)

        matches = paragraph_pattern.findall(content)

        if matches:
            for number, text in matches:
                cleaned = self._clean_paragraph_text(text)
                if cleaned and cleaned != '...':
                    paragraphs.append({
                        'number': int(number),
                        'content': cleaned
                    })
        else:
            # No numbered paragraphs found, treat as single paragraph
            cleaned = self._clean_paragraph_text(content)
            if cleaned and cleaned != '...':
                paragraphs.append({
                    'number': 1,
                    'content': cleaned
                })

        return paragraphs

    def _clean_paragraph_text(self, text: str) -> str:
        """Clean and normalize paragraph text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()

        # Format sub-items properly
        # Handle patterns like "a.", "b.", etc. that should be on new lines
        text = re.sub(r'\s+([a-z])\.\s+', r'\n\n\1. ', text)

        # Handle numbered sub-items like "1°", "2°"
        text = re.sub(r'\s+(\d+)°\s+', r'\n\n\1° ', text)

        # Clean up any excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


def load_existing_laws(content_dir: Path) -> List[Dict[str, Any]]:
    """Load existing law YAML files to get BWB IDs."""
    laws = []

    for yaml_file in content_dir.glob("*.yaml"):
        if yaml_file.name == "template.yaml":
            continue

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'bwb_id' in data:
                    laws.append({
                        'bwb_id': data['bwb_id'],
                        'title': data.get('title', ''),
                        'file_path': yaml_file
                    })
        except Exception as e:
            logger.error(f"Failed to load {yaml_file}: {e}")

    return laws


def save_law_yaml(law_data: Dict[str, Any], output_path: Path):
    """Save law data to YAML file."""
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Custom YAML representer for better formatting
    def str_presenter(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    yaml.add_representer(str, str_presenter)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(law_data, f, default_flow_style=False, allow_unicode=True, width=120, sort_keys=False)

    logger.info(f"Saved law to {output_path}")


def main():
    """Main function to fetch and process laws."""
    # Set up paths
    base_dir = Path("/Users/anneschuth/poc-machine-law")
    content_dir = base_dir / "laws" / "content"
    output_dir = base_dir / "laws" / "fetched"

    # Load existing laws
    existing_laws = load_existing_laws(content_dir)
    logger.info(f"Found {len(existing_laws)} existing law files")

    # Initialize fetcher
    fetcher = LawFetcher(delay=1.0)

    # Process each law
    for law_info in existing_laws:
        bwb_id = law_info['bwb_id']
        logger.info(f"\nProcessing {bwb_id}: {law_info['title']}")

        # Fetch the law
        html = fetcher.fetch_law(bwb_id)
        if not html:
            logger.error(f"Failed to fetch {bwb_id}")
            continue

        # Parse the law
        try:
            law_structure = fetcher.parse_law_html(html, bwb_id)

            # Create the full law data
            law_data = {
                'bwb_id': bwb_id,
                'title': law_structure['title'],
                'url': f"{fetcher.BASE_URL}/{bwb_id}",
                'fetched_at': datetime.now().isoformat(),
                'structure': {
                    'chapters': law_structure['chapters']
                }
            }

            # Save to YAML
            output_path = output_dir / f"{bwb_id}.yaml"
            save_law_yaml(law_data, output_path)

        except Exception as e:
            logger.error(f"Failed to parse {bwb_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    logger.info("\nFetching complete!")


if __name__ == "__main__":
    main()
