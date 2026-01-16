"""WebSocket connection manager for real-time scan streaming.

Manages active WebSocket connections and provides methods for
broadcasting messages to connected clients. Includes connection
limits to prevent resource exhaustion.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from backend.core.rate_limit import get_rate_limit_config

logger = logging.getLogger(__name__)


class WebSocketConnectionLimitExceeded(Exception):
    """Raised when the WebSocket connection limit is exceeded."""

    def __init__(self, current_count: int, max_connections: int) -> None:
        self.current_count = current_count
        self.max_connections = max_connections
        super().__init__(f"WebSocket connection limit exceeded: {current_count}/{max_connections}")


class ConnectionManager:
    """Manages WebSocket connections for real-time scan data streaming.

    Tracks active connections and provides methods for sending messages
    to individual clients or broadcasting to all connected clients.
    Enforces connection limits to prevent resource exhaustion.
    """

    def __init__(self, max_connections: int | None = None) -> None:
        """Initialize the connection manager.

        Args:
            max_connections: Maximum allowed concurrent connections.
                             If None, uses the value from rate limit config.
        """
        self._active_connections: list[WebSocket] = []
        self._max_connections = max_connections

    @property
    def max_connections(self) -> int:
        """Get the maximum allowed concurrent connections."""
        if self._max_connections is not None:
            return self._max_connections
        config = get_rate_limit_config()
        return config.websocket_max_connections

    @property
    def active_connections(self) -> list[WebSocket]:
        """Get list of active WebSocket connections."""
        return self._active_connections.copy()

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)

    def can_accept_connection(self) -> bool:
        """Check if a new connection can be accepted.

        Returns:
            True if the connection count is below the limit, False otherwise.
        """
        return self.connection_count < self.max_connections

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept

        Raises:
            WebSocketConnectionLimitExceeded: If the connection limit is reached
        """
        if not self.can_accept_connection():
            logger.warning(
                f"WebSocket connection rejected: limit exceeded "
                f"({self.connection_count}/{self.max_connections})"
            )
            raise WebSocketConnectionLimitExceeded(
                current_count=self.connection_count,
                max_connections=self.max_connections,
            )

        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Active connections: "
            f"{self.connection_count}/{self.max_connections}"
        )

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

    async def graceful_shutdown(self, reason: str = "Server shutting down") -> None:
        """Gracefully close all WebSocket connections with a shutdown notification.

        Sends a server_shutdown message to all connected clients before closing
        connections. This allows clients to handle the shutdown gracefully
        (e.g., disable auto-reconnect).

        Args:
            reason: Human-readable reason for the shutdown
        """
        if not self._active_connections:
            logger.info("No active WebSocket connections to close")
            return

        logger.info(
            f"Initiating graceful shutdown for {self.connection_count} WebSocket connections"
        )

        # Send shutdown notification to all clients
        shutdown_message = {
            "type": "server_shutdown",
            "reason": reason,
        }

        # Send shutdown message to all connections concurrently
        async def notify_and_close(ws: WebSocket) -> None:
            try:
                # Only send if the connection is still open
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(shutdown_message)
                    # Give client a moment to process the message
                    await asyncio.sleep(0.1)
                    await ws.close(code=1001, reason=reason)
                    logger.debug("Gracefully closed WebSocket connection")
            except Exception as e:
                logger.debug(f"Error during graceful WebSocket close: {e}")

        # Close all connections concurrently with a timeout
        close_tasks = [notify_and_close(ws) for ws in self._active_connections]
        try:
            await asyncio.wait_for(
                asyncio.gather(*close_tasks, return_exceptions=True),
                timeout=5.0,  # 5 second timeout for graceful shutdown
            )
        except TimeoutError:
            logger.warning("Graceful shutdown timed out, forcing connection closure")

        # Clear the connections list
        self._active_connections.clear()
        logger.info("All WebSocket connections closed")


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
