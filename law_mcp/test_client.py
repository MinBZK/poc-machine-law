#!/usr/bin/env python3
"""
MCP Client Example - Working example using FastMCP library

This demonstrates how to connect to our MCP Streamable HTTP server
and execute Dutch law operations using the Model Context Protocol.

Usage:
    uv run python law_mcp/test_client.py

Requirements:
    - MCP server running on http://localhost:8001/mcp/
    - FastMCP client library
"""

import asyncio

from fastmcp.client import Client


async def test_fastmcp_client():
    """Test using FastMCP client against our MCP server"""
    print("🚀 Testing with FastMCP Client Library")

    # Connect to our MCP server
    async with Client("http://localhost:8002/mcp/") as client:
        print("✅ Connected to MCP server")

        # List tools (FastMCP auto-initializes)
        print("\n1️⃣ Listing tools...")
        tools = await client.list_tools()
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"     • {tool.name}: {tool.description[:50]}...")

        # Call execute_law tool
        print("\n2️⃣ Executing WPM law...")
        result = await client.call_tool(
            "execute_law", arguments={"service": "RVO", "law": "wpm", "parameters": {"KVK_NUMMER": "12345678"}}
        )

        print(f"   Tool call result: {len(result.content)} content items")

        # Print human-readable content
        for content in result.content:
            if hasattr(content, "text"):
                print(f"   Human-readable: {content.text}")
            elif hasattr(content, "data"):
                print(f"   Data: {content.data}")

        # Print structured content if available
        if hasattr(result, "structured_content") and result.structured_content:
            print("   Structured content available!")
            structured = result.structured_content
            if isinstance(structured, dict):
                if "success" in structured:
                    print(f"   Success: {structured.get('success')}")
                    if structured.get("success") and "data" in structured:
                        data = structured["data"]
                        print(f"   Requirements Met: {data.get('requirements_met')}")
                        print(f"   Employees: {data.get('output', {}).get('aantal_werknemers')}")
                else:
                    print(f"   Structured data: {structured}")
        else:
            # Fallback to old JSON parsing for backward compatibility
            for content in result.content:
                if hasattr(content, "text"):
                    import json

                    try:
                        parsed_data = json.loads(content.text)
                        print(f"   (Fallback) Success: {parsed_data.get('success')}")
                        if parsed_data.get("success"):
                            data = parsed_data["data"]
                            print(f"   (Fallback) Requirements Met: {data.get('requirements_met')}")
                            print(f"   (Fallback) Employees: {data.get('output', {}).get('aantal_werknemers')}")
                    except json.JSONDecodeError:
                        print(f"   (Fallback) Text: {content.text[:100]}...")

        # List resources
        print("\n3️⃣ Listing resources...")
        resources = await client.list_resources()
        print(f"   Found {len(resources)} resources:")
        for resource in resources:
            print(f"     • {resource.name}: {resource.uri}")

        # Read resource
        print("\n4️⃣ Reading laws resource...")
        resource_content = await client.read_resource("laws://list")
        print(f"   Resource content: {len(resource_content)} items")

        # Parse the resource content
        for content in resource_content:
            if hasattr(content, "text"):
                import json

                try:
                    laws_data = json.loads(content.text)
                    total = laws_data.get("total_count", 0)
                    laws = laws_data.get("available_laws", [])
                    print(f"   Total laws: {total}")
                    print(f"   Example laws: {[law.get('law', 'unknown') for law in laws[:3]]}")
                except json.JSONDecodeError:
                    print(f"   Raw text: {content.text[:100]}...")

        print("\n✅ FastMCP client test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_fastmcp_client())
