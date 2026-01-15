"""
Service for managing TinySA device connections.

Provides a singleton-based service for managing device state and operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from backend.core.tinysa import TinySA, TinySAConnectionError, TinySAError, get_tinysa

logger = logging.getLogger(__name__)


@dataclass
class DeviceState:
    """Cached device state information."""

    connected: bool = False
    port: Optional[str] = None
    version: Optional[str] = None
    hardware: Optional[str] = None
    device_type: Optional[str] = None
    error: Optional[str] = None


class DeviceService:
    """Service for managing TinySA device connections.

    Uses the singleton TinySA instance from backend.core.tinysa and maintains
    cached device state for efficient status queries.
    """

    def __init__(self, tinysa: Optional[TinySA] = None) -> None:
        """Initialize the device service.

        Args:
            tinysa: Optional TinySA instance. If not provided, uses the singleton.
        """
        self._tinysa = tinysa or get_tinysa()
        self._cached_state = DeviceState()

    @property
    def tinysa(self) -> TinySA:
        """Get the TinySA instance."""
        return self._tinysa

    def list_ports(self) -> list[dict[str, Any]]:
        """List available serial ports with TinySA detection.

        Returns:
            List of port information dictionaries with an additional 'is_tinysa'
            field indicating if the port is likely a TinySA device.
        """
        ports = TinySA.list_ports()

        # Add TinySA detection heuristics
        for port in ports:
            is_tinysa = False

            # Check for TinySA indicators
            description = (port.get("description") or "").lower()
            product = (port.get("product") or "").lower()
            manufacturer = (port.get("manufacturer") or "").lower()

            if any(
                indicator in description
                for indicator in ["tinysa", "nanovna", "stm32"]
            ):
                is_tinysa = True
            elif any(indicator in product for indicator in ["tinysa", "nanovna"]):
                is_tinysa = True
            elif "stmicroelectronics" in manufacturer:
                is_tinysa = True
            # TinySA typically uses USB VID 0x0483 (STMicroelectronics)
            elif port.get("vid") == 0x0483:
                is_tinysa = True

            port["is_tinysa"] = is_tinysa

        return ports

    def get_status(self) -> DeviceState:
        """Get the current device connection status.

        Returns:
            DeviceState object with current connection information.
        """
        if self._tinysa.is_connected:
            return DeviceState(
                connected=True,
                port=self._tinysa.port,
                version=self._cached_state.version,
                hardware=self._cached_state.hardware,
                device_type=self._cached_state.device_type,
                error=None,
            )
        else:
            return DeviceState(
                connected=False,
                port=None,
                version=None,
                hardware=None,
                device_type=None,
                error=self._cached_state.error,
            )

    async def connect(self, port: str) -> dict[str, Any]:
        """Connect to a TinySA device.

        Args:
            port: Serial port path to connect to.

        Returns:
            Device information dictionary on successful connection.

        Raises:
            TinySAConnectionError: If connection fails.
        """
        try:
            # Connect and get device info
            device_info = await self._tinysa.connect(port)

            # Cache the device state
            self._cached_state = DeviceState(
                connected=True,
                port=device_info.get("port"),
                version=device_info.get("version"),
                hardware=device_info.get("hardware"),
                device_type=device_info.get("device_type"),
                error=None,
            )

            logger.info(f"Successfully connected to TinySA on {port}")
            return device_info

        except TinySAConnectionError as e:
            # Store the error for status queries
            self._cached_state = DeviceState(error=str(e))
            logger.error(f"Failed to connect to TinySA on {port}: {e}")
            raise

        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error connecting to {port}: {e}"
            self._cached_state = DeviceState(error=error_msg)
            logger.exception(error_msg)
            raise TinySAConnectionError(error_msg) from e

    async def disconnect(self) -> bool:
        """Disconnect from the TinySA device.

        Returns:
            True if disconnection was successful or device was already disconnected.
        """
        try:
            await self._tinysa.disconnect()

            # Clear cached state
            self._cached_state = DeviceState()

            logger.info("Successfully disconnected from TinySA")
            return True

        except TinySAError as e:
            logger.error(f"Error disconnecting from TinySA: {e}")
            # Still clear the cached state since we're attempting to disconnect
            self._cached_state = DeviceState(error=str(e))
            return False


# Singleton service instance
_device_service: Optional[DeviceService] = None


def get_device_service() -> DeviceService:
    """Get the singleton DeviceService instance.

    Returns:
        The global DeviceService instance.
    """
    global _device_service
    if _device_service is None:
        _device_service = DeviceService()
    return _device_service
