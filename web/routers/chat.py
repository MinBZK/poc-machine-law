import json
import os
import re

import anthropic
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from explain.mcp_connector import MCPLawConnector
from machine.service import Services
from web.dependencies import get_services, templates
from web.services.profiles import get_profile_data

router = APIRouter(prefix="/chat", tags=["chat"])

# Store active connections
connections: dict[str, list[WebSocket]] = {}


class ChatConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)


manager = ChatConnectionManager()


@router.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request, bsn: str = "100000001", services: Services = Depends(get_services)):
    """Render the chat interface page"""
    profile = get_profile_data(bsn)
    if not profile:
        return HTMLResponse("Profile not found", status_code=404)

    from web.services.profiles import get_all_profiles

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "all_profiles": get_all_profiles(),  # Add this for the profile selector
        },
    )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, services: Services = Depends(get_services)):
    await manager.connect(websocket, client_id)

    try:
        # Get the BSN from the client_id (client_id format is "chat_{bsn}")
        bsn = client_id.split("_")[1] if "_" in client_id else "100000001"
        profile = get_profile_data(bsn)

        if not profile:
            error_msg = f"Profile not found for BSN: {bsn}"
            print(error_msg)
            await websocket.send_text(json.dumps({"error": error_msg}))
            manager.disconnect(client_id)
            return

        # Set up Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            error_msg = "ANTHROPIC_API_KEY environment variable not set"
            print(error_msg)
            await websocket.send_text(json.dumps({"error": error_msg}))
            manager.disconnect(client_id)
            return

        client = anthropic.Anthropic(api_key=api_key)

        # Set up MCP connector
        mcp_connector = MCPLawConnector(services)

        # Create initial system prompt with profile context and dynamic service information
        system_prompt = mcp_connector.jinja_env.get_template("chat_system_prompt.j2").render(
            profile=profile, bsn=bsn, mcp_system_prompt=mcp_connector.get_system_prompt()
        )

        # Initialize the conversation with just a list for user/assistant messages
        messages = []

        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            user_message = json.loads(data)

            # Add user message to conversation
            user_msg_content = user_message["message"]
            messages.append({"role": "user", "content": user_msg_content})

            # Send message to Claude API to get initial response
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
                temperature=0.7,
            )

            # Get Claude's response and extract any tool calls
            assistant_message = response.content[0].text

            # Check for value responses to previous questions about missing fields
            # Format would be like "mijn inkomen is 35000 euro" or "mijn leeftijd is 42"
            # Extract these as key-value pairs and create claims

            # Simple pattern matching for common formats: "mijn X is Y" or "X: Y"
            value_patterns = [
                r"(?:mijn|mij|ik heb|ik ben|mijn|mijn|het)\s+([a-zéëïöüáóúA-Z\s_]+)\s+(?:is|zijn|bedraagt|heb|ben)\s+([0-9.,]+(?:\s*(?:euro|jaar|maanden|dagen|weken|personen|kinderen))?)",
                r"([a-zéëïöüáóúA-Z\s_]+):\s*([0-9.,]+(?:\s*(?:euro|jaar|maanden|dagen|weken|personen|kinderen))?)",
            ]

            # Try to extract claims from user message
            for pattern in value_patterns:
                matches = re.findall(pattern, user_msg_content)
                for match in matches:
                    if len(match) == 2:
                        key, value = match
                        key = key.strip().lower().replace(" ", "_")

                        # Clean up the value
                        value_str = value.strip()
                        parsed_value = value_str

                        if "euro" in value_str:
                            # Convert euro to cents
                            value_str = value_str.replace("euro", "").strip()
                            try:
                                # Replace comma with dot for float parsing
                                value_str = value_str.replace(",", ".")
                                # Convert to cents (integer)
                                parsed_value = int(float(value_str) * 100)
                            except ValueError:
                                # If conversion fails, keep as string
                                parsed_value = value_str
                        elif value_str.replace(".", "", 1).isdigit() or value_str.replace(",", "", 1).isdigit():
                            # Convert to appropriate number type
                            try:
                                if "," in value_str:
                                    value_str = value_str.replace(",", ".")
                                parsed_value = float(value_str) if "." in value_str else int(value_str)
                            except ValueError:
                                parsed_value = value_str

                        try:
                            # Get services that might need this claim
                            # If we're responding to a specific service request, use that service
                            service_refs = mcp_connector.service_executor.extract_service_references(assistant_message)
                            if service_refs:
                                for service_name in service_refs:
                                    service = mcp_connector.registry.get_service(service_name)
                                    if service:
                                        # Submit claim for this value
                                        services.claim_manager.submit_claim(
                                            service=service.service_type,
                                            key=key,
                                            new_value=parsed_value,
                                            reason=f"Gebruiker gaf waarde door via chat: '{value_str}'",
                                            claimant=f"CHAT_USER_{bsn}",
                                            law=service.law_path,
                                            bsn=bsn,
                                            auto_approve=True,  # Auto-approve user-provided values in chat
                                        )
                                        print(f"Created claim for {key}={parsed_value} for service {service_name}")
                        except Exception as e:
                            print(f"Error creating claim for {key}: {str(e)}")
                            import traceback

                            traceback.print_exc()

            # Process Claude's message with MCP connector to extract and execute law services
            service_results = await mcp_connector.process_message(assistant_message, bsn)

            # If there are service results, add them to the context and generate a new response
            final_message = assistant_message
            if service_results:
                # Let the user know we're executing services
                await websocket.send_text(
                    json.dumps(
                        {"message": "Ik ben even bezig met het uitvoeren van berekeningen... ⏳", "isProcessing": True}
                    )
                )

                # Format the service results
                service_context = mcp_connector.format_results_for_llm(service_results)

                # Create a temporary message from Claude that includes the tool call
                tool_message = {"role": "assistant", "content": assistant_message}

                # Check if there are missing required fields
                missing_fields = []
                for service_name, result in service_results.items():
                    if isinstance(result.get("missing_fields"), list) and result.get("missing_fields"):
                        missing_fields.extend([(service_name, field) for field in result.get("missing_fields")])

                # Prepare content for the tool response using the template
                content = mcp_connector.jinja_env.get_template("tool_response.j2").render(
                    service_context=service_context, missing_fields=missing_fields if missing_fields else None
                )

                # Add service results as user message (representing tool output)
                tool_response = {
                    "role": "user",
                    "content": content,
                }

                # Create a new conversation with the tool interaction
                tool_conversation = messages.copy()
                tool_conversation.append(tool_message)
                tool_conversation.append(tool_response)

                # Get a new response from Claude with the tool results
                final_response = client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=tool_conversation,
                    temperature=0.7,
                )

                # Get the final message with tool results incorporated
                final_message = final_response.content[0].text

                # Update our conversation history
                messages.append(tool_message)
                messages.append(tool_response)

            # Add the final message to the conversation history
            messages.append({"role": "assistant", "content": final_message})

            # Function to clean messages - extracted for reuse
            def clean_message(message_text):
                # Remove tool_use blocks
                cleaned = re.sub(r"<tool_use>[\s\S]*?<\/tool_use>", "", message_text)
                # Remove any empty lines that might be left
                cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
                return cleaned.strip()

            # Clean the message
            cleaned_message = clean_message(final_message)

            # Send Claude's response back to the client
            await websocket.send_text(json.dumps({"message": cleaned_message}))

            # Helper function for recursive law chaining and claim processing
            # We keep track of processed services to avoid duplicates in the same chain
            processed_services = set()

            async def process_next_step(current_message, current_messages):
                """Process the next step in the chain recursively.

                This handles both claim_value tools and service tools in a single recursive function.
                For claims, it processes them and then re-executes the relevant service.
                For service tools, it executes the requested service.
                In both cases, it continues the recursion with the new response.
                """
                print("Processing next step in chain")

                # Create fresh list of services to execute for this recursion level only
                services_to_execute = []

                # First check for claims - they take precedence
                claim_refs = mcp_connector.claim_processor.extract_claims(current_message)
                if claim_refs:
                    print(f"Found {len(claim_refs)} claim references in message")
                    claims_result = await mcp_connector.claim_processor.process_claims(claim_refs, bsn)

                    if claims_result and claims_result.get("submitted"):
                        # Collect affected services for execution
                        for claim in claims_result.get("submitted", []):
                            service_name = claim.get("service")
                            if service_name and service_name not in services_to_execute:
                                services_to_execute.append(service_name)
                                print(f"Adding service {service_name} to execution list due to claim")

                # Then check for service references
                service_refs = mcp_connector.service_executor.extract_service_references(current_message)
                if service_refs:
                    for service_name in service_refs:
                        if service_name not in services_to_execute:
                            services_to_execute.append(service_name)
                            print(f"Adding service {service_name} to execution list due to tool call")

                # If no services to execute, we're done with the recursion
                if not services_to_execute:
                    print("No services to execute, ending recursion")
                    return

                # Execute each service in order, but skip already processed ones in this chain
                for service_name in services_to_execute:
                    # Skip if we've already processed this service in this chain
                    if service_name in processed_services:
                        print(f"Skipping already processed service {service_name} in this chain")
                        continue

                    # Add to processed services set
                    processed_services.add(service_name)

                    service = mcp_connector.registry.get_service(service_name)
                    if not service:
                        print(f"Service {service_name} not found, skipping")
                        continue

                    # Let the user know we're executing this service
                    await websocket.send_text(
                        json.dumps(
                            {"message": f"Ik ga nu kijken naar uw recht op {service_name}... ⏳", "isProcessing": True}
                        )
                    )

                    try:
                        # Execute the service
                        result = await service.execute(bsn, {})
                        service_results = {service_name: result}

                        # Format the results
                        service_context = mcp_connector.format_results_for_llm(service_results)

                        # Create message prompt based on context
                        is_from_claim = service_name in services_to_execute[: len(claim_refs)] if claim_refs else False

                        if is_from_claim:
                            content = mcp_connector.jinja_env.get_template("claim_processing.j2").render(
                                service_name=service_name, service_context=service_context
                            )
                        else:
                            content = mcp_connector.jinja_env.get_template("chained_service.j2").render(
                                service_name=service_name, service_context=service_context
                            )

                        # Create a new conversation with these results
                        next_conversation = current_messages.copy()
                        next_conversation.append({"role": "user", "content": content})

                        # Get a new response from Claude
                        next_response = client.messages.create(
                            model="claude-3-7-sonnet-20250219",
                            max_tokens=2000,
                            system=system_prompt,
                            messages=next_conversation,
                            temperature=0.7,
                        )

                        # Get the response message
                        next_message = next_response.content[0].text

                        # Update conversation history
                        current_messages.append({"role": "user", "content": content})
                        current_messages.append({"role": "assistant", "content": next_message})

                        # Clean message before sending to client
                        cleaned_next_message = clean_message(next_message)

                        # Send response to client
                        await websocket.send_text(json.dumps({"message": cleaned_next_message}))

                        # Continue recursion with this new message
                        await process_next_step(next_message, current_messages)

                    except Exception as e:
                        print(f"Error executing service {service_name}: {str(e)}")
                        import traceback

                        traceback.print_exc()

            # Start recursive chaining process with the current message
            await process_next_step(final_message, messages)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for client {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        print(f"Error in websocket endpoint for client {client_id}: {str(e)}")
        import traceback

        traceback.print_exc()
        if client_id in manager.active_connections:
            await websocket.send_text(json.dumps({"error": f"Server error: {str(e)}"}))
        manager.disconnect(client_id)
