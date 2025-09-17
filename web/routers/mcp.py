import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, Response
from sse_starlette import EventSourceResponse

from law_mcp.prompt_templates import PROMPT_TEMPLATES
from law_mcp.schemas import TOOL_SCHEMAS

# Import our components
from web.dependencies import get_machine_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPConnectionManager:
    """Manages active MCP connections for HTTP/SSE transport"""

    def __init__(self):
        self.active_sessions: dict[str, dict[str, Any]] = {}

    def create_session(self) -> str:
        """Create a new MCP session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "created_at": asyncio.get_event_loop().time(),
        }
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
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
            "prompts": list(PROMPT_TEMPLATES.keys()),
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


@router.post("/")
@router.get("/")
async def mcp_streamable_endpoint(request: Request):
    """MCP Streamable HTTP endpoint (2025 specification)."""

    # Security: Validate Origin header to prevent DNS rebinding attacks
    origin = request.headers.get("origin")
    if origin and not origin.startswith(("http://localhost", "http://127.0.0.1", "https://localhost")):
        return {"error": "Invalid origin", "status": 403}

    # Check Accept header
    accept_header = request.headers.get("accept", "")
    wants_sse = "text/event-stream" in accept_header
    wants_json = "application/json" in accept_header

    if request.method == "GET":
        # GET method: Open SSE stream for server-to-client messages
        if not wants_sse:
            return {"error": "GET requires Accept: text/event-stream", "status": 400}

        async def event_generator():
            session_id = manager.create_session()

            try:
                # Keep connection alive - MCP client will send POST requests
                # This stream is for server-initiated messages only
                while True:
                    # Check if request was disconnected
                    if await request.is_disconnected():
                        break
                    await asyncio.sleep(60)  # Keep connection alive

            except asyncio.CancelledError:
                pass
            finally:
                manager.cleanup_session(session_id)

        return EventSourceResponse(event_generator())

    elif request.method == "POST":
        # POST method: Handle JSON-RPC messages
        try:
            data = await request.json()
            machine_service = get_machine_service()

            # Handle both single messages and batched messages
            if isinstance(data, list):
                # Batch request
                results = []
                for msg in data:
                    result = await handle_jsonrpc_message(msg, machine_service)
                    if result:  # Only add non-None results (notifications return None)
                        results.append(result)

                # Return SSE stream if client accepts it, otherwise JSON
                if wants_sse and not wants_json:
                    return await stream_batch_responses(results)
                else:
                    return results if results else Response(status_code=202)
            else:
                # Single request
                result = await handle_jsonrpc_message(data, machine_service)

                # Return SSE stream if client accepts it, otherwise JSON
                if wants_sse and not wants_json:
                    return await stream_single_response(result)
                else:
                    return result if result else Response(status_code=202)

        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": data.get("id") if "data" in locals() else None,
            }

            if wants_sse and not wants_json:
                return await stream_single_response(error_response)
            else:
                return error_response


async def handle_jsonrpc_message(data: dict, machine_service) -> dict | None:
    """Handle a single JSON-RPC message."""
    method = data.get("method")
    params = data.get("params", {})
    request_id = data.get("id")

    # Notifications don't have an id and don't expect a response
    is_notification = request_id is None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                    "logging": {},
                    "experimental": {},
                },
                "serverInfo": {"name": "machine-law-executor", "version": "0.1.0"},
            }
        elif method == "tools/list":
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
            if is_notification:
                return None  # Unknown notifications are ignored
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id,
            }

        # Don't send response for notifications
        if is_notification:
            return None

        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    except Exception as e:
        logger.error(f"Error handling method {method}: {e}")
        if is_notification:
            return None
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": request_id,
        }


async def stream_single_response(response: dict | None):
    """Stream a single response via SSE."""
    if response is None:
        return Response(status_code=202)  # No content for notifications

    async def event_generator():
        yield {"id": "1", "event": "message", "data": json.dumps(response)}

    return EventSourceResponse(event_generator())


async def stream_batch_responses(responses: list[dict]):
    """Stream batch responses via SSE."""
    if not responses:
        return Response(status_code=202)

    async def event_generator():
        for i, response in enumerate(responses, 1):
            yield {"id": str(i), "event": "message", "data": json.dumps(response)}

    return EventSourceResponse(event_generator())


@router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """Legacy SSE endpoint for backwards compatibility"""

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
                            "prompts": list(PROMPT_TEMPLATES.keys()),
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
    return {"tools": list(TOOL_SCHEMAS.values())}


async def call_tool(machine_service, params: dict[str, Any]):
    """Execute a tool call"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "execute_law":
            # Use machine service to execute law
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
            )
            # Return the result as JSON text (MCP standard)
            import json

            result_data = {
                "success": True,
                "data": {
                    "output": result.output,
                    "requirements_met": result.requirements_met,
                    "input": result.input,
                    "rulespec_uuid": result.rulespec_uuid,
                    "missing_required": result.missing_required,
                },
            }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_data, indent=2),
                    }
                ]
            }

        elif tool_name == "check_eligibility":
            # Check eligibility using machine service
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
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
                parameters=arguments["parameters"],
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
        logger.error(f"Tool call failed: {e}")
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


