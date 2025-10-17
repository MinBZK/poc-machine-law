#!/usr/bin/env python3
"""
Optimized MCP Server for Machine Law Execution - DRY and Elegant Implementation

This is a clean, DRY implementation that eliminates code duplication
and provides elegant abstractions for MCP protocol handling.
"""

import asyncio
import json
import logging
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import Prompt, Resource, TextContent, Tool

from law_mcp.config import get_config, setup_logging
from law_mcp.engine_adapter import LawEngineAdapter
from law_mcp.prompt_templates import PROMPT_TEMPLATES
from law_mcp.response_handler import (
    format_benefit_response,
    format_eligibility_response,
    format_execution_response,
    handle_tool_with_error_handling,
)
from law_mcp.schemas import TOOL_SCHEMAS

# Setup
config = get_config()
setup_logging(config.logging)
logger = logging.getLogger(__name__)
server = Server("machine-law-executor")

# Initialize engine
try:
    law_engine = LawEngineAdapter()
    logger.info("MCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize law engine: {e}")
    raise


# =============================================================================
# TOOLS - Elegant tool handling with DRY principles
# =============================================================================


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools using schema definitions"""
    return [Tool(**schema) for schema in TOOL_SCHEMAS.values()]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Unified tool handler with clean delegation"""

    # Tool handler mapping - clean and extensible
    handlers = {
        "execute_law": lambda: _handle_execute_law(arguments),
        "check_eligibility": lambda: _handle_check_eligibility(arguments),
        "calculate_benefit_amount": lambda: _handle_calculate_benefit_amount(arguments),
        "get_available_roles": lambda: _handle_get_available_roles(arguments),
        "select_role": lambda: _handle_select_role(arguments),
    }

    handler = handlers.get(name)
    if not handler:
        return handle_tool_with_error_handling(name, lambda: {"error": f"Unknown tool: {name}"})

    return await handle_tool_with_error_handling(name, handler)


async def _handle_execute_law(args: dict[str, Any]) -> dict[str, Any]:
    """Handle law execution with clean parameter extraction"""
    result = await law_engine.execute_law(
        service=args["service"],
        law=args["law"],
        parameters=args["parameters"],
        reference_date=args.get("reference_date"),
        overrides=args.get("overrides"),
        requested_output=args.get("requested_output"),
        approved=args.get("approved", False),
    )
    return format_execution_response(result, args)


async def _handle_check_eligibility(args: dict[str, Any]) -> dict[str, Any]:
    """Handle eligibility checking"""
    eligible = await law_engine.check_eligibility(
        service=args["service"],
        law=args["law"],
        parameters=args["parameters"],
        reference_date=args.get("reference_date"),
    )
    return format_eligibility_response(eligible, args)


async def _handle_calculate_benefit_amount(args: dict[str, Any]) -> dict[str, Any]:
    """Handle benefit amount calculation"""
    amount = await law_engine.calculate_benefit_amount(
        service=args["service"],
        law=args["law"],
        parameters=args["parameters"],
        output_field=args["output_field"],
        reference_date=args.get("reference_date"),
    )
    return format_benefit_response(amount, args)


async def _handle_get_available_roles(args: dict[str, Any]) -> dict[str, Any]:
    """Handle getting available roles for an actor"""
    from machine.authorization import AuthorizationService

    auth_service = AuthorizationService(law_engine.services)
    roles = auth_service.get_available_roles(
        actor_bsn=args["actor_bsn"], reference_date=args.get("reference_date")
    )

    return {
        "actor_bsn": args["actor_bsn"],
        "roles": [
            {
                "type": role.type,
                "id": role.id,
                "name": role.name,
                "legal_ground": role.legal_ground,
                "legal_basis": role.legal_basis,
                "scope": role.scope,
                "restrictions": role.restrictions,
            }
            for role in roles
        ],
    }


async def _handle_select_role(args: dict[str, Any]) -> dict[str, Any]:
    """Handle selecting a role"""
    from machine.authorization import AuthorizationService

    auth_service = AuthorizationService(law_engine.services)

    # Handle SELF selection
    if args["target_type"] == "SELF":
        return {
            "status": "ok",
            "message": "Acting as self",
            "acting_as": None,
        }

    # Verify authorization
    is_authorized, legal_ground = auth_service.verify_authorization(
        actor_bsn=args["actor_bsn"],
        target_type=args["target_type"],
        target_id=args["target_id"],
        action=args.get("action"),
        reference_date=args.get("reference_date"),
    )

    if not is_authorized:
        return {"error": f"Not authorized to act on behalf of {args['target_type']} {args['target_id']}"}

    return {
        "status": "ok",
        "message": f"Now acting as {args['target_type']} {args['target_id']}",
        "acting_as": {
            "type": args["target_type"],
            "id": args["target_id"],
            "legal_ground": legal_ground,
            "action": args.get("action"),
        },
    }


