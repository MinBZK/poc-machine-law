#!/usr/bin/env python3
"""
Test MCP Response Format

Direct test to see what the MCP server returns when we call a tool.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from law_mcp.chat_client import MCPChatClient


async def test_mcp_response():
    """Test MCP response format directly"""
    print("🧪 Testing MCP Response Format...")

    client = MCPChatClient("http://localhost:8000/mcp/")

    try:
        await client.initialize()
        print("✅ Connected to MCP server")

        # Test execute_law tool with a simple BSN
        print("\n🔧 Testing execute_law tool...")
        response = await client.call_mcp_tool(
            "execute_law",
            {
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000001"},
                "reference_date": "2025-01-01",
            },
        )

        print("\n📤 Returned text content:")
        print(response)

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(test_mcp_response())
