#!/usr/bin/env python3
"""
Test Law Metadata in MCP Response

Test to see if the law description and metadata are included in MCP responses.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from law_mcp.chat_client import MCPChatClient


async def test_law_metadata():
    """Test if law metadata is included in MCP response"""
    print("🧪 Testing Law Metadata in MCP Response...")

    client = MCPChatClient("http://localhost:8000/mcp/")

    try:
        await client.initialize()
        print("✅ Connected to MCP server")

        # Test WPM law to see if we get the description
        print("\n🔧 Testing WPM law metadata...")
        response = await client.call_mcp_tool(
            "execute_law",
            {"service": "RVO", "law": "wpm", "parameters": {"KVK_NUMMER": "12345678"}, "reference_date": "2025-01-01"},
        )

        print("\n📤 Response should now include WPM description...")

        # Parse the response to show law metadata
        try:
            response_data = json.loads(response)
            if "data" in response_data and "law_metadata" in response_data["data"]:
                metadata = response_data["data"]["law_metadata"]
                print("\n📋 Law Metadata Found:")
                print(f"   Name: {metadata.get('name', 'N/A')}")
                print(f"   Description: {metadata.get('description', 'N/A')}")
                print(f"   Service: {metadata.get('service', 'N/A')}")
                print(f"   Type: {metadata.get('law_type', 'N/A')}")
                print(f"   Character: {metadata.get('legal_character', 'N/A')}")
            else:
                print("❌ No law_metadata found in response")
        except json.JSONDecodeError as e:
            print(f"❌ Could not parse response: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(test_law_metadata())
