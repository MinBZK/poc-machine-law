#!/usr/bin/env python3
"""Test navigation links in the wetten interface"""

import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8000"
VISITED = set()
ERRORS = []


def test_link(url, parent_url=None):
    """Test a single link"""
    if url in VISITED:
        return True

    VISITED.add(url)

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            ERRORS.append(f"❌ {url} returned {response.status_code} (from {parent_url})")
            return False
        else:
            print(f"✅ {url}")
            return True
    except Exception as e:
        ERRORS.append(f"❌ {url} failed: {str(e)} (from {parent_url})")
        return False


def extract_links(url, html):
    """Extract all links from HTML"""
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for tag in soup.find_all(["a"]):
        href = tag.get("href")
        if href:
            # Skip external links and anchors
            if href.startswith("http") and not href.startswith(BASE_URL):
                continue
            if href.startswith("#"):
                # Test anchor exists
                anchor_id = href[1:]
                if anchor_id and not soup.find(id=anchor_id):
                    ERRORS.append(f"⚠️  Anchor #{anchor_id} not found in {url}")
                continue

            # Convert relative to absolute URL
            full_url = urljoin(url, href)
            if full_url.startswith(BASE_URL):
                links.append(full_url)

    return links


def crawl_and_test(start_url, max_depth=3, current_depth=0):
    """Crawl and test all links recursively"""
    if current_depth >= max_depth:
        return

    if start_url in VISITED:
        return

    print(f"\n{'  ' * current_depth}Testing: {start_url}")

    try:
        response = requests.get(start_url, timeout=5)
        if response.status_code != 200:
            ERRORS.append(f"❌ {start_url} returned {response.status_code}")
            return

        VISITED.add(start_url)

        # Extract and test all links
        links = extract_links(start_url, response.text)
        for link in links:
            if link not in VISITED:
                test_link(link, start_url)
                # Only crawl wetten pages deeper
                if "/wetten" in link and current_depth < max_depth - 1:
                    crawl_and_test(link, max_depth, current_depth + 1)

    except Exception as e:
        ERRORS.append(f"❌ Failed to crawl {start_url}: {str(e)}")


def test_specific_flows():
    """Test specific navigation flows"""
    print("\n🧪 Testing specific navigation flows...")

    # Flow 1: Home -> Wetten -> Law -> YAML -> Back
    print("\n📍 Flow: Burger.nl → Wetten → Zorgtoeslag → YAML → Terug")

    # Test home page
    if test_link(f"{BASE_URL}/") and test_link(f"{BASE_URL}/wetten/") and test_link(f"{BASE_URL}/wetten/BWBR0018451"):
        # Test YAML implementation
        yaml_url = f"{BASE_URL}/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml"
        if test_link(yaml_url):
            print("✅ Complete flow works!")

    # Flow 2: Test article anchors
    print("\n📍 Testing article anchor links...")
    law_url = f"{BASE_URL}/wetten/BWBR0018451"
    response = requests.get(law_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # Check if Artikel2 anchor exists
        artikel2 = soup.find(id="Artikel2")
        if artikel2:
            print("✅ Artikel2 anchor found")
        else:
            ERRORS.append("❌ Artikel2 anchor not found in law page")

    # Flow 3: Test legal basis pills in YAML
    print("\n📍 Testing legal basis pill links in YAML...")
    yaml_url = f"{BASE_URL}/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml"
    response = requests.get(yaml_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        legal_basis_links = soup.find_all("a", class_="legal-basis-link")
        print(f"Found {len(legal_basis_links)} legal basis pill links")
        for link in legal_basis_links[:3]:  # Test first 3
            href = link.get("href")
            if href:
                full_url = urljoin(yaml_url, href)
                test_link(full_url, yaml_url)


def main():
    """Main test function"""
    print("🚀 Starting navigation tests...\n")

    # Test if server is running
    try:
        requests.get(BASE_URL, timeout=2)
        print(f"✅ Server is running on {BASE_URL}")
    except:
        print(f"❌ Server not running on {BASE_URL}")
        sys.exit(1)

    # Test specific flows
    test_specific_flows()

    # Crawl and test all links starting from wetten
    print("\n🕷️  Crawling all wetten pages...")
    crawl_and_test(f"{BASE_URL}/wetten/", max_depth=2)

    # Report results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"✅ Links tested: {len(VISITED)}")
    print(f"❌ Errors found: {len(ERRORS)}")

    if ERRORS:
        print("\n🚨 ERRORS:")
        for error in ERRORS:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n🎉 All navigation tests passed!")


if __name__ == "__main__":
    main()
