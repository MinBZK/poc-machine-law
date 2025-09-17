import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse

# Import our components
from web.dependencies import get_machine_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPConnectionManager:
    """Manages active MCP connections for HTTP/SSE transport"""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """Create a new MCP session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "created_at": asyncio.get_event_loop().time(),
        }
        return session_id

    def get_session(self, session_id: str) -> Dict[str, Any] | None:
        """Get an existing session"""
        return self.active_sessions.get(session_id)

    def cleanup_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# Global connection manager
manager = MCPConnectionManager()


@router.get("/health")
async def health_check():
    """Health check endpoint for MCP server"""
    return {
        "status": "healthy",
        "transport": "http+sse",
        "active_sessions": len(manager.active_sessions),
        "capabilities": {
            "tools": ["execute_law", "check_eligibility", "calculate_benefit_amount"],
            "resources": ["laws://list", "law://{service}/{law}/spec", "profile://{bsn}"],
            "prompts": ["check_all_benefits", "explain_calculation", "compare_scenarios"],
        },
    }


@router.post("/rpc")
async def handle_rpc(request: Request):
    """Handle JSON-RPC calls to MCP server"""
    try:
        # Parse JSON-RPC request
        data = await request.json()
        method = data.get("method", "")
        params = data.get("params", {})
        request_id = data.get("id")

        # Get machine service using web dependency
        machine_service = get_machine_service()

        # Handle different MCP methods
        if method == "tools/list":
            result = await list_tools()
        elif method == "tools/call":
            result = await call_tool(machine_service, params)
        elif method == "resources/list":
            result = await list_resources(machine_service)
        elif method == "resources/read":
            result = await read_resource(machine_service, params)
        elif method == "prompts/list":
            result = await list_prompts()
        elif method == "prompts/get":
            result = await get_prompt(params)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id,
            }

        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    except Exception as e:
        logger.error(f"Error handling RPC request: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": data.get("id") if "data" in locals() else None,
        }


@router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """SSE endpoint for MCP communication (future enhancement)"""

    async def event_generator():
        session_id = manager.create_session()

        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps(
                    {
                        "session_id": session_id,
                        "capabilities": {
                            "tools": ["execute_law", "check_eligibility", "calculate_benefit_amount"],
                            "resources": ["laws://list", "law://{service}/{law}/spec", "profile://{bsn}"],
                            "prompts": ["check_all_benefits", "explain_calculation", "compare_scenarios"],
                        },
                    }
                ),
            }

            # Keep connection alive (for future streaming capabilities)
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                yield {"event": "heartbeat", "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})}

        except asyncio.CancelledError:
            pass
        finally:
            manager.cleanup_session(session_id)

    return EventSourceResponse(event_generator())


# Tool handlers
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "execute_law",
                "description": "Execute a Dutch law for a specific citizen with optional parameter overrides",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bsn": {"type": "string", "description": "BSN van de persoon"},
                        "service": {"type": "string", "description": "Service provider code"},
                        "law": {"type": "string", "description": "Law identifier"},
                        "reference_date": {"type": "string", "description": "Reference date (YYYY-MM-DD)"},
                        "parameters": {"type": "object", "description": "Additional parameters"},
                    },
                    "required": ["bsn", "service", "law"],
                },
            },
            {
                "name": "check_eligibility",
                "description": "Check if a citizen is eligible for a specific benefit or law",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bsn": {"type": "string", "description": "BSN van de persoon"},
                        "service": {"type": "string", "description": "Service provider code"},
                        "law": {"type": "string", "description": "Law identifier"},
                        "reference_date": {"type": "string", "description": "Reference date (YYYY-MM-DD)"},
                    },
                    "required": ["bsn", "service", "law"],
                },
            },
            {
                "name": "calculate_benefit_amount",
                "description": "Calculate a specific benefit amount for a citizen",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bsn": {"type": "string", "description": "BSN van de persoon"},
                        "service": {"type": "string", "description": "Service provider code"},
                        "law": {"type": "string", "description": "Law identifier"},
                        "output_field": {"type": "string", "description": "Output field to calculate"},
                        "reference_date": {"type": "string", "description": "Reference date (YYYY-MM-DD)"},
                    },
                    "required": ["bsn", "service", "law", "output_field"],
                },
            },
        ]
    }


async def call_tool(machine_service, params: Dict[str, Any]):
    """Execute a tool call"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "execute_law":
            # Use machine service to execute law
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters={"BSN": arguments["bsn"]},
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
            )
            return {"content": [{"type": "text", "text": json.dumps(result.__dict__, indent=2, default=str)}]}

        elif tool_name == "check_eligibility":
            # Check eligibility using machine service
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters={"BSN": arguments["bsn"]},
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
            )
            # Check if requirements are met
            eligible = result.requirements_met
            return {"content": [{"type": "text", "text": f"Eligible: {eligible}"}]}

        elif tool_name == "calculate_benefit_amount":
            # Calculate benefit amount using machine service
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters={"BSN": arguments["bsn"]},
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
                requested_output=arguments["output_field"],
            )
            # Extract the requested output field
            output_field = arguments["output_field"]
            amount = result.output.get(output_field, "Not available")
            return {"content": [{"type": "text", "text": f"Amount: {amount}"}]}

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}


