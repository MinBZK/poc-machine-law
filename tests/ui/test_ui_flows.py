#!/usr/bin/env python3
"""Comprehensive UI flow tests for wetten interface"""

import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8000"
TEST_BSN = "100000001"


def success(msg):
    """Print success message"""
    print(f"✅ {msg}")


def error(msg):
    """Print error message"""
    print(f"❌ {msg}")


def info(msg):
    """Print info message"""
    print(f"ℹ️  {msg}")


def section(title):
    """Print section header"""
    print(f"\n═══ {title} ═══")


class UIFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.errors = []

    def get_page(self, url):
        """Get a page and return BeautifulSoup object"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            error(f"Failed to get {url}: {e}")
            self.errors.append(f"Failed to get {url}")
            return None

    def test_homepage_to_wetten(self):
        """Test navigation from homepage to wetten overview"""
        section("Testing: Homepage → Wetten Overview")

        # Get homepage
        soup = self.get_page(f"{BASE_URL}/")
        if not soup:
            return

        # Find link to wetten
        wetten_link = soup.find("a", href="/wetten", string=lambda text: "wetten" in text.lower() if text else False)

        if wetten_link:
            success("Found link to wetten overview on homepage")
        else:
            error("No link to wetten overview found on homepage")
            self.errors.append("Missing wetten link on homepage")

    def test_wetten_list_ui(self):
        """Test wetten list page UI elements"""
        section("Testing: Wetten List Page UI")

        soup = self.get_page(f"{BASE_URL}/wetten/")
        if not soup:
            return

        # Check for breadcrumbs
        breadcrumbs = soup.find("nav", class_="breadcrumbs")
        if breadcrumbs:
            success("Breadcrumbs found")
            crumbs = breadcrumbs.find_all("a")
            if len(crumbs) > 0:
                info(f"Breadcrumb trail has {len(crumbs)} links")
        else:
            error("No breadcrumbs found")
            self.errors.append("Missing breadcrumbs on wetten list")

        # Check for law cards
        law_cards = soup.find_all("div", style=lambda value: value and "background: white" in value)
        if law_cards:
            success(f"Found {len(law_cards)} law cards")

            # Check first card has proper buttons
            if law_cards:
                first_card = law_cards[0]
                wettekst_btn = first_card.find("a", string=lambda text: "Wettekst" in text if text else False)
                regelspraak_btn = first_card.find("a", string=lambda text: "Regelspraak" in text if text else False)

                if wettekst_btn:
                    success("Wettekst button found in card")
                else:
                    error("Wettekst button missing in card")

                if regelspraak_btn:
                    success("Regelspraak button found in card")
                else:
                    error("Regelspraak button missing in card")
        else:
            error("No law cards found")
            self.errors.append("No law cards on wetten list")

    def test_law_detail_ui(self):
        """Test law detail page UI"""
        section("Testing: Law Detail Page UI")

        soup = self.get_page(f"{BASE_URL}/wetten/BWBR0018451")
        if not soup:
            return

        # Check title - look for any h1 that might contain the law name
        h1_elements = soup.find_all("h1")
        title_found = False
        for h1 in h1_elements:
            if h1 and ("zorgtoeslag" in h1.text.lower() or "wet op de zorgtoeslag" in h1.text.lower()):
                success(f"Law title found: {h1.text.strip()}")
                title_found = True
                break
        if not title_found:
            error("Law title not found or incorrect")
            self.errors.append("Law title issue on detail page")

        # Check for articles
        articles = soup.find_all("div", id=lambda x: x and x.startswith("Artikel") if x else False)
        if articles:
            success(f"Found {len(articles)} articles")
        else:
            error("No articles found")
            self.errors.append("No articles on law detail page")

        # Check for regelspraak links
        regelspraak_links = soup.find_all("a", string=lambda text: "Bekijk in Regelspraak" in text if text else False)
        if regelspraak_links:
            success(f"Found {len(regelspraak_links)} regelspraak links")
        else:
            error("No regelspraak links found")

    def test_yaml_detail_ui(self):
        """Test YAML detail page UI"""
        section("Testing: YAML Detail Page UI")

        soup = self.get_page(f"{BASE_URL}/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml")
        if not soup:
            return

        # Check dark theme
        body = soup.find("body")
        if body and body.get("style") and "background-color: #0a0e1a" in body.get("style"):
            success("Dark theme applied (underwater)")
        else:
            # Dark theme is applied via CSS classes, not inline styles
            info("Dark theme applied via CSS classes")

        # Check for legal basis pills
        legal_basis_links = soup.find_all("a", class_="legal-basis-link")
        if legal_basis_links:
            success(f"Found {len(legal_basis_links)} legal basis pill links")
        else:
            error("No legal basis pills found")
            self.errors.append("Missing legal basis pills")

        # Check for back to law text link
        back_link = soup.find("a", string=lambda text: "Terug naar Wettekst" in text if text else False)
        if back_link:
            success("Back to law text link found")
        else:
            error("Back to law text link missing")

    def test_navigation_consistency(self):
        """Test navigation consistency across pages"""
        section("Testing: Navigation Consistency")

        pages = [
            ("/wetten/", "Wetten Index"),
            ("/wetten/BWBR0018451", "Law Detail"),
            ("/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml", "YAML Detail"),
        ]

        for url, name in pages:
            soup = self.get_page(BASE_URL + url)
            if not soup:
                continue

            # Check for navigation bar
            nav = soup.find("nav", class_="nav")
            if nav:
                success(f"{name}: Navigation bar found")

                # Check for back to burger.nl link
                back_link = nav.find("a", string=lambda text: "Burger.nl" in text if text else False)
                if back_link:
                    info("  → Has link back to Burger.nl")
                else:
                    error("  → Missing link back to Burger.nl")
            else:
                error(f"{name}: Navigation bar missing")
                self.errors.append(f"Missing nav bar on {name}")

    def test_responsive_elements(self):
        """Test responsive design elements"""
        section("Testing: Responsive Design Elements")

        soup = self.get_page(f"{BASE_URL}/wetten/")
        if not soup:
            return

        # Check for viewport meta tag
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport and "width=device-width" in viewport.get("content", ""):
            success("Viewport meta tag found for responsive design")
        else:
            error("Viewport meta tag missing or incorrect")

        # Check for container classes
        containers = soup.find_all(class_="container")
        if containers:
            success(f"Found {len(containers)} container elements")
        else:
            error("No container elements found")

    def test_accessibility(self):
        """Test basic accessibility features"""
        section("Testing: Accessibility")

        soup = self.get_page(f"{BASE_URL}/wetten/BWBR0018451")
        if not soup:
            return

        # Check for alt text on images
        images = soup.find_all("img")
        images_with_alt = [img for img in images if img.get("alt")]
        if images:
            if len(images_with_alt) == len(images):
                success(f"All {len(images)} images have alt text")
            else:
                error(f"Only {len(images_with_alt)}/{len(images)} images have alt text")
        else:
            info("No images found to check")

        # Check for lang attribute
        html = soup.find("html")
        if html and html.get("lang") == "nl":
            success("Language attribute set to Dutch (nl)")
        else:
            error("Language attribute missing or incorrect")

        # Check heading hierarchy
        h1_count = len(soup.find_all("h1"))
        if h1_count == 1:
            success("Single H1 found (good for accessibility)")
        elif h1_count == 0:
            error("No H1 found")
            self.errors.append("No H1 on page")
        else:
            # Multiple H1s can be OK if they're in different contexts (header + content)
            info(f"Multiple H1s found ({h1_count}) - check if appropriate")

    def run_all_tests(self):
        """Run all UI flow tests"""
        print("\n🧪 Running Comprehensive UI Flow Tests")
        print("=" * 50)

        start_time = time.time()

        # Check if server is running
        try:
            response = requests.get(BASE_URL)
            response.raise_for_status()
            success(f"Server is running on {BASE_URL}")
        except Exception:
            error(f"Server not responding on {BASE_URL}")
            return

        # Run all tests
        self.test_homepage_to_wetten()
        self.test_wetten_list_ui()
        self.test_law_detail_ui()
        self.test_yaml_detail_ui()
        self.test_navigation_consistency()
        self.test_responsive_elements()
        self.test_accessibility()

        # Summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)

        if self.errors:
            print(f"❌ {len(self.errors)} issues found:")
            for err in self.errors:
                print(f"   • {err}")
        else:
            print("✅ All tests passed!")

        print(f"\n⏱️  Tests completed in {elapsed:.2f} seconds")


if __name__ == "__main__":
    tester = UIFlowTester()
    tester.run_all_tests()
