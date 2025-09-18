#!/usr/bin/env python3
"""
Test all MCP tools to verify path and rule_spec information
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from fastmcp.client import Client


async def test_all_mcp_tools():
    """Test all three MCP tools for path and rule_spec information"""
    print("🧪 Testing All MCP Tools...")

    client = Client("http://localhost:8000/mcp/")

    try:
        await client.__aenter__()
        print("✅ Connected to MCP server")

        # Test 1: execute_law
        print("\n🔧 Testing execute_law tool...")
        result1 = await client.call_tool(
            "execute_law",
            arguments={
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000001"},
                "reference_date": "2025-01-01"
            }
        )

        structured1 = result1.structured_content
        if structured1 and 'path' in structured1 and 'rule_spec' in structured1:
            print(f"   ✅ execute_law: path={structured1['path'] is not None}, rule_spec={structured1['rule_spec'] is not None}")
        else:
            print(f"   ❌ execute_law: Missing path or rule_spec")

        # Test 2: check_eligibility
        print("\n🔧 Testing check_eligibility tool...")
        result2 = await client.call_tool(
            "check_eligibility",
            arguments={
                "service": "TOESLAGEN",
                "law": "wet_op_de_huurtoeslag",
                "parameters": {"BSN": "100000002"}
            }
        )

        structured2 = result2.structured_content
        if structured2 and 'path' in structured2 and 'rule_spec' in structured2:
            print(f"   ✅ check_eligibility: path={structured2['path'] is not None}, rule_spec={structured2['rule_spec'] is not None}")
            if structured2['path']:
                print(f"   📊 Path root type: {structured2['path'].get('type', 'N/A')}")
        else:
            print(f"   ❌ check_eligibility: Missing path or rule_spec")

        # Test 3: calculate_benefit_amount
        print("\n🔧 Testing calculate_benefit_amount tool...")
        result3 = await client.call_tool(
            "calculate_benefit_amount",
            arguments={
                "service": "TOESLAGEN",
                "law": "zorgtoeslagwet",
                "parameters": {"BSN": "100000003"},
                "output_field": "hoogte_toeslag"
            }
        )

        structured3 = result3.structured_content
        if structured3 and 'path' in structured3 and 'rule_spec' in structured3:
            print(f"   ✅ calculate_benefit_amount: path={structured3['path'] is not None}, rule_spec={structured3['rule_spec'] is not None}")
            if structured3['rule_spec']:
                print(f"   📋 Rule name: {structured3['rule_spec'].get('name', 'N/A')}")
        else:
            print(f"   ❌ calculate_benefit_amount: Missing path or rule_spec")

        # Summary
        print(f"\n📊 Summary:")
        results = [
            ("execute_law", structured1 and 'path' in structured1 and 'rule_spec' in structured1),
            ("check_eligibility", structured2 and 'path' in structured2 and 'rule_spec' in structured2),
            ("calculate_benefit_amount", structured3 and 'path' in structured3 and 'rule_spec' in structured3)
        ]

        for tool_name, has_data in results:
            status = "✅" if has_data else "❌"
            print(f"   {status} {tool_name}: path & rule_spec included")

        all_working = all(result[1] for result in results)
        print(f"\n🎯 All tools working: {'✅ YES' if all_working else '❌ NO'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_all_mcp_tools())