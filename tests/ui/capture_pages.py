#!/usr/bin/env python3
"""Capture page HTML and open in browser for visual inspection"""

import subprocess
import time
import webbrowser
from datetime import datetime

# Pages to capture
PAGES = [
    ("http://localhost:8000/", "homepage"),
    ("http://localhost:8000/wetten/", "wetten_index"),
    ("http://localhost:8000/wetten/BWBR0018451", "law_detail"),
    ("http://localhost:8000/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml", "yaml_detail"),
]


def capture_page(url, name):
    """Capture page HTML and open in browser"""
    print(f"\n📸 Capturing {name} from {url}")

    # Save HTML
    html_file = f"captured_{name}.html"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)

    if result.returncode == 0:
        with open(html_file, "w") as f:
            f.write(result.stdout)
        print(f"✅ Saved HTML to {html_file}")

        # Check for issues in HTML
        html = result.stdout.lower()
        issues = []

        if "404" in html:
            issues.append("Contains 404 errors")
        if "error" in html and "404" not in html:
            issues.append("Contains error messages")
        if "rosanswebtext" in html:
            issues.append("References RO Sans fonts")
        if "container" not in html:
            issues.append("Missing container class")

        if issues:
            print(f"⚠️  Issues found: {', '.join(issues)}")
    else:
        print("❌ Failed to capture page")

    return html_file


def main():
    print(f"🚀 Starting page capture at {datetime.now().strftime('%H:%M:%S')}")
    print("I'll capture the HTML and open pages in your browser for visual inspection")

    captured_files = []

    # Capture all pages
    for url, name in PAGES:
        html_file = capture_page(url, name)
        captured_files.append((url, html_file))
        time.sleep(1)

    # Open in browser
    print("\n🌐 Opening pages in browser for visual inspection...")
    print("Please take screenshots manually using Cmd+Shift+4 on Mac")
    print("Save them with descriptive names!")

    for url, _ in PAGES:
        print(f"\nOpening: {url}")
        webbrowser.open(url)
        time.sleep(2)  # Give time to load

    print("\n📝 Critical things to check:")
    print("1. ❓ Is the navigation clear and consistent?")
    print("2. 🎨 Are the colors and contrast good?")
    print("3. 📱 Is the layout responsive and well-spaced?")
    print("4. 🔗 Do all links work as expected?")
    print("5. 🌊 Is the underwater/above water metaphor clear?")
    print("6. 📖 Is the text readable and well-formatted?")
    print("7. 🚦 Are the legal basis pills visible and clickable?")
    print("8. 🏠 Can you easily navigate back to burger.nl?")

    print("\n✅ Pages opened! Please inspect and take screenshots")


if __name__ == "__main__":
    main()
