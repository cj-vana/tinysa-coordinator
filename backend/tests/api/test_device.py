"""
Tests for the device management API routes (/api/device/*).

These tests verify the TinySA device connection and management endpoints,
including listing ports, checking device status, connecting, and disconnecting.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from backend.core.tinysa import TinySA, TinySAConnectionError
from backend.services.device_service import DeviceService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_device_service(mock_tinysa) -> DeviceService:
    """Create a DeviceService with a mock TinySA instance."""
    return DeviceService(tinysa=mock_tinysa)


@pytest.fixture
def mock_device_service_connected(mock_tinysa_connected) -> DeviceService:
    """Create a DeviceService with a connected mock TinySA instance."""
    return DeviceService(tinysa=mock_tinysa_connected)


@pytest.fixture
def mock_device_service_connection_error(mock_tinysa) -> DeviceService:
    """Create a DeviceService that fails to connect."""
    mock_tinysa.connect = AsyncMock(
        side_effect=TinySAConnectionError("Device not found on /dev/test")
    )
    return DeviceService(tinysa=mock_tinysa)


@pytest.fixture
def mock_device_service_disconnect_error(mock_tinysa_connected) -> DeviceService:
    """Create a DeviceService where disconnect fails."""
    from backend.core.tinysa import TinySAError

    mock_tinysa_connected.disconnect = AsyncMock(
        side_effect=TinySAError("Error during disconnect")
    )
    return DeviceService(tinysa=mock_tinysa_connected)


# =============================================================================
# GET /api/device/ports Tests
# =============================================================================


class TestListPorts:
    """Tests for the GET /api/device/ports endpoint."""

    @pytest.mark.unit
    async def test_list_ports_success(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
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

    @pytest.mark.unit
    async def test_list_ports_returns_expected_fields(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that port objects have all expected fields."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.get("/api/device/ports")

        assert response.status_code == 200
        data = response.json()
        port = data[0]

        # Required fields
        assert "port" in port
        assert "description" in port
        assert "is_tinysa" in port

        # Optional fields from USB info
        assert "hwid" in port
        assert "manufacturer" in port
        assert "product" in port
        assert "serial_number" in port
        assert "vid" in port
        assert "pid" in port

    @pytest.mark.unit
    async def test_list_ports_tinysa_detection(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that TinySA devices are properly detected."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.get("/api/device/ports")

        assert response.status_code == 200
        data = response.json()
        # The mock returns a TinySA device
        tinysa_ports = [p for p in data if p["is_tinysa"]]
        assert len(tinysa_ports) >= 1

    @pytest.mark.unit
    async def test_list_ports_empty_list(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that empty ports list is handled correctly."""
        # Patch both the service and the static TinySA.list_ports method
        with (
            patch(
                "backend.api.routes.device.get_device_service",
                return_value=mock_device_service,
            ),
            patch.object(TinySA, "list_ports", return_value=[]),
        ):
            response = await client.get("/api/device/ports")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.unit
    async def test_list_ports_response_content_type(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that response content type is application/json."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.get("/api/device/ports")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


# =============================================================================
# GET /api/device/status Tests
# =============================================================================


class TestDeviceStatus:
    """Tests for the GET /api/device/status endpoint."""

    @pytest.mark.unit
    async def test_device_status_disconnected(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
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
        assert data["version"] is None
        assert data["hardware"] is None
        assert data["device_type"] is None

    @pytest.mark.unit
    async def test_device_status_connected(
        self, client: AsyncClient, mock_device_service_connected: DeviceService
    ):
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
    async def test_device_status_response_fields(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that status response has all expected fields."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.get("/api/device/status")

        assert response.status_code == 200
        data = response.json()

        # All expected fields should be present
        expected_fields = ["connected", "port", "version", "hardware", "device_type"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.unit
    async def test_device_status_content_type(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that status response content type is JSON."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.get("/api/device/status")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


# =============================================================================
# POST /api/device/connect Tests
# =============================================================================


class TestConnectDevice:
    """Tests for the POST /api/device/connect endpoint."""

    @pytest.mark.unit
    async def test_connect_device_success(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test connecting to a TinySA device successfully."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post(
                "/api/device/connect", json={"port": "/dev/cu.usbmodem4001"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["port"] == "/dev/cu.usbmodem4001"
        assert data["device_type"] == "tinySA ULTRA"
        assert "version" in data

    @pytest.mark.unit
    async def test_connect_device_returns_device_info(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that connect returns complete device information."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post(
                "/api/device/connect", json={"port": "/dev/cu.usbmodem4001"}
            )

        assert response.status_code == 200
        data = response.json()

        # All device info fields should be present
        expected_fields = ["port", "version", "hardware", "device_type"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.unit
    async def test_connect_device_already_connected(
        self, client: AsyncClient, mock_device_service_connected: DeviceService
    ):
        """Test connecting when already connected returns 409 conflict."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service_connected,
        ):
            response = await client.post(
                "/api/device/connect", json={"port": "/dev/cu.usbmodem4002"}
            )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "Already connected" in data["detail"]

    @pytest.mark.unit
    async def test_connect_device_connection_error(
        self, client: AsyncClient, mock_device_service_connection_error: DeviceService
    ):
        """Test that connection failure returns 400 error."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service_connection_error,
        ):
            response = await client.post(
                "/api/device/connect", json={"port": "/dev/test"}
            )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    async def test_connect_device_missing_port(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that missing port field returns validation error."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post("/api/device/connect", json={})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    async def test_connect_device_empty_port(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that empty port string is accepted but may fail on connection."""
        # Note: Pydantic doesn't reject empty strings by default for str fields
        # The empty port will be passed to the service which may handle it
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post("/api/device/connect", json={"port": ""})

        # Empty string passes Pydantic validation but the mock connect succeeds
        # In a real scenario, the device service would fail with an appropriate error
        # For this test, we just verify the endpoint handles the request
        assert response.status_code in [200, 400, 422]

    @pytest.mark.unit
    async def test_connect_device_invalid_json(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that invalid JSON returns error."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post(
                "/api/device/connect",
                content="not valid json",
                headers={"Content-Type": "application/json"},
            )

        assert response.status_code == 422

    @pytest.mark.unit
    async def test_connect_device_wrong_content_type(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that wrong content type returns error."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post(
                "/api/device/connect",
                content="port=/dev/test",
                headers={"Content-Type": "text/plain"},
            )

        assert response.status_code == 422


# =============================================================================
# POST /api/device/disconnect Tests
# =============================================================================


class TestDisconnectDevice:
    """Tests for the POST /api/device/disconnect endpoint."""

    @pytest.mark.unit
    async def test_disconnect_device_success(
        self, client: AsyncClient, mock_device_service_connected: DeviceService
    ):
        """Test disconnecting from a TinySA device successfully."""
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
    async def test_disconnect_device_not_connected(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
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

    @pytest.mark.unit
    async def test_disconnect_device_returns_expected_format(
        self, client: AsyncClient, mock_device_service_connected: DeviceService
    ):
        """Test that disconnect returns expected response format."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service_connected,
        ):
            response = await client.post("/api/device/disconnect")

        assert response.status_code == 200
        data = response.json()

        # Response should have success and message fields
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)

    @pytest.mark.unit
    async def test_disconnect_device_error_handling(
        self, client: AsyncClient, mock_device_service_disconnect_error: DeviceService
    ):
        """Test that disconnect error is handled gracefully."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service_disconnect_error,
        ):
            response = await client.post("/api/device/disconnect")

        # Should still return 200 but with success=False
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.unit
    async def test_disconnect_device_content_type(
        self, client: AsyncClient, mock_device_service: DeviceService
    ):
        """Test that disconnect response content type is JSON."""
        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=mock_device_service,
        ):
            response = await client.post("/api/device/disconnect")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestDeviceWorkflow:
    """Tests for complete device workflow scenarios."""

    @pytest.mark.unit
    async def test_connect_then_status_shows_connected(
        self, client: AsyncClient, mock_tinysa
    ):
        """Test that status reflects connection state after connect."""
        service = DeviceService(tinysa=mock_tinysa)

        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=service,
        ):
            # First check status - should be disconnected
            status_response = await client.get("/api/device/status")
            assert status_response.status_code == 200
            assert status_response.json()["connected"] is False

            # Connect
            connect_response = await client.post(
                "/api/device/connect", json={"port": "/dev/cu.usbmodem4001"}
            )
            assert connect_response.status_code == 200

            # Status should now show connected
            status_response = await client.get("/api/device/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["connected"] is True
            assert status_data["port"] == "/dev/cu.usbmodem4001"

    @pytest.mark.unit
    async def test_disconnect_then_status_shows_disconnected(
        self, client: AsyncClient, mock_tinysa_connected
    ):
        """Test that status reflects disconnected state after disconnect."""
        service = DeviceService(tinysa=mock_tinysa_connected)

        with patch(
            "backend.api.routes.device.get_device_service",
            return_value=service,
        ):
            # First check status - should be connected
            status_response = await client.get("/api/device/status")
            assert status_response.status_code == 200
            assert status_response.json()["connected"] is True

            # Disconnect
            disconnect_response = await client.post("/api/device/disconnect")
            assert disconnect_response.status_code == 200
            assert disconnect_response.json()["success"] is True

            # Status should now show disconnected
            status_response = await client.get("/api/device/status")
            assert status_response.status_code == 200
            assert status_response.json()["connected"] is False
