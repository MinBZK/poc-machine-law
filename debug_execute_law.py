#!/usr/bin/env python3
"""
Debug execute_law tool specifically
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from fastmcp.client import Client


async def debug_execute_law():
    """Debug execute_law tool response"""
    print("🐛 Debugging execute_law tool...")

    client = Client("http://localhost:8000/mcp/")

    try:
        await client.__aenter__()
        print("✅ Connected to MCP server")

        # Test execute_law
        result = await client.call_tool(
            "execute_law",
            arguments={
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000001"},
                "reference_date": "2025-01-01",
            },
        )

        print(f"\n📋 Result type: {type(result)}")
        print(f"📋 Has structured_content: {hasattr(result, 'structured_content')}")
        print(f"📋 Structured content type: {type(result.structured_content)}")

        if result.structured_content:
            print(f"📋 Structured content keys: {list(result.structured_content.keys())}")

            if "path" in result.structured_content:
                path_data = result.structured_content["path"]
                print(f"📊 Path: {path_data is not None}")
                if path_data:
                    print(f"📊 Path type: {path_data.get('type', 'N/A')}")
            else:
                print("❌ No 'path' key in structured content")

            if "rule_spec" in result.structured_content:
                rule_spec_data = result.structured_content["rule_spec"]
                print(f"📋 Rule spec: {rule_spec_data is not None}")
                if rule_spec_data:
                    print(f"📋 Rule name: {rule_spec_data.get('name', 'N/A')}")
            else:
                print("❌ No 'rule_spec' key in structured content")
        else:
            print("❌ No structured content")

        print(f"\n📋 Content items: {len(result.content)}")
        for i, content in enumerate(result.content):
            print(f"   Content {i + 1}: {content.type} - {content.text[:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(debug_execute_law())
