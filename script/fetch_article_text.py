#!/usr/bin/env python3
"""Fetch article text from wetten.overheid.nl and lokaleregelgeving.overheid.nl.

Populates the empty `text` fields in v0.5.0 YAML law files with actual legal text.
"""

import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

# ---------------------------------------------------------------------------
# XML helpers for wetten.overheid.nl
# ---------------------------------------------------------------------------


def _xml_text(element: ET.Element) -> str:
    """Recursively extract text from an XML element, handling nested tags."""
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        tag = child.tag
        if tag == "lid":
            parts.append(_format_lid(child))
        elif tag == "lijst":
            parts.append(_format_lijst(child))
        elif tag == "al":
            text = _inline_text(child).strip()
            if text:
                parts.append(text)
        elif tag in ("extref", "intref"):
            parts.append(_inline_text(child))
        elif tag == "meta-data":
            continue  # skip metadata
        elif tag == "kop":
            continue  # skip article headers (we have the number already)
        else:
            parts.append(_xml_text(child))
        if child.tail:
            parts.append(child.tail)
    return "\n".join(p for p in parts if p.strip())


def _inline_text(element: ET.Element) -> str:
    """Extract inline text, preserving references as plain text."""
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        if child.tag == "meta-data":
            continue
        parts.append(_inline_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _format_lid(lid: ET.Element) -> str:
    """Format a <lid> (paragraph) element."""
    parts: list[str] = []
    lidnr = lid.find("lidnr")
    nr_text = _inline_text(lidnr).strip() if lidnr is not None else ""

    for child in lid:
        if child.tag in ("lidnr", "meta-data", "kop"):
            continue
        if child.tag == "al":
            text = _inline_text(child).strip()
            if text:
                if nr_text and not parts:
                    parts.append(f"{nr_text} {text}")
                    nr_text = ""
                else:
                    parts.append(text)
        elif child.tag == "lijst":
            parts.append(_format_lijst(child))
        elif child.tag == "lid":
            parts.append(_format_lid(child))
        elif child.tag == "tabel":
            parts.append("[tabel]")
        else:
            t = _xml_text(child).strip()
            if t:
                parts.append(t)
    return "\n".join(parts)


def _format_lijst(lijst: ET.Element) -> str:
    """Format a <lijst> (list) element."""
    items: list[str] = []
    for li in lijst:
        if li.tag == "meta-data":
            continue
        if li.tag != "li":
            continue
        li_nr_el = li.find("li.nr")
        li_nr = _inline_text(li_nr_el).strip() if li_nr_el is not None else "-"
        li_parts: list[str] = []
        for child in li:
            if child.tag in ("li.nr", "meta-data"):
                continue
            if child.tag == "al":
                li_parts.append(_inline_text(child).strip())
            elif child.tag == "lijst":
                li_parts.append(_format_lijst(child))
            else:
                t = _xml_text(child).strip()
                if t:
                    li_parts.append(t)
        text = "\n".join(li_parts)
        items.append(f"  {li_nr} {text}")
    return "\n".join(items)


def fetch_xml(bwb_id: str, date: str) -> ET.Element | None:
    """Fetch XML from wetten.overheid.nl and return root element.

    Tries multiple date fallbacks: requested date, 2025-01-01, 2024-01-01, geldend.
    """
    dates_to_try = [date]
    if date not in ("2025-01-01", "2024-01-01"):
        dates_to_try.extend(["2025-01-01", "2024-01-01"])
    elif date != "2025-01-01":
        dates_to_try.append("2025-01-01")

    for try_date in dates_to_try:
        url = f"https://wetten.overheid.nl/{bwb_id}/{try_date}/0/xml"
        try:
            req = Request(url, headers={"User-Agent": "poc-machine-law/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
                if len(data) > 100:
                    root = ET.fromstring(data)
                    if root is not None:
                        if try_date != date:
                            print(f"  (used fallback date {try_date} instead of {date})")
                        return root
        except (HTTPError, URLError, TimeoutError):
            continue
        except ET.ParseError as e:
            print(f"  WARNING: XML parse error for {url}: {e}", file=sys.stderr)
            continue

    # Try "geldend" (current version)
    url = f"https://wetten.overheid.nl/{bwb_id}/geldend/0/xml"
    try:
        req = Request(url, headers={"User-Agent": "poc-machine-law/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) > 100:
                root = ET.fromstring(data)
                if root is not None:
                    print("  (used 'geldend' fallback)")
                    return root
    except (HTTPError, URLError, ET.ParseError, TimeoutError) as e:
        print(f"  WARNING: All attempts failed for {bwb_id}: {e}", file=sys.stderr)

    return None


def extract_article_text(root: ET.Element, article_number: str) -> str | None:
    """Extract text for a specific article from the XML tree."""
    # Normalize: "2" -> match "Artikel 2", "2:28" -> "Artikel 2:28", "1a" -> "Artikel 1a"
    target_labels = [
        f"Artikel {article_number}",
        f"Artikel {article_number}.",
    ]

    # Also try matching on bwb-ng-variabel-deel attribute
    target_paths = [
        f"/Artikel{article_number}",
    ]

    for artikel in root.iter("artikel"):
        label = artikel.get("label", "")
        variabel = artikel.get("bwb-ng-variabel-deel", "")

        if label in target_labels or variabel in target_paths:
            return _xml_text(artikel)

    # Fallback: try broader search
    for artikel in root.iter("artikel"):
        label = artikel.get("label", "")
        # Try extracting just the number from the label
        m = re.match(r"Artikel\s+(.+)", label)
        if m and m.group(1).strip().rstrip(".") == article_number:
            return _xml_text(artikel)

    return None


# ---------------------------------------------------------------------------
# HTML helpers for lokaleregelgeving.overheid.nl
# ---------------------------------------------------------------------------


def _fetch_cvdr_html(cvdr_url: str) -> str | None:
    """Fetch HTML from lokaleregelgeving.overheid.nl."""
    try:
        req = Request(cvdr_url, headers={"User-Agent": "poc-machine-law/1.0"})
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  WARNING: Failed to fetch {cvdr_url}: {e}", file=sys.stderr)
        return None


def _find_article_id(html: str, article_number: str) -> str | None:
    """Find the HTML element ID for a given article number.

    Handles variations like 2:28, 2.28, 2_28.
    """
    # Normalize: try both : and . and _ as separators
    normalized = article_number.replace(":", ".").replace("_", ".")
    patterns = [
        article_number,
        article_number.replace(":", "."),
        article_number.replace(".", ":"),
    ]

    for pat in patterns:
        # Look for id="...artikel_{pat}" or id="...artikel_{pat.with" variants
        escaped = re.escape(pat)
        m = re.search(rf'id="([^"]*artikel_{escaped})"', html, re.IGNORECASE)
        if m:
            return m.group(1)
        # Try with dots replaced by other separators in the id
        for sep in [".", ":", "_"]:
            alt_pat = normalized.replace(".", sep)
            escaped_alt = re.escape(alt_pat)
            m = re.search(rf'id="([^"]*artikel_{escaped_alt})"', html, re.IGNORECASE)
            if m:
                return m.group(1)

    return None


def fetch_cvdr_article(cvdr_url: str, article_number: str, html_cache: dict[str, str | None] | None = None) -> str | None:
    """Fetch article text from lokaleregelgeving.overheid.nl HTML."""
    base_url = cvdr_url.split("#")[0]

    if html_cache is not None and base_url in html_cache:
        html = html_cache[base_url]
    else:
        html = _fetch_cvdr_html(base_url)
        if html_cache is not None:
            html_cache[base_url] = html

    if not html:
        return None

    article_id = _find_article_id(html, article_number)
    if not article_id:
        print(f"  WARNING: Could not find article {article_number} in HTML", file=sys.stderr)
        return None

    # Extract text between this article's div and the next article div
    escaped_id = re.escape(article_id)
    # Find the start of this article
    start_match = re.search(rf'id="{escaped_id}"', html)
    if not start_match:
        return None

    start_pos = start_match.start()

    # Find the next article div (any id containing "artikel_")
    next_article = re.search(r'id="[^"]*artikel_[^"]*"', html[start_pos + len(start_match.group()):])
    if next_article:
        end_pos = start_pos + len(start_match.group()) + next_article.start()
    else:
        end_pos = len(html)

    section = html[start_pos:end_pos]

    # Strip HTML tags and extract text
    text = re.sub(r'<[^>]+>', ' ', section)
    # Remove the leading id="..." attribute text
    text = re.sub(r'^[^>]*>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove leading "id=..." artifact if present
    text = re.sub(r'^id="[^"]*"\s*', '', text)
    return text if text else None


# ---------------------------------------------------------------------------
# YAML processing
# ---------------------------------------------------------------------------


def process_yaml_file(yaml_path: Path, xml_cache: dict[str, ET.Element | None], html_cache: dict[str, str | None] | None = None) -> bool:
    """Process a single YAML file, filling in empty article text fields.

    Returns True if the file was modified.
    """
    with open(yaml_path) as f:
        content = f.read()

    data = yaml.safe_load(content)
    if not data or "articles" not in data:
        return False

    top_url = data.get("url", "")
    bwb_id = data.get("bwb_id", "")
    valid_from = data.get("valid_from", "")

    # Extract BWB ID from URL if not in a separate field
    if not bwb_id:
        m = re.search(r"(BWBR\d+)", top_url)
        if m:
            bwb_id = m.group(1)

    is_cvdr = "lokaleregelgeving" in top_url
    modified = False

    for article in data["articles"]:
        if article.get("text", "").strip():
            continue  # already has text

        article_number = str(article.get("number", ""))
        if not article_number:
            continue

        text = None
        if is_cvdr:
            # Use CVDR HTML scraping
            cvdr_url = top_url.split("#")[0]  # remove fragment
            text = fetch_cvdr_article(cvdr_url, article_number, html_cache)
        elif bwb_id:
            # Use BWB XML API
            cache_key = f"{bwb_id}/{valid_from}"
            if cache_key not in xml_cache:
                print(f"  Fetching XML for {bwb_id}/{valid_from}...")
                xml_cache[cache_key] = fetch_xml(bwb_id, str(valid_from))
                time.sleep(0.5)  # be polite

            root = xml_cache[cache_key]
            if root is not None:
                text = extract_article_text(root, article_number)

        if text:
            article["text"] = text
            modified = True
            print(f"  Article {article_number}: {len(text)} chars")
        else:
            print(f"  Article {article_number}: NOT FOUND", file=sys.stderr)

    if modified:
        # Write back preserving YAML style
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    return modified


def main() -> None:
    laws_dir = Path("laws")
    if not laws_dir.exists():
        print("Error: laws/ directory not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    yaml_files = sorted(laws_dir.rglob("*.yaml"))
    print(f"Found {len(yaml_files)} YAML files")

    xml_cache: dict[str, ET.Element | None] = {}
    html_cache: dict[str, str | None] = {}
    modified_count = 0
    failed_articles: list[str] = []

    for i, yaml_path in enumerate(yaml_files, 1):
        print(f"\n[{i}/{len(yaml_files)}] {yaml_path}")

        data = yaml.safe_load(yaml_path.read_text())
        if not data or "articles" not in data:
            print("  Skipping (no articles)")
            continue

        # Check if any articles need text
        needs_text = any(not a.get("text", "").strip() for a in data["articles"])
        if not needs_text:
            print("  Already has text, skipping")
            continue

        if process_yaml_file(yaml_path, xml_cache, html_cache):
            modified_count += 1
        else:
            # Check which articles failed
            for a in data["articles"]:
                if not a.get("text", "").strip():
                    failed_articles.append(f"{yaml_path}: Article {a.get('number', '?')}")

    print(f"\n{'='*60}")
    print(f"Modified: {modified_count} files")
    if failed_articles:
        print(f"Failed to fetch {len(failed_articles)} articles:")
        for f in failed_articles:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
