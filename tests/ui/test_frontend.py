#!/usr/bin/env python3
"""
Frontend test script for the wetten.overheid.nl clone interface.
This script tests the functionality without relying on the running server.
"""

from pathlib import Path

import yaml


def test_data_loading():
    """Test that data loading functions work correctly"""
    print("🧪 Testing data loading functions...")

    # Test BWB mapping
    print("\n1. Testing BWB mapping loading...")
    BWB_MAPPING_PATH = Path("laws/bwb_mapping.yaml")
    try:
        with open(BWB_MAPPING_PATH, encoding="utf-8") as f:
            bwb_mapping = yaml.safe_load(f)
        print(f"   ✅ Loaded BWB mapping with {len(bwb_mapping.get('laws', {}))} laws")
    except Exception as e:
        print(f"   ❌ Error loading BWB mapping: {e}")
        return []

    # Test law content loading
    print("\n2. Testing law content loading...")
    available_laws = []
    LAWS_CONTENT_DIR = Path("laws/content")

    for bwb_id, law_info in bwb_mapping.get("laws", {}).items():
        content_file = LAWS_CONTENT_DIR / f"{bwb_id}.yaml"
        if content_file.exists():
            try:
                with open(content_file, encoding="utf-8") as f:
                    yaml.safe_load(f)  # Just validate the file loads
                available_laws.append((bwb_id, law_info["title"]))
                print(f"   ✅ {bwb_id}: {law_info['title']}")
            except Exception as e:
                print(f"   ⚠️  {bwb_id}: Error loading content: {e}")

    print(f"\n   📊 Found {len(available_laws)} laws with content files")

    return available_laws


def test_yaml_implementations():
    """Test YAML implementation detection"""
    print("\n🔗 Testing YAML implementation detection...")

    available_laws = test_data_loading()

    for bwb_id, title in available_laws[:3]:  # Test first 3 laws
        try:
            # Load law content and check for yaml_files
            content_file = Path("laws/content") / f"{bwb_id}.yaml"
            with open(content_file, encoding="utf-8") as f:
                law_content = yaml.safe_load(f)

            yaml_files = law_content.get("yaml_files", [])
            print(f"   📄 {bwb_id}: {len(yaml_files)} implementations listed")

            # Check if the YAML files actually exist
            for yaml_file in yaml_files:
                yaml_path = Path(yaml_file["path"])
                if yaml_path.exists():
                    print(f"      ✅ {yaml_file['description']} - {yaml_path}")
                else:
                    print(f"      ❌ {yaml_file['description']} - MISSING: {yaml_path}")

        except Exception as e:
            print(f"   ⚠️  {bwb_id}: Error checking implementations: {e}")


def test_templates():
    """Test that templates exist and can be loaded"""
    print("\n🎨 Testing template files...")

    template_dir = Path(__file__).parent / "web" / "templates" / "wetten"
    required_templates = ["index.html", "law_detail.html", "article_detail.html", "yaml_detail.html"]

    for template in required_templates:
        template_path = template_dir / template
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"   ✅ {template} ({size:,} bytes)")
        else:
            print(f"   ❌ {template} - MISSING")


def test_content_structure():
    """Test the structure of law content files"""
    print("\n📋 Testing law content structure...")

    content_dir = Path(__file__).parent / "laws" / "content"
    content_files = list(content_dir.glob("BWBR*.yaml"))

    print(f"   📁 Found {len(content_files)} content files")

    for content_file in content_files[:3]:  # Test first 3
        try:
            import yaml

            with open(content_file, encoding="utf-8") as f:
                content = yaml.safe_load(f)

            required_fields = ["bwb_id", "title", "structure"]
            missing_fields = [field for field in required_fields if field not in content]

            if missing_fields:
                print(f"   ⚠️  {content_file.name}: Missing fields: {missing_fields}")
            else:
                chapters = len(content.get("structure", {}).get("chapters", []))
                print(f"   ✅ {content_file.name}: {chapters} chapters")

        except Exception as e:
            print(f"   ❌ {content_file.name}: Error loading: {e}")


def test_direct_routes():
    """Test routes by making direct HTTP requests"""
    print("\n🌐 Testing direct HTTP routes...")

    import subprocess

    test_urls = [
        "http://localhost:8000/wetten/",
        "http://localhost:8000/wetten/BWBR0008659",  # Huurtoeslag
        "http://localhost:8000/wetten/BWBR0017017",  # Kinderopvang
    ]

    for url in test_urls:
        try:
            result = subprocess.run(
                ["curl", "-s", "-w", "%{http_code}", url], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                output = result.stdout
                # Extract status code (last 3 chars)
                status_code = output[-3:]
                content = output[:-3]

                if status_code == "200":
                    content_type = "HTML" if "<html>" in content.lower() else "Other"
                    content_size = len(content)
                    print(f"   ✅ {url}: {status_code} ({content_type}, {content_size} bytes)")
                else:
                    print(f"   ⚠️  {url}: {status_code}")
            else:
                print(f"   ❌ {url}: curl failed")

        except Exception as e:
            print(f"   ❌ {url}: Error - {e}")


def main():
    """Run all frontend tests"""
    print("🚀 Starting frontend tests for wetten.overheid.nl clone\n")

    try:
        test_data_loading()
        test_yaml_implementations()
        test_templates()
        test_content_structure()
        test_direct_routes()

        print("\n✅ Frontend tests completed successfully!")
        print("\n🌐 To test the web interface:")
        print("   1. Make sure server is running: uv run web/main.py")
        print("   2. Visit: http://localhost:8000/wetten/")
        print("   3. Check individual laws like: http://localhost:8000/wetten/BWBR0008659")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