async def read_resource(machine_service, params: dict[str, Any]):
    """Read a specific resource"""
    uri = params.get("uri", "")

    try:
        if uri == "laws://list":
            # Get available laws from machine service - include both citizen and business laws
            available_laws = []

            # Get citizen laws
            try:
                citizen_laws = machine_service.get_discoverable_service_laws("CITIZEN")
                for service, law_list in citizen_laws.items():
                    for law in law_list:
                        available_laws.append(
                            {
                                "service": service,
                                "law": law,
                                "discoverable": True,
                                "name": law.replace("_", " ").title(),
                                "description": f"Citizen law {law} managed by {service}",
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not get citizen laws: {e}")

            # Get business laws
            try:
                business_laws = machine_service.get_discoverable_service_laws("BUSINESS")
                for service, law_list in business_laws.items():
                    for law in law_list:
                        available_laws.append(
                            {
                                "service": service,
                                "law": law,
                                "discoverable": True,
                                "name": law.replace("_", " ").title(),
                                "description": f"Business law {law} managed by {service}",
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not get business laws: {e}")

            response_data = {"available_laws": available_laws, "total_count": len(available_laws)}
            return {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(response_data, indent=2)}]
            }
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
    prompts = []
    for name, template in PROMPT_TEMPLATES.items():
        # Create argument schema based on prompt type
        if name == "check_all_benefits":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {"name": "include_details", "description": "Include detailed explanations", "required": False},
            ]
        elif name == "explain_calculation":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {"name": "service", "description": "Service provider code", "required": True},
                {"name": "law", "description": "Law identifier", "required": True},
            ]
        elif name == "compare_scenarios":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {"name": "scenarios", "description": "List of scenarios to compare (JSON)", "required": True},
            ]
        elif name == "generate_citizen_report":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {"name": "include_projections", "description": "Include future benefit projections", "required": False},
            ]
        elif name == "optimize_benefits":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {
                    "name": "focus_area",
                    "description": "Area to focus on (all, income, family, housing)",
                    "required": False,
                },
            ]
        elif name == "legal_research":
            arguments = [
                {"name": "topic", "description": "Research topic", "required": True},
                {"name": "law", "description": "Specific law to research", "required": False},
                {"name": "service", "description": "Specific service to research", "required": False},
            ]
        elif name == "appeal_assistance":
            arguments = [
                {"name": "bsn", "description": "BSN van de persoon", "required": True},
                {"name": "decision_type", "description": "Type of decision to appeal", "required": False},
                {"name": "service", "description": "Service that made the decision", "required": False},
            ]
        else:
            arguments = []

        prompts.append(
            {
                "name": name,
                "description": template.description,
                "arguments": arguments,
            }
        )

    return {"prompts": prompts}


async def get_prompt(params: dict[str, Any]):
    """Get a specific prompt"""
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name not in PROMPT_TEMPLATES:
        return {
            "error": {"code": -32602, "message": f"Unknown prompt: {name}"},
        }

    try:
        template = PROMPT_TEMPLATES[name]
        prompt_result = template.generate(arguments)

        # Convert from MCP types to HTTP response format
        return {
            "description": prompt_result.description,
            "messages": [
                {
                    "role": msg.role,
                    "content": {"type": msg.content.type, "text": msg.content.text},
                }
                for msg in prompt_result.messages
            ],
        }
    except Exception as e:
        return {
            "error": {"code": -32603, "message": f"Error generating prompt: {str(e)}"},
        }