async def list_resources(machine_service):
    """List available MCP resources"""
    return {
        "resources": [
            {
                "uri": "laws://list",
                "name": "Available Laws",
                "description": "List of all available laws and regulations",
                "mimeType": "application/json",
            },
            {
                "uri": "law://{service}/{law}/spec",
                "name": "Law Specification",
                "description": "Detailed specification for a specific law",
                "mimeType": "application/json",
            },
            {
                "uri": "profile://{bsn}",
                "name": "Citizen Profile",
                "description": "Profile data for a specific citizen",
                "mimeType": "application/json",
            },
        ]
    }


async def read_resource(machine_service, params: Dict[str, Any]):
    """Read a specific resource"""
    uri = params.get("uri", "")

    try:
        if uri == "laws://list":
            # Get available laws from machine service
            laws = machine_service.get_sorted_discoverable_service_laws("123456782")
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(laws, indent=2)}]}
        elif uri.startswith("law://"):
            # Parse law://{service}/{law}/spec
            parts = uri.replace("law://", "").split("/")
            if len(parts) >= 3:
                service, law = parts[0], parts[1]
                # Get basic law info - this is a simplified implementation
                spec = {"service": service, "law": law, "description": f"Specification for {service}.{law}"}
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(spec, indent=2)}]}
        elif uri.startswith("profile://"):
            # Parse profile://{bsn}
            bsn = uri.replace("profile://", "")
            profile = machine_service.get_profile_data(bsn)
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(profile, indent=2)}]}
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except Exception as e:
        return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error: {str(e)}"}]}


async def list_prompts():
    """List available MCP prompts"""
    return {
        "prompts": [
            {
                "name": "check_all_benefits",
                "description": "Check all benefits for BSN 123456782",
                "arguments": [{"name": "bsn", "description": "BSN van de persoon", "required": True}],
            },
            {
                "name": "explain_calculation",
                "description": "Explain calculation",
                "arguments": [
                    {"name": "service", "description": "Service provider code", "required": True},
                    {"name": "law", "description": "Law identifier", "required": True},
                ],
            },
            {
                "name": "compare_scenarios",
                "description": "Compare scenarios",
                "arguments": [
                    {"name": "scenarios", "description": "List of scenarios to compare (JSON)", "required": True}
                ],
            },
        ]
    }


async def get_prompt(params: Dict[str, Any]):
    """Get a specific prompt"""
    name = params.get("name")
    arguments = params.get("arguments", {})

    # This would integrate with the existing prompt system from law_mcp/prompt_templates.py
    # For now, return a simple response
    return {
        "description": f"Generated prompt for {name}",
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": f"Execute {name} with arguments: {json.dumps(arguments)}"},
            }
        ],
    }
