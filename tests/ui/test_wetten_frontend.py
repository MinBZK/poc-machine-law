#!/usr/bin/env python3
"""
Frontend tests for the wetten.overheid.nl clone interface.
Tests navigation, links, and page rendering.
"""

import asyncio
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup


class TestWettenFrontend:
    """Test suite for wetten.overheid.nl clone interface"""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=10.0)

    def test_wetten_homepage(self):
        """Test the main wetten homepage loads correctly"""
        print("\n🧪 Testing /wetten homepage...")
        response = self.client.get("/wetten/")  # Add trailing slash
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Check title
        title = soup.find("title")
        assert title is not None, "Page title not found"
        assert "wetten" in title.text.lower(), "Page title should contain 'wetten'"

        # Check header has logo
        logo = soup.find("img", {"alt": "Overheid.nl"})
        assert logo is not None, "Overheid.nl logo not found"

        # Check navigation tabs
        nav_tabs = soup.find_all("a", class_="nav-tab")
        assert len(nav_tabs) >= 4, "Should have at least 4 navigation tabs"

        # Check search form exists
        search_form = soup.find("form", class_="search-form")
        assert search_form is not None, "Search form not found"

        # Check laws are listed
        laws_section = soup.find("section", class_="laws-section")
        assert laws_section is not None, "Laws section not found"

        law_items = soup.find_all("div", class_="law-item")
        print(f"✅ Found {len(law_items)} laws listed")
        assert len(law_items) > 0, "No laws found on page"

        # Check implementation links
        impl_links = soup.find_all("a", class_="implementation-link")
        print(f"✅ Found {len(impl_links)} implementation links")

        return True

    def test_law_detail_page(self):
        """Test law detail page loads correctly"""
        print("\n🧪 Testing law detail page...")
        # Test with Awb
        response = self.client.get("/wetten/BWBR0005537")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Check law title
        law_title = soup.find("h1", class_="law-title")
        assert law_title is not None, "Law title not found"
        assert "Algemene wet bestuursrecht" in law_title.text, "Wrong law title"

        # Check sidebar with table of contents
        sidebar = soup.find("aside", class_="sidebar")
        assert sidebar is not None, "Sidebar not found"

        toc_links = sidebar.find_all("a", class_="toc-link")
        print(f"✅ Found {len(toc_links)} table of contents links")
        assert len(toc_links) > 0, "No table of contents links found"

        # Check articles exist
        articles = soup.find_all("article", class_="article")
        print(f"✅ Found {len(articles)} articles")
        assert len(articles) > 0, "No articles found"

        # Check machine implementations button
        impl_btn = soup.find("div", class_="implementations-btn")
        assert impl_btn is not None, "Machine implementations button not found"

        return True

    def test_yaml_detail_page(self):
        """Test YAML detail page loads correctly"""
        print("\n🧪 Testing YAML detail page...")
        # Test with a known YAML path
        yaml_path = quote("law/awb/bezwaar/JenV-2024-01-01.yaml")
        response = self.client.get(f"/wetten/BWBR0005537/yaml/{yaml_path}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Check back navigation
        back_link = soup.find("a", string=lambda text: text and "Terug naar" in text)
        assert back_link is not None, "Back to law link not found"

        # Check YAML content sections
        yaml_sections = soup.find_all("div", class_="yaml-section")
        print(f"✅ Found {len(yaml_sections)} YAML sections")
        assert len(yaml_sections) > 0, "No YAML sections found"

        # Check legal basis references
        legal_basis = soup.find("div", class_="legal-basis-main")
        assert legal_basis is not None, "Legal basis section not found"

        return True

    def test_navigation_links(self):
        """Test all navigation links work"""
        print("\n🧪 Testing navigation links...")

        # Test burger.nl dropdown has wetten link
        response = self.client.get("/")
        soup = BeautifulSoup(response.text, "html.parser")
        wetten_link = soup.find("a", {"href": "/wetten"})
        assert wetten_link is not None, "Wetten link not found in burger.nl"

        # Test wetten page links
        response = self.client.get("/wetten/")  # Add trailing slash
        soup = BeautifulSoup(response.text, "html.parser")

        # Test law links
        law_links = soup.find_all("a", href=lambda x: x and x.startswith("/wetten/BWBR"))
        print(f"✅ Found {len(law_links)} law links")
        assert len(law_links) > 0, "No law links found"

        # Test first law link
        if law_links:
            first_law_href = law_links[0]["href"]
            response = self.client.get(first_law_href)
            assert response.status_code == 200, f"Law link {first_law_href} failed"

        return True

    def test_explanation_panel_link(self):
        """Test that explanation panel has wetten link"""
        print("\n🧪 Testing explanation panel wetten link...")

        # Simulate getting an explanation
        response = self.client.get("/laws/explanation?service=TOESLAGEN&law=wet_op_de_zorgtoeslag&bsn=100000001")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            wetten_link = soup.find("a", string=lambda text: text and "regelspraak" in text)
            assert wetten_link is not None, "Wetten link not found in explanation panel"
            assert wetten_link.get("href") == "/wetten", "Wrong href for wetten link"
            print("✅ Wetten link found in explanation panel")

        return True

    def test_responsive_design(self):
        """Test that pages have responsive design elements"""
        print("\n🧪 Testing responsive design...")

        response = self.client.get("/wetten/")  # Add trailing slash
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for responsive grid
        grid_elements = soup.find_all(attrs={"class": lambda x: x and "grid" in x})
        assert len(grid_elements) > 0, "No responsive grid elements found"

        # Check for media query styles
        styles = soup.find_all("style")
        has_media_queries = any("@media" in str(style) for style in styles)
        assert has_media_queries, "No media queries found for responsive design"

        print("✅ Responsive design elements found")
        return True

    def run_all_tests(self):
        """Run all tests and report results"""
        print("🚀 Starting wetten frontend tests...")

        tests = [
            self.test_wetten_homepage,
            self.test_law_detail_page,
            self.test_yaml_detail_page,
            self.test_navigation_links,
            self.test_explanation_panel_link,
            self.test_responsive_design,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"❌ {test.__name__} failed: {e}")
                failed += 1
            except Exception as e:
                print(f"❌ {test.__name__} error: {e}")
                failed += 1

        print(f"\n📊 Test Results: {passed} passed, {failed} failed")
        return failed == 0


async def main():
    """Main test runner"""
    # First check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/")
            if response.status_code != 200:
                print("⚠️  Server not responding properly")
                return
    except Exception:
        print("❌ Server not running. Please start with: uv run web/main.py")
        return

    # Run tests
    tester = TestWettenFrontend()
    success = tester.run_all_tests()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
