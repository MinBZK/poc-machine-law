#!/usr/bin/env python3
"""
MCP + Claude Chat Client

Een eenvoudige CLI chat client die MCP tools gebruikt om met Claude te praten
over Nederlandse wetgeving.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    uv run python law_mcp/chat_client.py

Voorbeeld conversatie:
    Gebruiker: "Mijn BSN is 100000001. Heb ik recht op huurtoeslag?"
    Claude: [gebruikt MCP tools om profiel op te halen en huurtoeslag te berekenen]
"""

import asyncio
import json
import os
import sys
from typing import Any

import anthropic
from fastmcp.client import Client


class MCPChatClient:
    def __init__(self, mcp_url: str = "http://localhost:8000/mcp/"):
        self.mcp_url = mcp_url
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.mcp_client = None
        self.available_tools = []
        self.conversation_history = []

    async def initialize(self):
        """Initialize MCP connection and fetch available tools"""
        print("🔌 Connecting to MCP server...")
        self.mcp_client = Client(self.mcp_url)

        try:
            # Initialize connection
            await self.mcp_client.__aenter__()

            # Fetch available tools
            tools = await self.mcp_client.list_tools()
            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                }
                for tool in tools
            ]

            print(f"✅ Connected! Found {len(self.available_tools)} MCP tools:")
            for tool in self.available_tools:
                print(f"   • {tool['name']}: {tool['description']}")

        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            print(f"   Make sure the server is running on {self.mcp_url}")
            sys.exit(1)

    async def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool and return the result as a string"""
        try:
            print(f"🔧 Calling MCP tool: {tool_name} with {arguments}")
            result = await self.mcp_client.call_tool(tool_name, arguments=arguments)

            # Print the complete MCP response for debugging
            print("\n📋 Complete MCP Response:")
            print(f"   Type: {type(result)}")

            if hasattr(result, "content"):
                print(f"   Content items: {len(result.content)}")
                for i, content in enumerate(result.content):
                    print(f"   Content {i + 1}:")
                    print(f"     Type: {type(content)}")
                    if hasattr(content, "type"):
                        print(f"     Content type: {content.type}")
                    if hasattr(content, "text"):
                        print(f"     Text: {content.text}")
                    if hasattr(content, "data"):
                        print(f"     Data: {content.data}")
                    print()

            # Check for structured content
            if hasattr(result, "structured_content"):
                print(f"   Structured content available: {result.structured_content is not None}")
                if result.structured_content:
                    print(f"   Structured content: {json.dumps(result.structured_content, indent=2)}")
            else:
                print("   No structured_content attribute found")

            print(f"   All attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
            print("-" * 60)

            # Extract text content from MCP response
            content_text = []
            for content in result.content:
                if hasattr(content, "text"):
                    content_text.append(content.text)
                elif hasattr(content, "data"):
                    content_text.append(json.dumps(content.data, indent=2))

            return "\n".join(content_text)

        except Exception as e:
            print(f"❌ Error calling {tool_name}: {str(e)}")
            return f"Error calling {tool_name}: {str(e)}"

    def create_claude_tools(self) -> list[dict[str, Any]]:
        """Convert MCP tools to Claude-compatible format"""
        claude_tools = []

        for tool in self.available_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": {"type": "object", "properties": {}, "required": []},
            }

            # Add basic schema for known tools
            if tool["name"] == "execute_law":
                claude_tool["input_schema"]["properties"] = {
                    "service": {"type": "string", "description": "Service provider (e.g., TOESLAGEN, RVO)"},
                    "law": {"type": "string", "description": "Law identifier (e.g., zorgtoeslagwet, wpm)"},
                    "parameters": {"type": "object", "description": 'Parameters for the law (e.g., {"BSN": "123"})'},
                    "reference_date": {"type": "string", "description": "Reference date (YYYY-MM-DD)"},
                }
                claude_tool["input_schema"]["required"] = ["service", "law", "parameters"]

            elif tool["name"] == "check_eligibility":
                claude_tool["input_schema"]["properties"] = {
                    "service": {"type": "string"},
                    "law": {"type": "string"},
                    "parameters": {"type": "object"},
                }
                claude_tool["input_schema"]["required"] = ["service", "law", "parameters"]

            claude_tools.append(claude_tool)

        return claude_tools

    async def chat_with_claude(self, user_message: str) -> str:
        """Send message to Claude with MCP tools available"""
        self.conversation_history.append({"role": "user", "content": user_message})

        system_prompt = """Je bent een behulpzame assistent die Nederlandse burgers helpt met vragen over uitkeringen, toeslagen en andere overheidsregelingen.

