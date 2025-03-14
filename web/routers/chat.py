import json
import os

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
        system_prompt = f"""
        Je bent een behulpzame assistent die Nederlandse burgers helpt met vragen over overheidsregelingen.

        Huidige burger profiel:
        Naam: {profile.get("name", "Onbekend")}
        Beschrijving: {profile.get("description", "Geen beschrijving beschikbaar")}
        BSN: {bsn}

        {mcp_connector.get_system_prompt()}

        Houd je antwoorden kort, informatief en relevant voor Nederlandse regelgeving. Als je het antwoord niet weet,
        wees dan eerlijk en geef aan waar ze officiële informatie kunnen vinden.

        Reageer in het Nederlands tenzij iemand expliciet vraagt om een andere taal.
        """

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

                # Add service results as user message (representing tool output)
                tool_response = {
                    "role": "user",
                    "content": f"""
Resultaten van tool aanroep:

{service_context}

Verwerk deze resultaten in je antwoord aan de burger. Leg uit wat de uitkomst betekent in eenvoudige taal.
Gebruik geen technische termen zoals "tool" of "resultaten" in je antwoord aan de burger.
""",
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

            # Send Claude's response back to the client
            await websocket.send_text(json.dumps({"message": final_message}))

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
