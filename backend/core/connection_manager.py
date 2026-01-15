"""WebSocket connection manager for real-time scan streaming.

Manages active WebSocket connections and provides methods for
broadcasting messages to connected clients.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time scan data streaming.

    Tracks active connections and provides methods for sending messages
    to individual clients or broadcasting to all connected clients.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_connections: list[WebSocket] = []

    @property
    def active_connections(self) -> list[WebSocket]:
        """Get list of active WebSocket connections."""
        return self._active_connections.copy()

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {self.connection_count}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the manager.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Active connections: {self.connection_count}")

    async def send_json(self, websocket: WebSocket, data: dict[str, Any]) -> bool:
        """Send JSON data to a specific WebSocket connection.

        Args:
            websocket: The target WebSocket connection
            data: Dictionary to send as JSON

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
            return False

    async def broadcast(self, data: dict[str, Any]) -> int:
        """Send JSON data to all active WebSocket connections.

        Args:
            data: Dictionary to broadcast as JSON

        Returns:
            Number of successful sends
        """
        success_count = 0
        disconnected: list[WebSocket] = []

        for connection in self._active_connections:
            try:
                await connection.send_json(data)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

        return success_count


# Singleton instance for application-wide use
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance.

    Returns:
        The global ConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
