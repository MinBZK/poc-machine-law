#!/usr/bin/env python3
"""
Interactive Chat with LangChain + MCP Integration

This implements an interactive command-line chat that demonstrates:
- Official LangChain MCP integration using langchain-mcp-adapters
- LangGraph ReAct agents for reasoning
- Dutch law execution via MCP protocol
- Claude for natural language understanding

Usage: uv run law_mcp/interactive_chat.py
"""

import asyncio
import os
import re
import sys

import aiohttp
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


class OfficialLangChainMCP:
    """Official LangChain + MCP integration using langchain-mcp-adapters"""

    def __init__(self):
        # Get API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("\n❌ Anthropic API key not found!")
            print("💡 Set your API key with:")
            print("   export ANTHROPIC_API_KEY='sk-ant-api03-...'")
            print("\n🔑 Or enter it now:")
            try:
                self.api_key = input("API Key: ").strip()
                if not self.api_key:
                    print("❌ API key required!")
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print("\n❌ API key required!")
                sys.exit(1)

        # Initialize Claude LLM
        self.llm = ChatAnthropic(
            api_key=self.api_key, model="claude-3-5-sonnet-20241022", temperature=0.1, max_tokens=2000
        )

        # MCP client configuration for our law server
        self.mcp_client = MultiServerMCPClient(
            {
                "law_server": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8000/mcp",
                }
            }
        )

        # Agent will be created after loading tools
        self.agent = None
        self.tools = []

        # Conversation state
        self.current_bsn = None
        self.current_kvk = None

    async def _load_available_laws(self) -> str:
        """Load available laws from MCP resources"""
        print("📋 Loading available laws from MCP resources...")

        # Call MCP resources/read for laws://list
        async with aiohttp.ClientSession() as session:
            request = {"jsonrpc": "2.0", "method": "resources/read", "params": {"uri": "laws://list"}, "id": 1}

            async with session.post(
                "http://localhost:8000/mcp/rpc", json=request, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result and "contents" in result["result"]:
                        content = result["result"]["contents"][0]["text"]
                        print("✅ Laws loaded from MCP:")
                        # Show first few lines of laws for verification
                        preview_lines = content.split("\n")[:20]
                        for line in preview_lines:
                            if line.strip():
                                print(f"   {line}")
                        if len(content.split("\n")) > 20:
                            print("   ...")
                        return content
                    else:
                        raise RuntimeError("No laws content found in MCP response")
                else:
                    raise RuntimeError(f"MCP resources/read failed with status {response.status}")

    async def initialize(self) -> bool:
        """Initialize MCP client and load tools"""
        try:
            print("🔌 Initializing official LangChain MCP integration...")

            # Test MCP server connection
            print("🔧 Testing MCP server connection...")

            # Load tools from MCP server
            print("📡 Loading tools from MCP server...")
            self.tools = await self.mcp_client.get_tools()

            if not self.tools:
                print("❌ No tools loaded from MCP server")
                return False

            print(f"✅ Loaded {len(self.tools)} MCP tools:")
            for tool in self.tools:
                print(f"   • {tool.name}: {tool.description[:80]}...")
                # Show if tool has schema/examples
                if hasattr(tool, "args_schema") and tool.args_schema:
                    try:
                        if hasattr(tool.args_schema, "model_json_schema"):
                            schema_info = str(tool.args_schema.model_json_schema())
                        else:
                            schema_info = str(tool.args_schema)

                        if "examples" in schema_info.lower():
                            print("     ✅ Has examples in schema")
                        else:
                            print("     ⚠️  No examples found in schema")
                    except Exception:
                        print("     ℹ️  Schema available (could not inspect)")

            # Load available laws dynamically
            available_laws = await self._load_available_laws()

            # Create LangGraph ReAct agent with MCP tools
            print("🤖 Creating LangGraph ReAct agent...")
            self.agent = create_react_agent(
                self.llm,
                self.tools,
                state_modifier=f"""Je bent een expert assistent voor Nederlandse wetgeving en uitkeringen.
Je helpt burgers en bedrijven met vragen over toeslagen, uitkeringen, en andere overheidsregelingen.

{available_laws}

PARAMETERS:
- Voor burgers: {{"BSN": "100000001"}} (standaard test BSN)
- Voor bedrijven: {{"KVK_NUMMER": "58372941"}} (standaard test KVK)

SCENARIO OVERRIDES (voor wat-als vragen):
- Inkomen wijzigen: {{"overrides": {{"UWV": {{"inkomen": 3500000}}}}}} (€35,000 per jaar)
- Werknemers: {{"overrides": {{"RVO": {{"AANTAL_WERKNEMERS": 150}}}}}}

OUTPUT FIELDS voor calculate_benefit_amount:
- "hoogte_toeslag" - voor zorgtoeslag en huurtoeslag bedragen
- "bedrag_per_maand" - voor maandelijkse uitkeringen (AOW, bijstand)
- "jaarbedrag" - voor jaarlijkse bedragen

WERKWIJZE:
1. Voor eligibiliteit vragen: gebruik check_eligibility
2. Voor exacte bedragen: gebruik calculate_benefit_amount MET output_field!
3. Voor complete overzichten: gebruik execute_law
4. Geef altijd duidelijke uitleg in Nederlands

Gebruik ALTIJD de beschikbare MCP tools voor berekeningen. Geef duidelijke uitleg in begrijpelijk Nederlands.""",
            )

            print("✅ LangGraph agent created successfully!")
            return True

        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False

    async def process_message(self, user_message: str) -> str:
        """Process message with LangGraph agent"""

        # Extract BSN and KVK numbers if mentioned
        bsn_match = re.search(r"\bBSN\s*(?:is\s*)?(\d{9})\b|\b(\d{9})\b.*BSN", user_message, re.IGNORECASE)
        if bsn_match:
            self.current_bsn = bsn_match.group(1) or bsn_match.group(2)
            print(f"📋 BSN detected and remembered: {self.current_bsn}")

        kvk_match = re.search(r"\bKVK[_\s]*NUMMER\s*(?:is\s*)?(\d{8})\b|\b(\d{8})\b.*KVK", user_message, re.IGNORECASE)
        if kvk_match:
            self.current_kvk = kvk_match.group(1) or kvk_match.group(2)
            print(f"🏢 KVK nummer detected and remembered: {self.current_kvk}")

        # Add context if BSN/KVK available but not mentioned
        context_additions = []
        if self.current_bsn and "BSN" not in user_message.upper():
            context_additions.append(f"BSN: {self.current_bsn}")
        if self.current_kvk and "KVK" not in user_message.upper():
            context_additions.append(f"KVK_NUMMER: {self.current_kvk}")

        if context_additions:
            user_message += f" (Context: {', '.join(context_additions)})"

        try:
            print("🧠 Processing with LangGraph agent...")

            # Run the agent
            response = await self.agent.ainvoke({"messages": [{"role": "user", "content": user_message}]})

            # Extract the final response
            if response and "messages" in response:
                last_message = response["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    return last_message["content"]

            return str(response)

        except Exception as e:
            error_msg = f"Fout bij het verwerken van je vraag: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    async def start_chat(self):
        """Start interactive chat session"""
        print("\n" + "=" * 80)
        print("🏛️  Nederlandse Wetgeving Chat - Official LangChain MCP Integration")
        print("=" * 80)
        print("\n🎯 Officiële implementatie met:")
        print("   • langchain-mcp-adapters (officiele LangChain MCP support)")
        print("   • LangGraph ReAct agent")
        print("   • Streamable HTTP MCP transport")
        print("   • Claude 3.5 Sonnet")

        print("\n📝 Probeer deze vragen:")
        print("• 'Mijn BSN is 100000001. Heb ik recht op zorgtoeslag?'")
        print("• 'Hoeveel zorgtoeslag krijg ik precies per maand?'")
        print("• 'Wat als mijn inkomen €35.000 wordt?'")
        print("• 'Kan ik ook huurtoeslag krijgen? En hoeveel?'")
        print("• 'Mijn bedrijf heeft KVK 58372941. Wat kan ik krijgen?'")

        print("\n💡 Je ziet de volledige LangGraph ReAct reasoning")
        print("Type 'quit' om te stoppen\n")
        print("-" * 80 + "\n")

        while True:
            try:
                user_input = input("👤 Jij: ").strip()

                if user_input.lower() in ["quit", "exit", "stop", "q"]:
                    print("\n👋 Chat beëindigd!")
                    break

                if not user_input:
                    continue

                print("\n🤖 LangGraph Agent aan het werk...")
                print("-" * 50)

                response = await self.process_message(user_input)

                print("-" * 50)
                print(f"📝 Antwoord: {response}")
                print("\n" + "=" * 80 + "\n")

            except KeyboardInterrupt:
                print("\n\n👋 Chat beëindigd!")
                break
            except Exception as e:
                print(f"\n❌ Onverwachte fout: {e}")

    async def cleanup(self):
        """Cleanup MCP client"""
        if self.mcp_client:
            try:
                # Check if client has close method
                if hasattr(self.mcp_client, "aclose"):
                    await self.mcp_client.aclose()
                elif hasattr(self.mcp_client, "close"):
                    await self.mcp_client.close()
                # If no close method, client is likely stateless
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")


async def main():
    """Main function"""
    print("🚀 Starting Official LangChain MCP Integration...")
    print("=" * 60)

    # Check prerequisites
    print("🔍 Checking prerequisites...")

    # Check MCP server
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get("http://localhost:8000/", timeout=aiohttp.ClientTimeout(total=5)) as response,
        ):
            if response.status != 200:
                print(f"❌ MCP server error: {response.status}")
                print("💡 Start the web server first:")
                print("   uv run web/main.py")
                return
        print("✅ MCP server is running")
    except Exception as e:
        print("❌ Cannot connect to MCP server")
        print("💡 Start the web server first:")
        print("   uv run web/main.py")
        print(f"   (Error: {e})")
        return

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("✅ Anthropic API key found")
    else:
        print("⚠️  Anthropic API key not in environment")

    print("=" * 60)

    # Create and initialize chat
    chat = OfficialLangChainMCP()

    try:
        if not await chat.initialize():
            print("❌ Failed to initialize MCP integration")
            return

        await chat.start_chat()

    finally:
        await chat.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
