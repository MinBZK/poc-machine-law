"""
Response handling utilities for MCP server - DRY principle applied
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.types import TextContent

from law_mcp.utils import format_currency, get_current_date

logger = logging.getLogger(__name__)


def create_success_response(data: dict[str, Any]) -> dict[str, Any]:
    """Create a standardized success response"""
    return {"success": True, "data": data}


def create_error_response(error: str, error_type: str = None) -> dict[str, Any]:
    """Create a standardized error response"""
    response = {"success": False, "error": str(error)}
    if error_type:
        response["error_type"] = error_type
    return response


def serialize_response(response: dict[str, Any]) -> list[TextContent]:
    """Serialize response to TextContent with proper JSON handling"""
    return [TextContent(type="text", text=json.dumps(response, indent=2, ensure_ascii=False, default=str))]


async def handle_tool_with_error_handling(
    tool_name: str, handler: Callable[[], Awaitable[dict[str, Any]]]
) -> list[TextContent]:
    """Generic tool handler with standardized error handling"""
    try:
        result = await handler()
        return serialize_response(create_success_response(result))
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        error_response = create_error_response(str(e), type(e).__name__)
        return serialize_response(error_response)


def add_common_metadata(data: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    """Add common metadata fields to response data"""
    metadata = {
        "bsn": arguments.get("bsn"),
        "service": arguments.get("service"),
        "law": arguments.get("law"),
        "reference_date": arguments.get("reference_date") or get_current_date(),
    }

    # Add metadata first, then data (so data can override if needed)
    return {**metadata, **data}


def format_benefit_response(amount: float | None, arguments: dict[str, Any]) -> dict[str, Any]:
    """Format benefit calculation response with common fields"""
    data = {
        "output_field": arguments["output_field"],
        "amount": amount,
        "formatted_amount": format_currency(amount) if amount is not None else None,
    }
    return add_common_metadata(data, arguments)


def format_eligibility_response(eligible: bool, arguments: dict[str, Any]) -> dict[str, Any]:
    """Format eligibility check response with common fields"""
    return add_common_metadata({"eligible": eligible}, arguments)


def format_execution_response(result, arguments: dict[str, Any]) -> dict[str, Any]:
    """Format law execution response with all fields"""
    data = {
        "output": result.output,
        "requirements_met": result.requirements_met,
        "missing_required": result.missing_required,
        "input_data": result.input_data,
        "rulespec_uuid": result.rulespec_uuid,
        "execution_path": result.execution_path,
    }
    return add_common_metadata(data, arguments)
