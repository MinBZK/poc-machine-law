#!/usr/bin/env python3
"""
Test script to verify path information appears in MCP responses
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from fastmcp.client import Client


async def test_path_information():
    """Test if path information is included in MCP responses"""
    print("🧪 Testing Path Information in MCP Responses...")

    client = Client("http://localhost:8000/mcp/")

    try:
        await client.__aenter__()
        print("✅ Connected to MCP server")

        # Test execute_law tool with path information
        print("\n🔧 Testing execute_law tool for path information...")
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
        for i, content in enumerate(result.content):
            print(f"   Content {i + 1}: {content.type}")

        if hasattr(result, "structured_content") and result.structured_content:
            structured = result.structured_content
            print(f"\n📊 Structured content keys: {list(structured.keys())}")

            if "data" in structured and "path" in structured["data"]:
                path_data = structured["data"]["path"]
                if path_data:
                    print(f"\n🛤️  Path information found!")
                    print(f"   Path type: {type(path_data)}")
                    print(f"   Path keys: {list(path_data.keys()) if isinstance(path_data, dict) else 'Not a dict'}")

                    # Show first few levels of path structure
                    if isinstance(path_data, dict):
                        print(f"   Path rule: {path_data.get('rule', 'N/A')}")
                        print(f"   Path result: {path_data.get('result', 'N/A')}")
                        if "children" in path_data:
                            print(f"   Children count: {len(path_data['children']) if path_data['children'] else 0}")
                else:
                    print(f"\n❌ Path data is None")
            else:
                print(f"\n❌ No path found in structured content")
                if "data" in structured:
                    print(f"   Available data keys: {list(structured['data'].keys())}")

        else:
            print(f"\n❌ No structured content available")

        # Test check_eligibility tool with correct law name
        print(f"\n🔧 Testing check_eligibility tool for path information...")
        result2 = await client.call_tool(
            "check_eligibility",
            arguments={"service": "TOESLAGEN", "law": "wet_op_de_huurtoeslag", "parameters": {"BSN": "100000002"}},
        )

        if hasattr(result2, "structured_content") and result2.structured_content:
            if "path" in result2.structured_content:
                path_data2 = result2.structured_content["path"]
                print(f"✅ Path information also found in check_eligibility!")
                print(f"   Path type: {type(path_data2)}")
            else:
                print(f"❌ No path in check_eligibility structured content")
                print(f"   Available keys: {list(result2.structured_content.keys())}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_path_information())
