import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
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


# MCP Streamable HTTP endpoint (2025 spec compatible)
@router.post("/")
@router.get("/")
async def mcp_streamable_endpoint(request: Request):
    """
    MCP Streamable HTTP endpoint compatible with 2025 specification.

    Supports both GET (for SSE streaming) and POST (for JSON-RPC requests).
    Single endpoint design as per latest MCP spec.
    """
    session_id = str(uuid.uuid4())

    if request.method == "GET":
        # Handle GET request - return SSE stream for server-initiated communication
        accept_header = request.headers.get("accept", "")

        if "text/event-stream" not in accept_header:
            raise HTTPException(status_code=405, detail="Method Not Allowed")

        async def event_generator():
            try:
                # Send initial capabilities
                capabilities = {
                    "tools": list(TOOL_SCHEMAS.keys()),
                    "resources": ["laws://list", "law://{service}/{law}/spec", "profile://{parameter}"],
                    "prompts": list(PROMPT_TEMPLATES.keys()),
                }

                yield {
                    "event": "mcp.initialize",
                    "data": json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2025-03-26",
                                "capabilities": capabilities,
                                "serverInfo": {"name": "machine-law-executor", "version": "1.0.0"},
                            },
                            "id": f"init-{session_id}",
                        }
                    ),
                }

                # Keep connection alive
                while True:
                    await asyncio.sleep(30)
                    yield {"event": "heartbeat", "data": json.dumps({"timestamp": datetime.now().isoformat()})}

            except asyncio.CancelledError:
                pass

        response = EventSourceResponse(event_generator())
        response.headers["Mcp-Session-Id"] = session_id
        return response

    elif request.method == "POST":
        # Handle POST request - process JSON-RPC messages
        accept_header = request.headers.get("accept", "")
        content_type = request.headers.get("content-type", "")

        if "application/json" not in content_type:
            raise HTTPException(status_code=400, detail="Content-Type must be application/json")

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Process JSON-RPC request(s)
        if isinstance(body, list):
            # Batch request - respond with SSE stream
            async def batch_event_generator():
                for rpc_request in body:
                    result = await process_mcp_request(rpc_request)
                    yield {"event": "mcp.response", "data": json.dumps(result)}

            response = EventSourceResponse(batch_event_generator())
            response.headers["Mcp-Session-Id"] = session_id
            return response

        else:
            # Single request - can respond with JSON or SSE
            result = await process_mcp_request(body)

            if "text/event-stream" in accept_header:
                # Client accepts streaming - use SSE
                async def single_event_generator():
                    yield {"event": "mcp.response", "data": json.dumps(result)}

                response = EventSourceResponse(single_event_generator())
                response.headers["Mcp-Session-Id"] = session_id
                return response
            else:
                # Standard JSON response
                response = JSONResponse(result)
                response.headers["Mcp-Session-Id"] = session_id
                return response


async def process_mcp_request(rpc_request: dict) -> dict:
    """Process a single MCP JSON-RPC request"""
    try:
        method = rpc_request.get("method")
        params = rpc_request.get("params", {})
        request_id = rpc_request.get("id")

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": list(TOOL_SCHEMAS.values())}}

        elif method == "tools/call":
            # Use existing tool call logic
            from web.dependencies import get_machine_service

            machine_service = get_machine_service()

            tool_result = await call_tool_mcp_compatible(params, machine_service)

            return {"jsonrpc": "2.0", "id": request_id, "result": tool_result}

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": [
                        {"uri": "laws://list", "name": "Available Laws", "description": "List of all discoverable laws"}
                    ]
                },
            }

        elif method == "resources/read":
            uri = params.get("uri")
            if uri == "laws://list":
                from web.dependencies import get_machine_service

                machine_service = get_machine_service()

                # Get both citizen and business laws
                available_laws = []
                try:
                    citizen_laws = machine_service.get_discoverable_service_laws("CITIZEN")
                    for service, law_list in citizen_laws.items():
                        for law in law_list:
                            available_laws.append(
                                {"service": service, "law": law, "type": "CITIZEN", "parameter_type": "BSN"}
                            )
                except Exception as e:
                    logger.warning(f"Could not get citizen laws: {e}")

                try:
                    business_laws = machine_service.get_discoverable_service_laws("BUSINESS")
                    for service, law_list in business_laws.items():
                        for law in law_list:
                            available_laws.append(
                                {"service": service, "law": law, "type": "BUSINESS", "parameter_type": "KVK_NUMMER"}
                            )
                except Exception as e:
                    logger.warning(f"Could not get business laws: {e}")

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(
                                    {"available_laws": available_laws, "total_count": len(available_laws)}, indent=2
                                ),
                            }
                        ]
                    },
                }
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Resource not found"}}

        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}

    except Exception as e:
        logger.error(f"MCP request processing error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": rpc_request.get("id"),
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }


async def call_tool_mcp_compatible(params: dict, machine_service) -> dict:
    """Call tool in MCP-compatible format"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "execute_law":
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
            )
            return {
                "content": [
                    {
                        "type": "application/json",
                        "data": {
                            "output": result.output,
                            "requirements_met": result.requirements_met,
                            "input": result.input,
                            "rulespec_uuid": result.rulespec_uuid,
                            "missing_required": result.missing_required,
                        },
                    }
                ]
            }

        elif tool_name == "check_eligibility":
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
            )
            return {"content": [{"type": "text", "text": f"Eligible: {result.requirements_met}"}]}

        elif tool_name == "calculate_benefit_amount":
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
                requested_output=arguments["output_field"],
            )
            output_field = arguments["output_field"]
            amount = result.output.get(output_field, "Not available")
            return {"content": [{"type": "text", "text": f"Amount: {amount}"}]}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        raise


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
            # Return the result object directly as JSON
            return {
                "content": [
                    {
                        "type": "application/json",
                        "data": {
                            "output": result.output,
                            "requirements_met": result.requirements_met,
                            "input": result.input,
                            "rulespec_uuid": result.rulespec_uuid,
                            "missing_required": result.missing_required,
                        },
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
