"""
Tests for the device management API routes.

These tests verify the TinySA device connection and management endpoints.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from backend.services.device_service import DeviceService


@pytest.fixture
def mock_device_service(mock_tinysa) -> DeviceService:
    """Create a DeviceService with a mock TinySA instance."""
    return DeviceService(tinysa=mock_tinysa)


@pytest.fixture
def mock_device_service_connected(mock_tinysa_connected) -> DeviceService:
    """Create a DeviceService with a connected mock TinySA instance."""
    return DeviceService(tinysa=mock_tinysa_connected)


@pytest.mark.unit
async def test_list_ports(client: AsyncClient, mock_device_service):
    """Test that listing serial ports returns expected format."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service,
    ):
        response = await client.get("/api/device/ports")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check that the first port has expected fields
    port = data[0]
    assert "port" in port
    assert "description" in port
    assert "is_tinysa" in port


@pytest.mark.unit
async def test_device_status_disconnected(client: AsyncClient, mock_device_service):
    """Test device status when no device is connected."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service,
    ):
        response = await client.get("/api/device/status")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["port"] is None


@pytest.mark.unit
async def test_device_status_connected(client: AsyncClient, mock_device_service_connected):
    """Test device status when a device is connected."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service_connected,
    ):
        response = await client.get("/api/device/status")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["port"] == "/dev/cu.usbmodem4001"


@pytest.mark.unit
async def test_connect_device(client: AsyncClient, mock_device_service):
    """Test connecting to a TinySA device."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service,
    ):
        response = await client.post("/api/device/connect", json={"port": "/dev/cu.usbmodem4001"})

    assert response.status_code == 200
    data = response.json()
    assert data["port"] == "/dev/cu.usbmodem4001"
    assert data["device_type"] == "tinySA ULTRA"
    assert "version" in data


@pytest.mark.unit
async def test_connect_device_already_connected(client: AsyncClient, mock_device_service_connected):
    """Test connecting when already connected returns conflict error."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service_connected,
    ):
        response = await client.post("/api/device/connect", json={"port": "/dev/cu.usbmodem4002"})

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "Already connected" in data["detail"]


@pytest.mark.unit
async def test_disconnect_device(client: AsyncClient, mock_device_service_connected):
    """Test disconnecting from a TinySA device."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service_connected,
    ):
        response = await client.post("/api/device/disconnect")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "disconnect" in data["message"].lower()


@pytest.mark.unit
async def test_disconnect_device_not_connected(client: AsyncClient, mock_device_service):
    """Test disconnecting when no device is connected."""
    with patch(
        "backend.api.routes.device.get_device_service",
        return_value=mock_device_service,
    ):
        response = await client.post("/api/device/disconnect")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "no device" in data["message"].lower()
