#!/usr/bin/env python3
"""
Live demonstration of MCP server interactions showing real law execution
"""

import asyncio
import json

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def demonstrate_mcp_server():
    """Demonstrate the MCP server with real law execution scenarios"""

    print("🏛️  Machine Law MCP Server - Live Demonstration")
    print("=" * 60)

    # Start the MCP server
    server_params = StdioServerParameters(command="uv", args=["run", "python", "-m", "law_mcp.server"])

    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        # Initialize the session
        await session.initialize()
        print("✅ Connected to MCP server")

        # Scenario 1: Discover available tools and resources
        print("\n📋 SCENARIO 1: Discovering Available Capabilities")
        print("-" * 50)

        tools = await session.list_tools()
        print(f"Available tools ({len(tools.tools)}):")
        for tool in tools.tools:
            print(f"  🔧 {tool.name}: {tool.description}")

        resources = await session.list_resources()
        print(f"\nAvailable resources ({len(resources.resources)}):")
        for resource in resources.resources:
            print(f"  📄 {resource.uri}: {resource.name}")

        prompts = await session.list_prompts()
        print(f"\nAvailable prompts ({len(prompts.prompts)}):")
        for prompt in prompts.prompts:
            print(f"  💬 {prompt.name}: {prompt.description}")

        # Scenario 2: Check what laws are available
        print("\n📚 SCENARIO 2: Discovering Available Laws")
        print("-" * 50)

        laws_result = await session.read_resource("laws://list")
        laws_data = json.loads(laws_result.contents[0].text)
        print(f"Found {laws_data['total_count']} available laws:")

        for law in laws_data["available_laws"][:5]:  # Show first 5
            service = law["service"]
            law_name = law["law"]
            description = law.get("description", "No description")
            print(f"  ⚖️  {service}.{law_name}")
            print(f"      {description}")

        # Scenario 3: Get detailed law specification
        print("\n🔍 SCENARIO 3: Understanding a Specific Law")
        print("-" * 50)

        spec_result = await session.read_resource("law://TOESLAGEN/zorgtoeslagwet/spec")
        spec_data = json.loads(spec_result.contents[0].text)

        print("Zorgtoeslag Law Specification:")
        print(f"  📝 Name: {spec_data.get('name', 'N/A')}")
        print(f"  🆔 UUID: {spec_data.get('uuid', 'N/A')}")
        print(f"  📅 Valid from: {spec_data.get('valid_from', 'N/A')}")
        print(f"  📖 Description: {spec_data.get('description', 'N/A')[:100]}...")

        if spec_data.get("parameters"):
            print("  📥 Required parameters:")
            for param in spec_data["parameters"][:3]:
                print(f"      • {param.get('name', 'N/A')}: {param.get('description', 'N/A')}")

        if spec_data.get("outputs"):
            print("  📤 Possible outputs:")
            for output in spec_data["outputs"][:3]:
                print(f"      • {output.get('name', 'N/A')}: {output.get('description', 'N/A')}")

        # Scenario 4: Get citizen profile data
        print("\n👤 SCENARIO 4: Looking Up Citizen Profile")
        print("-" * 50)

        profile_result = await session.read_resource("profile://100000001")
        profile_data = json.loads(profile_result.contents[0].text)

        print("Citizen Profile (BSN: 100000001):")
        citizen_data = profile_data.get("data", {})
        if citizen_data:
            print(f"  🎂 Birth date: {citizen_data.get('geboortedatum', 'N/A')}")
            print(f"  📍 Postal code: {citizen_data.get('postcode', 'N/A')}")
            print(f"  🏠 Household type: {citizen_data.get('huishouding', 'N/A')}")
            print(f"  💰 Annual income: €{citizen_data.get('inkomen', 0):,}")
            print(f"  🛡️  Insured: {citizen_data.get('verzekerd', 'N/A')}")
        else:
            print(f"  ⚠️  No profile data found for BSN: 100000001")

        # Scenario 5: Check eligibility for specific benefit
        print("\n✅ SCENARIO 5: Checking Eligibility for Zorgtoeslag")
        print("-" * 50)

        eligibility_result = await session.call_tool(
            "check_eligibility", {"parameters": {"BSN": "100000001"}, "service": "TOESLAGEN", "law": "zorgtoeslagwet"}
        )
        eligibility_data = json.loads(eligibility_result.content[0].text)

        if eligibility_data.get("success"):
            eligible = eligibility_data["data"]["eligible"]
            status = "✅ ELIGIBLE" if eligible else "❌ NOT ELIGIBLE"
            print(f"Zorgtoeslag eligibility: {status}")
            print(f"Reference date: {eligibility_data['data']['reference_date']}")

        # Scenario 6: Execute full law calculation
        print("\n⚖️  SCENARIO 6: Full Law Execution with Details")
        print("-" * 50)

        execution_result = await session.call_tool(
            "execute_law",
            {
                "parameters": {"BSN": "100000001"},
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "reference_date": "2024-01-01",
            },
        )
        execution_data = json.loads(execution_result.content[0].text)

        if execution_data.get("success"):
            data = execution_data["data"]
            print("Law execution completed:")
            print(f"  🎯 Requirements met: {data['requirements_met']}")
            print(f"  📊 Rule spec UUID: {data['rulespec_uuid']}")

            outputs = data.get("output", {})
            print("  📤 Calculation results:")
            for key, value in outputs.items():
                if isinstance(value, int | float) and "hoogte" in key.lower():
                    # Convert cents to euros for display
                    euro_value = value / 100 if isinstance(value, int | float) else value
                    print(f"      💰 {key}: €{euro_value:.2f}")
                else:
                    print(f"      📋 {key}: {value}")

            if data.get("missing_required"):
                print(f"  ⚠️  Missing required data: {data['missing_required']}")

        # Scenario 7: Calculate specific benefit amount
        print("\n💵 SCENARIO 7: Calculating Specific Benefit Amount")
        print("-" * 50)

        benefit_result = await session.call_tool(
            "calculate_benefit_amount",
            {
                "parameters": {"BSN": "100000001"},
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "output_field": "hoogte_toeslag",
            },
        )
        benefit_data = json.loads(benefit_result.content[0].text)

        if benefit_data.get("success"):
            amount = benefit_data["data"]["amount"]
            formatted_amount = benefit_data["data"].get("formatted_amount")
            print(f"Zorgtoeslag monthly amount: {formatted_amount or f'€{amount:.2f}' if amount else 'Not available'}")

        # Scenario 8: Testing WPM law with KvK nummer (Business law)
        print("\n🏢 SCENARIO 8: Testing WPM Business Law")
        print("-" * 50)

        try:
            wpm_result = await session.call_tool(
                "check_eligibility", {"parameters": {"KVK_NUMMER": "58372941"}, "service": "RVO", "law": "omgevingswet/werkgebonden_personenmobiliteit"}
            )
            wpm_data = json.loads(wpm_result.content[0].text)

            print("WPM law execution test:")
            if wpm_data.get("success"):
                eligible = wpm_data["data"]["eligible"]
                status = "✅ ELIGIBLE" if eligible else "❌ NOT ELIGIBLE"
                print(f"  WPM eligibility for KvK 58372941: {status}")
            else:
                print(f"  ❌ WPM test failed: {wpm_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  ⚠️  WPM test error: {str(e)}")

        # Scenario 9: Using prompts for guided analysis
        print("\n💬 SCENARIO 9: Generating Guided Analysis Prompt")
        print("-" * 50)

        prompt_result = await session.get_prompt("check_all_benefits", {"bsn": "100000001", "include_details": "true"})

        print("Generated prompt for comprehensive benefit analysis:")
        print(f"  📝 Description: {prompt_result.description}")
        print("  📄 Prompt content preview:")
        prompt_text = prompt_result.messages[0].content.text
        preview = prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
        for line in preview.split("\n")[:5]:
            if line.strip():
                print(f"      {line}")

        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("The MCP server is fully operational and ready for Claude Desktop integration.")
        print("\nKey capabilities demonstrated:")
        print("  ✅ Law discovery and specification lookup")
        print("  ✅ Citizen profile data access")
        print("  ✅ Eligibility checking")
        print("  ✅ Full law execution with detailed results")
        print("  ✅ Benefit amount calculations")
        print("  ✅ Guided prompt generation")
        print("\nNext steps:")
        print("  🔗 Configure Claude Desktop to connect to this MCP server")
        print("  💬 Start conversations that leverage these law execution capabilities")


if __name__ == "__main__":
    asyncio.run(demonstrate_mcp_server())
