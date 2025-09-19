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
from web.routers.laws import node_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


def extract_missing_parameters(
    result, machine_service, law: str, service: str, reference_date: str, arguments: dict
) -> list[dict]:
    """Extract missing parameters information from execution result."""
    missing_parameters = []
    if hasattr(result, "missing_required") and result.missing_required:
        provided_params = list(arguments.get("parameters", {}).keys()) or ["none"]

        # Extract specific missing field names from the value tree (same logic as mcp_services.py)
        missing_field_details = []
        if result.path:
            try:
                value_tree = machine_service.extract_value_tree(result.path)

                # Get rule specification to lookup parameter descriptions
                rule_spec = None
                try:
                    rule_spec = machine_service.get_rule_spec(law, reference_date, service)
                    logger.info(
                        f"Rule spec keys: {list(rule_spec.keys()) if isinstance(rule_spec, dict) else 'not a dict'}"
                    )
                    if isinstance(rule_spec, dict) and "sources" in rule_spec:
                        logger.info(f"Found sources in rule_spec: {rule_spec['sources']}")
                    if (
                        isinstance(rule_spec, dict)
                        and "properties" in rule_spec
                        and "sources" in rule_spec["properties"]
                    ):
                        logger.info(f"Found properties.sources in rule_spec: {rule_spec['properties']['sources']}")
                except Exception as e:
                    logger.warning(f"Could not get rule spec for descriptions: {e}")

                for path, node_info in value_tree.items():
                    if node_info.get("required") and not node_info.get("result"):
                        # Get the field name (last part of the path)
                        field_name = path.split(".")[-1]

                        # Try to find description from rule spec
                        description = None
                        if rule_spec and isinstance(rule_spec, dict):
                            # Check in parameters first
                            parameters = rule_spec.get("properties", {}).get("parameters", [])
                            if isinstance(parameters, list):
                                for param in parameters:
                                    if isinstance(param, dict) and param.get("name") == field_name:
                                        description = param.get("description")
                                        break

                            # If not found in parameters, check in input sources
                            if not description:
                                inputs = rule_spec.get("properties", {}).get("input", [])
                                if isinstance(inputs, list):
                                    for input_item in inputs:
                                        if isinstance(input_item, dict) and input_item.get("name") == field_name:
                                            description = input_item.get("description")
                                            break

                            # If still not found, check in sources section at root level
                            if not description:
                                sources = rule_spec.get("sources", [])
                                if isinstance(sources, list):
                                    for source_item in sources:
                                        if isinstance(source_item, dict) and source_item.get("name") == field_name:
                                            description = source_item.get("description")
                                            break

                                # Also check in properties.sources
                                if not description:
                                    properties_sources = rule_spec.get("properties", {}).get("sources", [])
                                    if isinstance(properties_sources, list):
                                        for source_item in properties_sources:
                                            if isinstance(source_item, dict) and source_item.get("name") == field_name:
                                                description = source_item.get("description")
                                                break

                        logger.info(f"DEBUG: Looking for description for field: {field_name}, found: {description}")
                        missing_field_details.append(
                            {"name": field_name, "description": description or f"Required parameter {field_name}"}
                        )

            except Exception as e:
                logger.warning(f"Could not extract missing fields from value tree: {e}")

        # Create detailed missing parameter info
        if missing_field_details:
            missing_parameters.append(
                {
                    "status": "missing_required_parameters",
                    "message": f"Required parameters are missing for {service}/{law}",
                    "missing_fields": missing_field_details,
                    "provided_parameters": provided_params,
                    "suggestion": f"Provide the missing parameters: {', '.join([field['name'] for field in missing_field_details])}",
                }
            )
        else:
            # Fallback if we can't extract specific field names
            missing_parameters.append(
                {
                    "status": "missing_required_parameters",
                    "message": f"Required parameters are missing for {service}/{law}",
                    "suggestion": f"Use the resource law://{service}/{law}/spec to see all required input parameters",
                    "provided_parameters": provided_params,
                    "help": "The law specification resource contains detailed information about required parameters, their types, and descriptions",
                }
            )

    return missing_parameters


