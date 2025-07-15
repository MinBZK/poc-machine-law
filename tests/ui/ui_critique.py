#!/usr/bin/env python3
"""Open pages for visual critique and provide improvement suggestions"""

import webbrowser

BASE_URL = "http://localhost:8000"

PAGES = [
    {
        "url": f"{BASE_URL}/",
        "name": "Burger.nl Homepage",
        "purpose": "Entry point for citizens",
        "check": ["Clear path to laws/wetten", "Professional government look", "Easy to understand purpose"],
    },
    {
        "url": f"{BASE_URL}/wetten/",
        "name": "Wetten Index",
        "purpose": "Overview of available laws",
        "check": [
            "Clear navigation back to burger.nl",
            "Easy to find specific laws",
            "Visual distinction between law text and regelspraak links",
            "Consistent with wetten.overheid.nl style",
        ],
    },
    {
        "url": f"{BASE_URL}/wetten/BWBR0018451",
        "name": "Law Detail (Above Water)",
        "purpose": "Human-readable law text",
        "check": [
            "Light theme (above water)",
            "Clear article structure",
            "Easy navigation to regelspraak",
            "Professional typography",
            "Good spacing and readability",
        ],
    },
    {
        "url": f"{BASE_URL}/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml",
        "name": "YAML Detail (Underwater)",
        "purpose": "Machine-readable implementation",
        "check": [
            "Dark theme (underwater metaphor clear)",
            "Legal basis pills are visible and clickable",
            "Easy navigation back to law text",
            "Regelspraak is readable",
            "Parameters and calculations are clear",
        ],
    },
]


def main():
    print("🎨 UI CRITIQUE SESSION")
    print("=" * 60)
    print("I'll open each page in your browser.")
    print("Please take screenshots and note improvements needed.")
    print("=" * 60)

    for i, page in enumerate(PAGES):
        print(f"\n📄 Page {i + 1}/{len(PAGES)}: {page['name']}")
        print(f"   URL: {page['url']}")
        print(f"   Purpose: {page['purpose']}")
        print("\n   ✅ Check for:")
        for check in page["check"]:
            print(f"      - {check}")

        print("\n   Opening in browser...")
        webbrowser.open(page["url"])

        if i < len(PAGES) - 1:
            input("\n   Press Enter when ready for next page...")

    print("\n" + "=" * 60)
    print("🎯 KEY IMPROVEMENTS NEEDED")
    print("=" * 60)

    improvements = """
1. VISUAL HIERARCHY
   - Headers need more weight and spacing
   - Buttons should be more prominent
   - Better contrast for important elements

2. NAVIGATION CLARITY
   - Breadcrumbs would help orientation
   - Active page indicator in navigation
   - Clearer "above/below water" indicators

3. TYPOGRAPHY & SPACING
   - Increase line height for better readability
   - More generous padding in content areas
   - Consistent heading sizes

4. UNDERWATER THEME
   - Darker background for stronger contrast
   - Blue accent colors for underwater feel
   - Better visual separation of sections

5. INTERACTION FEEDBACK
   - Hover states for all clickable elements
   - Loading indicators where needed
   - Success feedback after navigation
"""

    print(improvements)

    print("\n🚀 NEXT STEPS:")
    print("1. Implement visual improvements")
    print("2. Add breadcrumb navigation")
    print("3. Polish typography and spacing")
    print("4. Add micro-interactions")
    print("5. Test complete user flow")


if __name__ == "__main__":
    main()
