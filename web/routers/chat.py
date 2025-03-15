import json
import logging

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from machine.service import Services
from web.dependencies import get_services, templates
from web.services.chat_connection import manager
from web.services.chat_session import ChatSession
from web.services.llm_service import LLMService
from web.services.profiles import get_all_profiles, get_profile_data

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])

# Store active sessions
active_sessions: dict[str, ChatSession] = {}


@router.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request, bsn: str = "100000001", services: Services = Depends(get_services)):
    """Render the chat interface page.

    Args:
        request: The request object
        bsn: The BSN of the user
        services: The services dependency

    Returns:
        The rendered chat page
    """
    profile = get_profile_data(bsn)
    if not profile:
        return HTMLResponse("Profile not found", status_code=404)

    logger.info(f"Rendering chat page for BSN: {bsn}")

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
    """WebSocket endpoint for chat.

    Args:
        websocket: The WebSocket connection
        client_id: The client ID
        services: The services dependency
    """
    # Connect the client to the WebSocket manager
    await manager.connect(websocket, client_id)

    try:
        # Initialize services
        llm_service = LLMService(services)

        # Create or get the chat session
        if client_id not in active_sessions:
            session = ChatSession(client_id, llm_service)
            active_sessions[client_id] = session

            # Set up the session
            try:
                session.setup_system_prompt()
            except ValueError as e:
                logger.error(f"Error setting up session: {str(e)}")
                await manager.send_json({"error": str(e)}, client_id)
                manager.disconnect(client_id)
                return
        else:
            session = active_sessions[client_id]

        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            user_message = json.loads(data)

            # Add user message to session
            user_msg_content = user_message["message"]
            await session.add_user_message(user_msg_content)

            # Get initial response from Claude
            try:
                assistant_message = await session.generate_response()
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                await manager.send_json({"error": f"Error generating response: {str(e)}"}, client_id)
                continue

            # Clean the message (remove tool calls)
            cleaned_message = LLMService.clean_message(assistant_message)

            # Send the initial response to the client
            await manager.send_json({"message": cleaned_message}, client_id)

            # Process any service calls in the message
            try:
                # Reset the processed_services set at the start of each new user message
                session.processed_services = set()

                service_results = await session.process_service_calls(assistant_message)

                # If there are service results, generate a new response with tool results
                if service_results:
                    # Let the user know we're processing
                    await manager.send_processing_indicator(
                        "Ik ben even bezig met het uitvoeren van berekeningen... ⏳", client_id
                    )

                    # Generate a new response with the tool results
                    final_message = await session.generate_response_with_tool_results(service_results)

                    # Clean the message
                    cleaned_final_message = LLMService.clean_message(final_message)

                    # Send to client
                    await manager.send_json({"message": cleaned_final_message}, client_id)

                    # Process any chained service calls
                    await process_chained_services(session, final_message)
            except Exception as e:
                logger.error(f"Error processing service calls: {str(e)}")
                import traceback

                traceback.print_exc()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client {client_id}")
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]
    except Exception as e:
        logger.error(f"Error in websocket endpoint for client {client_id}: {str(e)}")
        import traceback

        traceback.print_exc()

        if client_id in manager.active_connections:
            await manager.send_json({"error": f"Server error: {str(e)}"}, client_id)

        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]


async def process_chained_services(session: ChatSession, message: str) -> None:
    """Process chained service calls recursively.

    Args:
        session: The chat session
        message: The message to process
    """
    try:
        logger.info("Starting chain processing for message")
        # Start the chain with the first message
        await session._recursive_process_next_steps(message)
        logger.info("Chain processing completed successfully")
    except Exception as e:
        logger.error(f"Error in chain processing: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
