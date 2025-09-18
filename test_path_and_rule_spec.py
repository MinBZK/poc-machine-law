#!/usr/bin/env python3
"""
Test script to verify both path and rule_spec information appear in MCP responses
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from fastmcp.client import Client


async def test_path_and_rule_spec():
    """Test if both path and rule_spec information are included in MCP responses"""
    print("🧪 Testing Path and Rule Spec Information in MCP Responses...")

    client = Client("http://localhost:8000/mcp/")

    try:
        await client.__aenter__()
        print("✅ Connected to MCP server")

        # Test execute_law tool
        print("\n🔧 Testing execute_law tool for path and rule_spec information...")
        result = await client.call_tool(
            "execute_law",
            arguments={
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000001"},
                "reference_date": "2025-01-01",
            },
        )

        print("\n📋 MCP Response structure:")
        print(f"   Content items: {len(result.content)}")

        if hasattr(result, "structured_content") and result.structured_content:
            structured = result.structured_content
            print(f"   Structured content keys: {list(structured.keys())}")

            if "data" in structured:
                data = structured["data"]
                print(f"   Data keys: {list(data.keys())}")

                # Check for path information
                if "path" in data:
                    path_data = data["path"]
                    if path_data:
                        print(f"\n✅ Path information found!")
                        print(f"   Path type: {type(path_data)}")
                        if isinstance(path_data, dict):
                            print(f"   Path keys: {list(path_data.keys())}")
                            print(f"   Path rule: {path_data.get('rule', 'N/A')}")
                            print(f"   Path result: {path_data.get('result', 'N/A')}")
                            if "children" in path_data and path_data["children"]:
                                print(f"   Children count: {len(path_data['children'])}")
                                print(
                                    f"   First child rule: {path_data['children'][0].get('rule', 'N/A') if path_data['children'] else 'N/A'}"
                                )
                    else:
                        print(f"\n❌ Path data is None")
                else:
                    print(f"\n❌ No path found in data")

                # Check for rule_spec information
                if "rule_spec" in data:
                    rule_spec_data = data["rule_spec"]
                    if rule_spec_data:
                        print(f"\n✅ Rule spec information found!")
                        print(f"   Rule spec type: {type(rule_spec_data)}")
                        if isinstance(rule_spec_data, dict):
                            print(f"   Rule spec keys: {list(rule_spec_data.keys())}")
                            print(f"   Rule name: {rule_spec_data.get('name', 'N/A')}")
                            description = rule_spec_data.get("description", "N/A")
                            print(
                                f"   Rule description: {description[:100]}..."
                                if len(description) > 100
                                else f"   Rule description: {description}"
                            )

                            if "properties" in rule_spec_data:
                                props = rule_spec_data["properties"]
                                print(f"   Properties keys: {list(props.keys())}")
                                print(f"   Input fields: {len(props.get('input', []))}")
                                print(f"   Output fields: {len(props.get('output', []))}")
                                print(f"   Parameter fields: {len(props.get('parameters', []))}")

                                # Show some input field names
                                inputs = props.get("input", [])
                                if inputs:
                                    input_names = [inp.get("name", "N/A") for inp in inputs[:3]]
                                    print(f"   First 3 input names: {input_names}")
                    else:
                        print(f"\n❌ Rule spec data is None")
                else:
                    print(f"\n❌ No rule_spec found in data")

            else:
                print(f"\n❌ No data in structured content")
        else:
            print(f"\n❌ No structured content available")
            print(f"   Response attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")

        # Test with a different law
        print(f"\n🔧 Testing with WPM law...")
        result2 = await client.call_tool(
            "execute_law",
            arguments={
                "service": "RVO",
                "law": "wpm",
                "parameters": {"KVK_NUMMER": "12345678"},
                "reference_date": "2025-01-01",
            },
        )

        if hasattr(result2, "structured_content") and result2.structured_content:
            data2 = result2.structured_content.get("data", {})
            path_found = "path" in data2 and data2["path"] is not None
            rule_spec_found = "rule_spec" in data2 and data2["rule_spec"] is not None
            print(f"   WPM - Path found: {path_found}")
            print(f"   WPM - Rule spec found: {rule_spec_found}")

            if rule_spec_found:
                wpm_rule = data2["rule_spec"]
                print(f"   WPM rule name: {wpm_rule.get('name', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_path_and_rule_spec())
