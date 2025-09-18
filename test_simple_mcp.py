#!/usr/bin/env python3
"""
Simple test to see what the MCP client is actually receiving
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from fastmcp.client import Client


async def test_simple_mcp():
    """Simple test to see what we're getting back"""
    print("🧪 Simple MCP Test...")

    client = Client("http://localhost:8000/mcp/")

    try:
        await client.__aenter__()
        print("✅ Connected to MCP server")

        # Test execute_law tool
        result = await client.call_tool(
            "execute_law",
            arguments={
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000001"},
                "reference_date": "2025-01-01",
            },
        )

        print(f"\n📋 Raw result type: {type(result)}")
        print(f"📋 Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")

        if hasattr(result, "content"):
            print(f"📋 Content: {result.content}")

        if hasattr(result, "structured_content"):
            print(f"📋 Structured content type: {type(result.structured_content)}")
            print(f"📋 Structured content value: {result.structured_content}")

        if hasattr(result, "data"):
            print(f"📋 Data: {result.data}")

        if hasattr(result, "is_error"):
            print(f"📋 Is error: {result.is_error}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_simple_mcp())
