import asyncio
import json
import re

from fastapi import APIRouter, Depends, Form, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from explain.llm_factory import LLMFactory
from explain.mcp_connector import MCPLawConnector
from web.dependencies import (
    TODAY,
    get_case_manager,
    get_claim_manager,
    get_engine_id,
    get_machine_service,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.feature_flags import is_chat_enabled
from web.utils import format_message

router = APIRouter(prefix="/chat", tags=["chat"])

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


async def handle_application_display(
    websocket: WebSocket,
    bsn: str,
    services,
    case_manager,
    claim_manager,
    mcp_connector,
    service_results,
    messages,
    user_msg_content,
    templates,
):
    """Display an application panel in the chat interface."""
    from web.routers.laws import evaluate_law

    try:
        # Parse the message to identify service and law
        msg = user_msg_content.lower()
        registry_service_name = None  # This is the service name in the registry (e.g. "zorgtoeslag")
        service = None  # This is the service type (e.g. "TOESLAGEN")
        law = None  # This is the law path (e.g. "zorgtoeslagwet")

        # First try to use the service name directly from application_form reference
        if "application_form" in service_results:
            registry_service_name = service_results["application_form"]["service"]

            # Get the service details from the registry
            service_obj = mcp_connector.registry.get_service(registry_service_name)
            if service_obj:
                service = service_obj.service_type
                law = service_obj.law_path

        # If not found yet, try to identify from other service results
        if not service or not law:
            # Filter out the application_form entry if it exists
            filtered_results = {k: v for k, v in service_results.items() if k != "application_form"}

            if filtered_results and len(filtered_results) > 0:
                result_service_name = list(filtered_results.keys())[0]
                service_obj = mcp_connector.registry.get_service(result_service_name)
                if service_obj:
                    registry_service_name = result_service_name
                    service = service_obj.service_type
                    law = service_obj.law_path

        # Last resort: search for all service names in the message
        if not service or not law:
            # Get all service names from the registry
            all_service_names = mcp_connector.registry.get_service_names()

            # Find service names that appear in the message
            for name in all_service_names:
                if name.lower() in msg:
                    service_obj = mcp_connector.registry.get_service(name)
                    if service_obj:
                        registry_service_name = name
                        service = service_obj.service_type
                        law = service_obj.law_path
                        break

        if service and law:
            # Get data for the application panel - explicitly use approved=False to include unapproved claims
            law, result, parameters = evaluate_law(bsn, law, service, services, approved=False)

            # Get the rule spec separately
            rule_spec = services.get_rule_spec(law, TODAY, service)

            # Use the service's extract_value_tree method, which now should be properly set up
            value_tree = services.extract_value_tree(result.path)

            # Get claims for this user
            claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
            claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

            # Get existing case if any
            existing_case = case_manager.get_case(bsn, service, law)

            # Render the application panel template with in_chat_panel=True
            panel_html = templates.get_template("partials/tiles/components/application_form.html").render(
                request=None,
                service=service,
                law=law,
                rule_spec=rule_spec,
                input=result.input,
                result=result.output,
                requirements_met=result.requirements_met,
                path=value_tree,
                bsn=bsn,
                current_case=existing_case,
                claim_map=claim_map,
                missing_required=result.missing_required,
                in_chat_panel=True,
                registry_service_name=registry_service_name,  # Pass the registry service name for submission
                current_engine_id=get_engine_id(),
            )

            # Send the application panel to the client
            await websocket.send_text(
                json.dumps(
                    {
                        "applicationPanel": True,
                        "html": panel_html,
                        "service": registry_service_name,  # Send the registry service name
                        "law": law,
                        "bsn": bsn,
                    }
                )
            )

            # Don't add anything to the conversation history when showing application panel
            # Since the form is shown after the LLM response, we don't need to track it in the conversation

            return True
        else:
            # No service/law identified, send message asking for more info
            # Include the available service names in the message to help the user
            available_services = mcp_connector.registry.get_service_names()
            service_list = ", ".join([s for s in available_services])

            error_msg = (
                "Ik kan geen specifieke regeling vinden om een aanvraagformulier voor te tonen. "
                "Kunt u aangeven voor welke van de volgende regelingen u een aanvraag wilt doen?\n\n"
                f"Beschikbare regelingen: {service_list}"
            )
            html_message = format_message(error_msg)
            await websocket.send_text(json.dumps({"message": error_msg, "html": str(html_message)}))

            # Add messages to conversation
            messages.append({"role": "user", "content": user_msg_content})
            messages.append({"role": "assistant", "content": error_msg})

            return True

    except Exception as e:
        print(f"Error showing application panel: {str(e)}")
        import traceback

        traceback.print_exc()

        # Send error message as a system message
        error_msg = "Er is een fout opgetreden bij het tonen van het aanvraagformulier. Probeer het later opnieuw."
        html_message = format_message(error_msg)
        await websocket.send_text(
            json.dumps({"message": error_msg, "html": str(html_message), "isSystemMessage": True})
        )

        # Add messages to conversation
        messages.append({"role": "user", "content": user_msg_content})
        messages.append({"role": "assistant", "content": error_msg})

        return True


async def handle_application_submission(
    websocket: WebSocket, bsn: str, services, case_manager, mcp_connector, service_name, law_path=None
):
    """Handle submission of an application from the chat interface."""
    try:
        # Import the laws router for application submission
        from web.routers.laws import evaluate_law

        # Get the service details from the registry using the service name
        service_obj = mcp_connector.registry.get_service(service_name)

        if not service_obj:
            error_msg = f"Service '{service_name}' niet gevonden in het systeem."
            html_message = format_message(error_msg)
            await websocket.send_text(json.dumps({"message": error_msg, "html": str(html_message)}))
            return True

        # Extract service type and law path from the service object
        service_type = service_obj.service_type
        law = law_path or service_obj.law_path

        # Get data needed for submission
        law, result, parameters = evaluate_law(bsn, law, service_type, services, approved=False)
        rule_spec = services.get_rule_spec(law, TODAY, service_type)

        # Submit the case
        case_manager.submit_case(
            bsn=bsn,
            service=service_type,
            law=law,
            parameters=parameters,
            claimed_result=result.output,
            approved_claims_only=False,
        )

        # Send confirmation message
        # This will be the final message shown to the user, no additional LLM response needed
        confirmation_msg = f"Uw aanvraag voor {rule_spec.get('name')} is succesvol verzonden."
        html_message = format_message(confirmation_msg)
        await websocket.send_text(
            json.dumps({"message": confirmation_msg, "html": str(html_message), "isSystemMessage": True})
        )

        return True

    except Exception as e:
        error_msg = f"Er is een fout opgetreden bij het indienen van uw aanvraag: {str(e)}"
        html_message = format_message(error_msg)
        await websocket.send_text(
            json.dumps({"message": error_msg, "html": str(html_message), "isSystemMessage": True})
        )

        print(f"Error submitting application: {str(e)}")
        import traceback

        traceback.print_exc()

        return True


manager = ChatConnectionManager()


@router.get("/", response_class=HTMLResponse)
async def get_chat_page(
    request: Request,
    bsn: str = "100000001",
    llm: str = Query(None, description="LLM provider to use (claude or vlam)"),
    services: EngineInterface = Depends(get_machine_service),
):
    """Render the chat interface page"""
    # Check if chat feature is enabled
    if not is_chat_enabled():
        return templates.TemplateResponse(
            "partials/feature_disabled.html", {"request": request, "feature_name": "Chat", "return_url": f"/?bsn={bsn}"}
        )

    profile = services.get_profile_data(bsn)
    if not profile:
        return HTMLResponse("Profile not found", status_code=404)

    # Get available and configured LLM providers
    available_providers = LLMFactory.get_available_providers()
    configured_providers = LLMFactory.get_configured_providers(request)

    # Determine which provider to use
    current_provider = None

    # First, check URL parameter
    if llm and llm in configured_providers:
        current_provider = llm
        request.session["preferred_llm_provider"] = llm

    # Then check session
    elif (
        "preferred_llm_provider" in request.session
        and request.session["preferred_llm_provider"] in configured_providers
    ):
        current_provider = request.session["preferred_llm_provider"]

    # Fall back to default
    else:
        current_provider = LLMFactory.get_provider(request)

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "all_profiles": services.get_all_profiles(),
            "llm_providers": available_providers,
            "current_provider": current_provider,
            "chat_enabled": is_chat_enabled(),
            "wallet_enabled": is_chat_enabled(),
        },
    )