Je hebt toegang tot MCP tools waarmee je Nederlandse wetten kunt uitvoeren en controleren. Gebruik deze tools om accurate informatie te geven.

Belangrijke tools:
- execute_law: Voer een specifieke wet uit voor gegeven parameters
- check_eligibility: Controleer of iemand recht heeft op een uitkering/toeslag

Veel voorkomende wetten en services:
- Huurtoeslag: service="TOESLAGEN", law="wet_op_de_huurtoeslag"
- Zorgtoeslag: service="TOESLAGEN", law="zorgtoeslagwet"
- AOW: service="SVB", law="algemene_ouderdomswet"
- WPM (voor bedrijven): service="RVO", law="wpm" (gebruik KVK_NUMMER i.p.v. BSN)

Als een gebruiker een BSN noemt, gebruik dat in de parameters: {"BSN": "123456789"}

Geef altijd vriendelijke, duidelijke uitleg in het Nederlands."""

        try:
            # Call Claude with MCP tools
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=self.conversation_history,
                tools=self.create_claude_tools(),
            )

            # Process response and handle tool calls
            assistant_message = {"role": "assistant", "content": []}

            for content_block in response.content:
                if content_block.type == "text":
                    assistant_message["content"].append({"type": "text", "text": content_block.text})

                elif content_block.type == "tool_use":
                    # Execute MCP tool
                    tool_result = await self.call_mcp_tool(content_block.name, content_block.input)

                    assistant_message["content"].append(
                        {
                            "type": "tool_use",
                            "id": content_block.id,
                            "name": content_block.name,
                            "input": content_block.input,
                        }
                    )

                    # Send tool result back to Claude
                    self.conversation_history.append(assistant_message)
                    self.conversation_history.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "tool_result", "tool_use_id": content_block.id, "content": tool_result}
                            ],
                        }
                    )

                    # Get Claude's interpretation of the result
                    follow_up = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        system=system_prompt,
                        messages=self.conversation_history,
                        tools=self.create_claude_tools(),
                    )

                    return follow_up.content[0].text if follow_up.content else "Geen antwoord ontvangen."

            # If no tools were called, return the text response
            self.conversation_history.append(assistant_message)
            text_parts = [block["text"] for block in assistant_message["content"] if block["type"] == "text"]
            return "\n".join(text_parts)

        except Exception as e:
            return f"❌ Fout bij het praten met Claude: {str(e)}"

    async def start_chat(self):
        """Start interactive chat session"""
        print("\n" + "=" * 60)
        print("🤖 MCP + Claude Chat Client voor Nederlandse Wetgeving")
        print("=" * 60)
        print("\nVoorbeelden van vragen:")
        print("• 'Mijn BSN is 100000001. Heb ik recht op huurtoeslag?'")
        print("• 'Kan ik zorgtoeslag krijgen met BSN 100000002?'")
        print("• 'Wat is de AOW-leeftijd voor iemand geboren in 1960?'")
        print("\nType 'quit' om te stoppen.\n")

        while True:
            try:
                user_input = input("👤 Jij: ").strip()

                if user_input.lower() in ["quit", "exit", "stop"]:
                    print("👋 Tot ziens!")
                    break

                if not user_input:
                    continue

                print("🤖 Claude: ", end="", flush=True)
                response = await self.chat_with_claude(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n👋 Tot ziens!")
                break
            except Exception as e:
                print(f"❌ Fout: {e}")

    async def cleanup(self):
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)


async def main():
    """Main function"""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable not set!")
        print("   Export your API key: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Create and initialize client
    chat_client = MCPChatClient()

    try:
        await chat_client.initialize()
        await chat_client.start_chat()
    finally:
        await chat_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