def extract_execution_details(result, machine_service, law: str, service: str, reference_date: str) -> dict[str, Any]:
    """
    Extract path and rule_spec information from law execution result.

    Args:
        result: RuleResult from machine service evaluation
        machine_service: Machine service instance
        law: Law identifier
        service: Service identifier
        reference_date: Reference date for rule spec

    Returns:
        Dictionary containing path_dict and rule_spec_dict
    """
    execution_details = {}

    # Extract path information
    try:
        path_dict = node_to_dict(result.path, skip_services=True) if result.path else None
        execution_details["path"] = path_dict
    except Exception as e:
        logger.warning(f"Could not extract path information: {e}")
        execution_details["path"] = None

    # Extract rule specification
    try:
        rule_spec = machine_service.get_rule_spec(law, reference_date, service)
        # Filter relevant parts of rule_spec (same logic as laws router)
        relevant_spec = {
            "name": rule_spec.get("name"),
            "description": rule_spec.get("description"),
            "properties": {
                "input": rule_spec.get("properties", {}).get("input", []),
                "output": rule_spec.get("properties", {}).get("output", []),
                "parameters": rule_spec.get("properties", {}).get("parameters", []),
                "definitions": rule_spec.get("properties", {}).get("definitions", []),
            },
            "requirements": rule_spec.get("requirements"),
            "actions": rule_spec.get("actions"),
        }
        execution_details["rule_spec"] = relevant_spec
    except Exception as e:
        logger.warning(f"Could not extract rule specification: {e}")
        execution_details["rule_spec"] = None

    return execution_details


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

    # Note: MCP server doesn't require authentication - allowing all origins
    # Origin validation removed to allow Claude Code connections

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
    logger.info(f"call_tool called with tool: {tool_name}, args: {arguments}")

    try:
        if tool_name == "execute_law":
            overrides = arguments.get("overrides")

            # Use machine service to execute law
            try:
                result = machine_service.evaluate(
                    service=arguments["service"],
                    law=arguments["law"],
                    parameters=arguments["parameters"],
                    reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
                    overwrite_input=overrides,
                    requested_output=arguments.get("requested_output"),
                    approved=arguments.get("approved", False),
                )
            except Exception:
                raise

            # Get law metadata to provide context
            law_metadata = {}
            try:
                reference_date = arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d"))
                rule_spec = machine_service.get_rule_spec(
                    law=arguments["law"], reference_date=reference_date, service=arguments["service"]
                )
                law_metadata = {
                    "name": rule_spec.get("name", arguments["law"]),
                    "description": rule_spec.get("description", ""),
                    "service": rule_spec.get("service", arguments["service"]),
                    "law_type": rule_spec.get("law_type", ""),
                    "legal_character": rule_spec.get("legal_character", ""),
                }
            except Exception as e:
                logger.warning(f"Could not get law metadata: {e}")
                law_metadata = {
                    "name": arguments["law"],
                    "description": f"Law: {arguments['law']}",
                    "service": arguments["service"],
                }

            # Extract execution details (path and rule spec)
            reference_date = arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d"))
            execution_details = extract_execution_details(
                result, machine_service, arguments["law"], arguments["service"], reference_date
            )

            # Get detailed missing parameters information
            missing_parameters = extract_missing_parameters(
                result, machine_service, arguments["law"], arguments["service"], reference_date, arguments
            )

            # Return both human-readable content and structured data
            result_data = {
                "success": True,
                "output": result.output,
                "requirements_met": result.requirements_met,
                "input": result.input,
                "rulespec_uuid": result.rulespec_uuid,
                "missing_required": result.missing_required,
                "missing_parameters": missing_parameters,
                "law_metadata": law_metadata,
                "path": execution_details["path"],
                "rule_spec": execution_details["rule_spec"],
            }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Law execution completed. Requirements met: {result.requirements_met}",
                    }
                ],
                "structuredContent": result_data,
                "isError": False,
            }

        elif tool_name == "check_eligibility":
            # Check eligibility using machine service
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
                overwrite_input=arguments.get("overrides"),
            )
            # Check if requirements are met
            eligible = result.requirements_met

            # Extract execution details (path and rule spec)
            reference_date = arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d"))
            execution_details = extract_execution_details(
                result, machine_service, arguments["law"], arguments["service"], reference_date
            )

            # Get detailed missing parameters information
            missing_parameters = extract_missing_parameters(
                result, machine_service, arguments["law"], arguments["service"], reference_date, arguments
            )

            eligibility_data = {
                "eligible": eligible,
                "requirements_met": result.requirements_met,
                "missing_required": result.missing_required,
                "missing_parameters": missing_parameters,
                "path": execution_details["path"],
                "rule_spec": execution_details["rule_spec"],
            }

            return {
                "content": [{"type": "text", "text": f"Eligible: {eligible}"}],
                "structuredContent": eligibility_data,
                "isError": False,
            }

        elif tool_name == "calculate_benefit_amount":
            # Calculate benefit amount using machine service
            result = machine_service.evaluate(
                service=arguments["service"],
                law=arguments["law"],
                parameters=arguments["parameters"],
                reference_date=arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d")),
                overwrite_input=arguments.get("overrides"),
                requested_output=arguments["output_field"],
            )
            # Extract the requested output field
            output_field = arguments["output_field"]
            amount = result.output.get(output_field, "Not available")

            # Extract execution details (path and rule spec)
            reference_date = arguments.get("reference_date", datetime.today().strftime("%Y-%m-%d"))
            execution_details = extract_execution_details(
                result, machine_service, arguments["law"], arguments["service"], reference_date
            )

            # Get detailed missing parameters information
            missing_parameters = extract_missing_parameters(
                result, machine_service, arguments["law"], arguments["service"], reference_date, arguments
            )

            amount_data = {
                "amount": amount,
                "output_field": output_field,
                "full_output": result.output,
                "requirements_met": result.requirements_met,
                "missing_required": getattr(result, "missing_required", False),
                "missing_parameters": missing_parameters,
                "path": execution_details["path"],
                "rule_spec": execution_details["rule_spec"],
            }

            return {
                "content": [{"type": "text", "text": f"Amount: {amount}"}],
                "structuredContent": amount_data,
                "isError": False,
            }

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}


