"""
WebSocket connection manager for chat functionality.
"""

import json

from fastapi import WebSocket


class ChatConnectionManager:
    """Manages active WebSocket connections for chat functionality."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new client.

        Args:
            websocket: The WebSocket connection
            client_id: A unique ID for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """Disconnect a client.

        Args:
            client_id: The client ID to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: str, client_id: str) -> None:
        """Send a message to a client.

        Args:
            message: The message to send
            client_id: The client ID to send the message to
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def send_json(self, data: dict, client_id: str) -> None:
        """Send JSON data to a client.

        Args:
            data: The data to send
            client_id: The client ID to send the data to
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(data))

    async def send_processing_indicator(self, message: str, client_id: str) -> None:
        """Send a processing indicator message to a client.

        Args:
            message: The processing message to show
            client_id: The client ID to send the message to
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps({"message": message, "isProcessing": True}))


# Singleton instance
manager = ChatConnectionManager()