@router.post("/set-provider")
async def set_chat_provider(request: Request, provider: str = Form(...)):
    """Set the preferred LLM provider in the session"""
    configured_providers = LLMFactory.get_configured_providers(request)

    if provider in configured_providers:
        request.session["preferred_llm_provider"] = provider

    # Redirect back to the chat page
    return templates.TemplateResponse(
        "partials/provider_updated.html",
        {
            "request": request,
            "provider": provider,
        },
    )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    services: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    # Check if chat feature is enabled
    if not is_chat_enabled():
        await websocket.accept()
        await websocket.send_text(json.dumps({"error": "Chat feature is currently disabled", "feature_disabled": True}))
        await websocket.close()
        return
    await manager.connect(websocket, client_id)

    try:
        # First receive connection data to get provider and BSN
        data = await websocket.receive_text()
        connection_data = json.loads(data)

        # Get the BSN from the client_id or connection data
        bsn = connection_data.get("bsn") or (client_id.split("_")[1] if "_" in client_id else "100000001")
        # Get LLM provider from request or use default
        selected_provider = connection_data.get("provider") or LLMFactory.get_provider()

        profile = services.get_profile_data(bsn)

        if not profile:
            error_msg = f"Profile not found for BSN: {bsn}"
            print(error_msg)
            await websocket.send_text(json.dumps({"error": error_msg}))
            manager.disconnect(client_id)
            return

        # services.set_profile_data(bsn) # TODO verify if this is necessary

        # Check if selected provider is properly configured
        if not LLMFactory.is_provider_configured(selected_provider):
            error_msg = f"LLM provider {selected_provider} is not properly configured"
            print(error_msg)
            await websocket.send_text(json.dumps({"error": error_msg}))
            manager.disconnect(client_id)
            return

        # Get appropriate LLM service using the factory
        llm_service = LLMFactory.get_service(selected_provider)

        # Send confirmation with provider info
        await websocket.send_text(
            json.dumps({"connected": True, "provider": selected_provider, "model": llm_service.model_id, "bsn": bsn})
        )

        mcp_connector = MCPLawConnector(services, case_manager, claim_manager)

        # Initial empty system prompt placeholder - we'll update it with fresh claims data each time
        system_prompt = ""

        # Function to get fresh system prompt with up-to-date cases data
        def get_updated_system_prompt():
            cases_context = mcp_connector.get_cases_context(bsn)
            return mcp_connector.jinja_env.get_template("chat_system_prompt.j2").render(
                profile=profile,
                bsn=bsn,
                cases_context=cases_context,
                mcp_system_prompt=mcp_connector.get_system_prompt(),
            )

        # Initialize system prompt with initial data
        system_prompt = get_updated_system_prompt()

        # Initialize the conversation with just a list for user/assistant messages
        messages = []

        # Initialize variable to track service results
        service_results = {}

        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            user_message = json.loads(data)

            # Handle application submission
            if user_message.get("submitApplication"):
                service_name = user_message.get("service")
                law = user_message.get("law")

                if await handle_application_submission(
                    websocket, bsn, services, case_manager, mcp_connector, service_name, law
                ):
                    continue

            # Note: We previously had code here to check for "toon aanvraagformulier",
            # but now we're using the LLM+tool approach instead, which is handled during service processing

            # Regular message handling
            user_msg_content = user_message.get("message", "")
            messages.append({"role": "user", "content": user_msg_content})

            # Get fresh system prompt with up-to-date claims data before each message
            system_prompt = get_updated_system_prompt()

            # Send message to get initial response using the LLM service
            response = llm_service.chat_completion(
                messages=messages,
                max_tokens=2000,
                system=system_prompt,
                temperature=0.7,
            )

            # Extract the message text using the service's standard method
            assistant_message = llm_service.get_completion_text(response)

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
                                        claim_manager.submit_claim(
                                            service=service.service_type,
                                            key=key,
                                            new_value=parsed_value,
                                            reason=f"Gebruiker gaf waarde door via chat: '{value_str}'",
                                            claimant=f"CHAT_USER_{bsn}",
                                            law=service.law_path,
                                            bsn=bsn,
                                            auto_approve=False,  # Don't auto-approve to ensure proper review
                                        )

                                        # Update system prompt with new claim data
                                        system_prompt = get_updated_system_prompt()
                                        print(f"Created claim for {key}={parsed_value} for service {service_name}")
                        except Exception as e:
                            print(f"Error creating claim for {key}: {str(e)}")
                            import traceback

                            traceback.print_exc()

            # Process Claude's message with MCP connector to extract and execute law services
            service_results = mcp_connector.process_message(assistant_message, bsn)

            # Get fresh system prompt with updated claims data
            system_prompt = get_updated_system_prompt()

            # If there are service results, add them to the context and generate a new response
            final_message = assistant_message

            # Store the application form reference for later
            app_form_request = None
            if "application_form" in service_results:
                app_form_service = service_results["application_form"]["service"]
                # Store the request for later, after the LLM responds
                app_form_request = {
                    "service": app_form_service,
                    "results": {k: v for k, v in service_results.items() if k != "application_form"},
                }

                # Remove the application_form from service_results to avoid confusion
                service_results.pop("application_form")

            if service_results:
                # Let the user know we're executing services
                processing_msg = "Ik ben even bezig met het uitvoeren van berekeningen... ⏳"
                html_message = format_message(processing_msg)
                await websocket.send_text(
                    json.dumps({"message": processing_msg, "html": str(html_message), "isProcessing": True})
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

                # Get latest claims data before generating the final response
                system_prompt = get_updated_system_prompt()

                # Get a new response with the tool results
                final_response = llm_service.chat_completion(
                    messages=tool_conversation,
                    max_tokens=2000,
                    system=system_prompt,
                    temperature=0.7,
                )

                # Get the final message with tool results incorporated
                final_message = llm_service.get_completion_text(final_response)

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

            # Server-side markdown rendering
            html_message = format_message(cleaned_message)

            # Send Claude's response back to the client with pre-rendered HTML
            await websocket.send_text(json.dumps({"message": cleaned_message, "html": str(html_message)}))

            # Now, if we have a pending application form request, display it AFTER the LLM response
            if app_form_request:
                # Give a small delay for better user experience
                await asyncio.sleep(0.5)

                # Display the application panel
                await handle_application_display(
                    websocket,
                    bsn,
                    services,
                    case_manager,
                    claim_manager,
                    mcp_connector,
                    app_form_request["results"],
                    messages,
                    f"Toon aanvraagformulier voor {app_form_request['service']}",
                    templates,
                )

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
                    claims_result = mcp_connector.claim_processor.process_claims(claim_refs, bsn)

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
                    processing_msg = f"Ik ga nu kijken naar uw recht op {service_name}... ⏳"
                    html_message = format_message(processing_msg)
                    await websocket.send_text(
                        json.dumps({"message": processing_msg, "html": str(html_message), "isProcessing": True})
                    )

                    try:
                        # Execute the service
                        result = service.execute(bsn, {})
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

                        # Get a new response using the LLM service
                        next_response = llm_service.chat_completion(
                            messages=next_conversation,
                            max_tokens=2000,
                            system=system_prompt,
                            temperature=0.7,
                        )

                        # Get the response message
                        next_message = llm_service.get_completion_text(next_response)

                        # Update conversation history
                        current_messages.append({"role": "user", "content": content})
                        current_messages.append({"role": "assistant", "content": next_message})

                        # Clean message before sending to client
                        cleaned_next_message = clean_message(next_message)

                        # Server-side markdown rendering
                        html_message = format_message(cleaned_next_message)

                        # Send response to client with pre-rendered HTML
                        await websocket.send_text(
                            json.dumps({"message": cleaned_next_message, "html": str(html_message)})
                        )

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
