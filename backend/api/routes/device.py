"""
API routes for TinySA device management.

Provides endpoints for listing serial ports, checking device status,
and managing device connections.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.core.exceptions import DeviceAlreadyConnectedError, DeviceConnectionError
from backend.core.tinysa import TinySAConnectionError
from backend.schemas.device import DeviceInfo, DeviceStatus, SerialPort
from backend.services.device_service import DeviceService, get_device_service

router = APIRouter(prefix="/api/device", tags=["device"])


class ConnectRequest(BaseModel):
    """Request body for device connection."""

    port: str = Field(..., description="Serial port path to connect to")


class DisconnectResponse(BaseModel):
    """Response for device disconnection."""

    success: bool = Field(..., description="Whether disconnection was successful")
    message: str = Field(..., description="Status message")


class SerialPortWithTinySA(SerialPort):
    """Serial port information with TinySA detection."""

    is_tinysa: bool = Field(
        False, description="Whether this port is likely a TinySA device"
    )


class DeviceStatusResponse(DeviceStatus):
    """Extended device status response with error information."""

    error: Optional[str] = Field(None, description="Last error message if any")


def get_service() -> DeviceService:
    """Dependency to get DeviceService instance."""
    return get_device_service()


@router.get("/ports", response_model=list[SerialPortWithTinySA])
async def list_ports(
    service: DeviceService = Depends(get_service),
) -> list[SerialPortWithTinySA]:
    """
    List available serial ports.

    Returns a list of available serial ports with metadata and an indication
    of whether each port is likely a TinySA device based on USB identifiers.
    """
    ports = service.list_ports()
    return [SerialPortWithTinySA(**port) for port in ports]


@router.get("/status", response_model=DeviceStatusResponse)
async def get_status(
    service: DeviceService = Depends(get_service),
) -> DeviceStatusResponse:
    """
    Get the current device connection status.

    Returns information about the currently connected device, or indicates
    that no device is connected. Also includes the last error message if
    a previous connection attempt failed.
    """
    state = service.get_status()
    return DeviceStatusResponse(
        connected=state.connected,
        port=state.port,
        version=state.version,
        hardware=state.hardware,
        device_type=state.device_type,
        error=state.error,
    )


@router.post("/connect", response_model=DeviceInfo)
async def connect(
    request: ConnectRequest,
    service: DeviceService = Depends(get_service),
) -> DeviceInfo:
    """
    Connect to a TinySA device.

    Establishes a connection to a TinySA device on the specified serial port.
    Returns device information on successful connection.

    Raises:
        400: If the port is invalid or connection fails
        409: If already connected to a device
    """
    # Check if already connected
    current_status = service.get_status()
    if current_status.connected:
        raise DeviceAlreadyConnectedError(
            message=f"Already connected to device on {current_status.port}. Disconnect first.",
            current_port=current_status.port,
        )

    try:
        device_info = await service.connect(request.port)
        return DeviceInfo(
            version=device_info.get("version", "unknown"),
            hardware=device_info.get("hardware"),
            device_type=device_info.get("device_type"),
            port=device_info.get("port", request.port),
        )
    except TinySAConnectionError as e:
        raise DeviceConnectionError(
            message=str(e),
            port=request.port,
        ) from e


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect(
    service: DeviceService = Depends(get_service),
) -> DisconnectResponse:
    """
    Disconnect from the TinySA device.

    Closes the connection to the currently connected TinySA device.
    Returns success even if no device was connected.
    """
    current_status = service.get_status()

    if not current_status.connected:
        return DisconnectResponse(
            success=True,
            message="No device was connected",
        )

    success = await service.disconnect()

    if success:
        return DisconnectResponse(
            success=True,
            message="Successfully disconnected from device",
        )
    else:
        return DisconnectResponse(
            success=False,
            message="Error occurred during disconnection",
        )