def get_all_required_parameters(
    machine_service, law: str, service: str, reference_date: str, visited_laws=None
) -> list[dict]:
    """
    Recursively extract all required parameters from a law and its dependencies.
    Returns a list of {name, description, source_law, source_service} objects.
    """
    if visited_laws is None:
        visited_laws = set()

    # Prevent infinite recursion
    law_key = f"{service}/{law}"
    if law_key in visited_laws:
        return []
    visited_laws.add(law_key)

    required_params = []

    try:
        rule_spec = machine_service.get_rule_spec(law, reference_date, service)
        if not isinstance(rule_spec, dict):
            return required_params

        properties = rule_spec.get("properties", {})

        # Extract required parameters
        for param in properties.get("parameters", []):
            if param.get("required", False):
                required_params.append(
                    {
                        "name": param.get("name"),
                        "description": param.get("description", f"Required parameter {param.get('name')}"),
                        "source_law": law,
                        "source_service": service,
                        "type": param.get("type", "unknown"),
                    }
                )

        # Extract required input fields
        for input_field in properties.get("input", []):
            if input_field.get("required", True):  # input fields are typically required by default
                required_params.append(
                    {
                        "name": input_field.get("name"),
                        "description": input_field.get("description", f"Required input {input_field.get('name')}"),
                        "source_law": law,
                        "source_service": service,
                        "type": input_field.get("type", "unknown"),
                    }
                )

                # Check for service_reference dependencies
                service_ref = input_field.get("service_reference")
                if service_ref:
                    dep_service = service_ref.get("service")
                    dep_law = service_ref.get("law")
                    if dep_service and dep_law:
                        # Recursively get parameters from dependent law
                        dep_params = get_all_required_parameters(
                            machine_service, dep_law, dep_service, reference_date, visited_laws
                        )
                        required_params.extend(dep_params)

        # Extract required sources
        for source in properties.get("sources", []):
            if source.get("required", False):
                required_params.append(
                    {
                        "name": source.get("name"),
                        "description": source.get("description", f"Required source {source.get('name')}"),
                        "source_law": law,
                        "source_service": service,
                        "type": source.get("type", "unknown"),
                    }
                )

    except Exception as e:
        logger.warning(f"Could not get parameters for {law}/{service}: {e}")

    return required_params


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
                        # Get the real law description from rule spec
                        try:
                            rule_spec = machine_service.get_rule_spec(law, "2025-01-01", service)
                            if isinstance(rule_spec, dict):
                                law_description = rule_spec.get(
                                    "description", f"Citizen law {law} managed by {service}"
                                )
                            else:
                                law_description = f"Citizen law {law} managed by {service}"
                        except Exception:
                            law_description = f"Citizen law {law} managed by {service}"

                        # Get all required parameters recursively
                        required_parameters = get_all_required_parameters(machine_service, law, service, "2025-01-01")

                        available_laws.append(
                            {
                                "service": service,
                                "law": law,
                                "discoverable": True,
                                "name": law.replace("_", " ").title(),
                                "description": law_description,
                                "required_parameters": required_parameters,
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not get citizen laws: {e}")

            # Get business laws
            try:
                business_laws = machine_service.get_discoverable_service_laws("BUSINESS")
                for service, law_list in business_laws.items():
                    for law in law_list:
                        # Get the real law description from rule spec
                        try:
                            rule_spec = machine_service.get_rule_spec(law, "2025-01-01", service)
                            if isinstance(rule_spec, dict):
                                law_description = rule_spec.get(
                                    "description", f"Business law {law} managed by {service}"
                                )
                            else:
                                law_description = f"Business law {law} managed by {service}"
                        except Exception:
                            law_description = f"Business law {law} managed by {service}"

                        # Get all required parameters recursively
                        required_parameters = get_all_required_parameters(machine_service, law, service, "2025-01-01")

                        available_laws.append(
                            {
                                "service": service,
                                "law": law,
                                "discoverable": True,
                                "name": law.replace("_", " ").title(),
                                "description": law_description,
                                "required_parameters": required_parameters,
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not get business laws: {e}")

            # Create plain text response with law descriptions
            text_lines = [f"Available Laws ({len(available_laws)} total):\n"]

            for law_info in available_laws:
                service = law_info["service"]
                law = law_info["law"]
                name = law_info["name"]
                description = law_info["description"]
                required_parameters = law_info.get("required_parameters", [])

                text_lines.append(f"• {name}")
                text_lines.append(f"  Service: {service}")
                text_lines.append(f"  Law ID: {law}")
                text_lines.append(f"  Resource: law://{service}/{law}/spec")
                text_lines.append(f"  Description: {description}")

                if required_parameters:
                    text_lines.append(f"  Required Parameters ({len(required_parameters)}):")
                    for param in required_parameters:
                        param_name = param.get("name", "unknown")
                        param_desc = param.get("description", "No description")
                        param_type = param.get("type", "unknown")
                        source_law = param.get("source_law", "")
                        source_service = param.get("source_service", "")

                        # Show parameter with source if it comes from a dependency
                        if source_law != law or source_service != service:
                            text_lines.append(
                                f"    - {param_name} ({param_type}): {param_desc} [from {source_service}/{source_law}]"
                            )
                            text_lines.append(f'      Override: {{"{source_service}": {{"{param_name}": value}}}}')
                        else:
                            text_lines.append(f"    - {param_name} ({param_type}): {param_desc}")
                            if param_type in ["amount", "number", "string", "boolean"]:
                                text_lines.append(f'      Override: {{"{service}": {{"{param_name}": value}}}}')
                else:
                    text_lines.append("  Required Parameters: None")

                text_lines.append("")  # Empty line between laws

            plain_text = "\n".join(text_lines)

            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": plain_text}]}
        elif uri.startswith("law://"):
            # Parse law://{service}/{law}/spec
            parts = uri.replace("law://", "").split("/")
            if len(parts) >= 3 and parts[-1] == "spec":
                service, law = parts[0], "/".join(parts[1:-1])  # Handle multi-part law names
                try:
                    # Get the actual rule specification
                    rule_spec = machine_service.get_rule_spec(law, "2025-01-01", service)

                    # Create plain text specification
                    text_lines = [f"Law Specification: {service}/{law}\n"]
                    text_lines.append(f"Service: {service}")
                    text_lines.append(f"Law ID: {law}")

                    # Debug: show what we got
                    text_lines.append(f"Rule spec type: {type(rule_spec)}")

                    # Handle different rule_spec formats safely
                    if isinstance(rule_spec, dict):
                        name = rule_spec.get("name", law)
                        description = rule_spec.get("description", "No description available")
                        text_lines.append(f"Name: {name}")
                        text_lines.append(f"Description: {description}")
                    elif isinstance(rule_spec, list):
                        text_lines.append(f"List with {len(rule_spec)} items:")
                        for i, item in enumerate(rule_spec[:3]):  # Show first 3 items
                            text_lines.append(f"  [{i}]: {type(item)} - {str(item)[:100]}...")
                        if len(rule_spec) > 3:
                            text_lines.append(f"  ... and {len(rule_spec) - 3} more items")
                    else:
                        text_lines.append(f"Raw specification: {str(rule_spec)[:500]}...")

                    plain_text = "\n".join(text_lines)
                    return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": plain_text}]}

                except Exception as e:
                    import traceback

                    error_detail = traceback.format_exc()
                    return {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "text/plain",
                                "text": f"Error loading law specification: {str(e)}\n\nDetails:\n{error_detail}",
                            }
                        ]
                    }
        elif uri.startswith("profile://"):
            # Parse profile://{bsn}
            bsn = uri.replace("profile://", "")
            profile = machine_service.get_profile_data(bsn)

            # Create plain text profile
            text_lines = [f"Citizen Profile: {profile.get('name', 'Unknown')}\n"]
            text_lines.append(f"BSN: {bsn}")
            text_lines.append(f"Description: {profile.get('description', 'No description available')}\n")

            # Add data sources
            if profile.get("sources"):
                text_lines.append("Available Data Sources:")
                for source_name, source_data in profile["sources"].items():
                    text_lines.append(f"  • {source_name}")
                    if isinstance(source_data, dict):
                        for key, value in source_data.items():
                            if isinstance(value, str | int | float | bool):
                                text_lines.append(f"    - {key}: {value}")
                            elif isinstance(value, list) and value:
                                text_lines.append(f"    - {key}: {len(value)} items")
                    text_lines.append("")

            plain_text = "\n".join(text_lines)
            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": plain_text}]}
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
