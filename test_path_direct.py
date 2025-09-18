#!/usr/bin/env python3
"""
Direct test of MCP endpoint to check path information
"""

import json
import requests


def test_path_direct():
    """Test MCP endpoint directly"""
    print("🧪 Testing MCP Path Information Directly...")

    # Test execute_law tool
    payload = {
        "tool": "execute_law",
        "arguments": {
            "service": "TOESLAGEN",
            "law": "zorgtoeslagwet",
            "parameters": {"BSN": "100000001"},
            "reference_date": "2025-01-01",
        },
    }

    try:
        response = requests.post(
            "http://localhost:8000/mcp/", json=payload, headers={"Content-Type": "application/json"}
        )

        print(f"📤 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response structure:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000] + "...")

            # Check if path is included
            if "structured_content" in result:
                structured = result["structured_content"]
                if "data" in structured and "path" in structured["data"]:
                    path_data = structured["data"]["path"]
                    if path_data:
                        print(f"\n✅ Path information found!")
                        print(f"   Path rule: {path_data.get('rule', 'N/A')}")
                        print(f"   Path result: {path_data.get('result', 'N/A')}")
                        if "children" in path_data:
                            print(f"   Children count: {len(path_data['children']) if path_data['children'] else 0}")
                    else:
                        print(f"\n❌ Path data is None")
                else:
                    print(f"\n❌ No path in structured content")
                    if "data" in structured:
                        print(f"   Available data keys: {list(structured['data'].keys())}")
            else:
                print(f"\n❌ No structured_content in response")
                print(f"   Available keys: {list(result.keys())}")

        else:
            print(f"❌ Request failed: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_path_direct()
