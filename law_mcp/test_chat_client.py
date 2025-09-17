#!/usr/bin/env python3
"""
Test script for MCP Chat Client

Tests the MCP connection and tool discovery without requiring Anthropic API key.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from law_mcp.chat_client import MCPChatClient

async def test_mcp_connection():
    """Test MCP connection and tool discovery"""
    print("🧪 Testing MCP Chat Client Connection...")

    client = MCPChatClient("http://localhost:8000/mcp/")

    try:
        await client.initialize()
        print("\n✅ Successfully connected to MCP server!")
        print("📋 Available tools:")

        for tool in client.available_tools:
            print(f"   • {tool['name']}: {tool['description']}")

        # Test Claude tool format conversion
        claude_tools = client.create_claude_tools()
        print(f"\n🔧 Claude-compatible tools: {len(claude_tools)}")

        for tool in claude_tools[:2]:  # Show first 2 tools
            print(f"   • {tool['name']}")
            if 'properties' in tool['input_schema']:
                props = list(tool['input_schema']['properties'].keys())
                print(f"     Parameters: {props}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())