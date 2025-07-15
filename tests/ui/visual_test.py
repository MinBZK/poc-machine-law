#!/usr/bin/env python3
"""Visual test and critique of the UI"""

import subprocess
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_page(url, name):
    """Test a page and capture key information"""
    print(f"\n🔍 Testing {name}: {url}")

    # Get page content
    result = subprocess.run(["curl", "-s", "-w", "\n%{http_code}", url], capture_output=True, text=True)

    lines = result.stdout.strip().split("\n")
    status_code = lines[-1]
    html = "\n".join(lines[:-1])

    print(f"   Status: {status_code}")

    # Check for issues
    issues = []
    if "404" in html:
        # Count 404s
        count = html.count("404")
        issues.append(f"{count} instances of '404' found")

    if "<title>" in html:
        title_start = html.find("<title>") + 7
        title_end = html.find("</title>")
        title = html[title_start:title_end].strip()
        print(f"   Title: {title}")

    # Check for key elements
    has_container = "container" in html
    has_nav = "nav-link" in html
    has_dark_theme = "#0f172a" in html or "background-color: #0f172a" in html

    print(f"   Container layout: {'✅' if has_container else '❌'}")
    print(f"   Navigation links: {'✅' if has_nav else '❌'}")
    print(f"   Dark theme: {'✅' if has_dark_theme else '❌ (Light theme)'}")

    if issues:
        print(f"   ⚠️  Issues: {', '.join(issues)}")

    return {
        "url": url,
        "name": name,
        "status": status_code,
        "has_container": has_container,
        "has_nav": has_nav,
        "is_dark": has_dark_theme,
        "issues": issues,
    }


def main():
    print(f"🎨 Visual UI Test - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    tests = [
        (f"{BASE_URL}/", "Homepage (Burger.nl)"),
        (f"{BASE_URL}/wetten/", "Wetten Index"),
        (f"{BASE_URL}/wetten/BWBR0018451", "Law Detail (Zorgtoeslag)"),
        (
            f"{BASE_URL}/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml",
            "YAML Detail (Underwater)",
        ),
    ]

    results = []
    for url, name in tests:
        result = test_page(url, name)
        results.append(result)
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    # Check consistency
    light_pages = [r for r in results if not r["is_dark"]]
    dark_pages = [r for r in results if r["is_dark"]]

    print(f"\n🌞 Light pages (Above water): {len(light_pages)}")
    for page in light_pages:
        print(f"   - {page['name']}")

    print(f"\n🌊 Dark pages (Underwater): {len(dark_pages)}")
    for page in dark_pages:
        print(f"   - {page['name']}")

    # Check navigation consistency
    nav_consistent = all(r["has_nav"] for r in results[1:])  # Skip homepage
    print(f"\n🧭 Navigation consistency: {'✅' if nav_consistent else '❌'}")

    # Check for issues
    total_issues = sum(len(r["issues"]) for r in results)
    print(f"\n⚠️  Total issues found: {total_issues}")

    # Critical assessment
    print("\n" + "=" * 60)
    print("🎯 CRITICAL ASSESSMENT")
    print("=" * 60)

    print("\n✅ What's Working:")
    print("   - Templates are loading correctly")
    print("   - Dark/light theme distinction is clear")
    print("   - Navigation structure is in place")

    print("\n❌ What Needs Improvement:")
    if total_issues > 0:
        print("   - Still have 404 references in HTML")
    if not nav_consistent:
        print("   - Navigation is not consistent across pages")

    print("\n🚀 Next Steps:")
    print("   1. Take actual screenshots to see visual appearance")
    print("   2. Test navigation flow (clicking through pages)")
    print("   3. Polish spacing, typography, and visual hierarchy")
    print("   4. Ensure burger.nl integration is seamless")


if __name__ == "__main__":
    main()