# =============================================================================
# RESOURCES - Clean resource handling
# =============================================================================

# Resource definitions - declarative and DRY
RESOURCES = [
    Resource(
        uri="laws://list",
        name="Available Laws",
        description="List all available laws in the system",
        mimeType="application/json",
    ),
    Resource(
        uri="law://{service}/{law}/spec",
        name="Law Specification",
        description="Get the specification for a specific law",
        mimeType="application/json",
    ),
    Resource(
        uri="profile://{bsn}",
        name="Citizen Profile",
        description="Get profile data for a specific citizen",
        mimeType="application/json",
    ),
]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources"""
    return RESOURCES


@server.read_resource()
async def handle_read_resource(uri) -> str:
    """Unified resource handler with clean delegation"""
    uri_str = str(uri)

    # Resource handler mapping
    handlers = {"laws://list": _handle_laws_list, "law://": _handle_law_spec, "profile://": _handle_profile}

    try:
        # Find matching handler
        for prefix, handler in handlers.items():
            if uri_str.startswith(prefix):
                return await handler(uri_str)

        # No handler found
        return json.dumps({"error": f"Unknown resource: {uri_str}"}, indent=2)

    except Exception as e:
        logger.error(f"Resource {uri_str} failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


async def _handle_laws_list(uri: str) -> str:
    """Handle laws list resource"""
    laws = law_engine.get_available_laws()
    result = {
        "available_laws": [
            {
                "service": law.service,
                "law": law.law,
                "name": law.name,
                "description": law.description,
                "discoverable": law.discoverable,
            }
            for law in laws
        ],
        "total_count": len(laws),
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


async def _handle_law_spec(uri: str) -> str:
    """Handle law specification resource"""
    # Parse URI like law://TOESLAGEN/zorgtoeslagwet/spec
    parts = uri.replace("law://", "").replace("/spec", "").split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid law spec URI format: {uri}")

    service, law = parts
    spec = law_engine.get_law_specification(service, law)
    result = {
        "uuid": spec.uuid,
        "name": spec.name,
        "law": spec.law,
        "service": spec.service,
        "description": spec.description,
        "valid_from": spec.valid_from,
        "references": spec.references,
        "parameters": spec.parameters,
        "outputs": spec.outputs,
    }
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


async def _handle_profile(uri: str) -> str:
    """Handle citizen profile resource"""
    # Parse URI like profile://123456782
    bsn = uri.replace("profile://", "")
    profile = law_engine.get_profile_data(bsn)
    result = {
        "bsn": profile.bsn,
        "data": profile.data,
        "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


# =============================================================================
# PROMPTS - Template-based prompt system
# =============================================================================


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """List available prompts from template registry"""
    return [
        Prompt(name=template.name, description=template.description, arguments=_get_prompt_arguments(name))
        for name, template in PROMPT_TEMPLATES.items()
    ]


def _get_prompt_arguments(prompt_name: str) -> list[dict[str, Any]]:
    """Get arguments schema for each prompt type"""
    base_args = [{"name": "bsn", "description": "Dutch citizen identifier (BSN)", "required": True}]

    prompt_specific_args = {
        "check_all_benefits": [
            {"name": "include_details", "description": "Include detailed calculation explanations", "required": False}
        ],
        "explain_calculation": [
            {"name": "service", "description": "Service provider code", "required": True},
            {"name": "law", "description": "Law identifier", "required": True},
        ],
        "compare_scenarios": [
            {"name": "scenarios", "description": "List of scenarios to compare (JSON)", "required": True}
        ],
    }

    return base_args + prompt_specific_args.get(prompt_name, [])


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str]):
    """Generate prompts using template system"""
    template = PROMPT_TEMPLATES.get(name)
    if not template:
        raise ValueError(f"Unknown prompt: {name}")

    return template.generate(arguments)


# =============================================================================
# SERVER STARTUP
# =============================================================================


async def main():
    """Main server entry point"""
    logger.info("Starting Machine Law MCP Server...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
