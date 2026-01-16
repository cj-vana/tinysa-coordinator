"""
Negative tests for the WebSocket scan endpoint (/ws/scan).

These tests verify proper error handling for:
- Malformed JSON messages
- Invalid frequency values
- Concurrent scan attempts
- Unknown actions
- Missing required fields
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_tinysa_for_ws() -> MagicMock:
    """Create a mock TinySA device for WebSocket tests."""
    mock = MagicMock()
    mock.is_connected = True
    mock.port = "/dev/cu.usbmodem4001"
    mock.set_rbw = AsyncMock()

    # Mock scan_raw to yield test data with a slight delay
    async def mock_scan_raw(
        start_hz: int, stop_hz: int, points: int = 450
    ) -> AsyncGenerator[tuple[int, float], None]:
        """Generate mock scan data with async behavior."""
        freq_step = (stop_hz - start_hz) / (points - 1) if points > 1 else 0
        for i in range(points):
            freq_hz = int(start_hz + (i * freq_step))
            amplitude_dbm = -100.0 + (i % 10) * 0.5
            await asyncio.sleep(0.001)  # Small delay to simulate real scan
            yield (freq_hz, amplitude_dbm)

    mock.scan_raw = mock_scan_raw
    return mock


@pytest.fixture
def mock_tinysa_disconnected() -> MagicMock:
    """Create a mock TinySA device that is not connected."""
    mock = MagicMock()
    mock.is_connected = False
    mock.port = None
    return mock


# =============================================================================
# Malformed JSON Tests
# =============================================================================


class TestMalformedJSON:
    """Tests for handling malformed JSON messages over WebSocket."""

    @pytest.mark.unit
    def test_completely_invalid_json(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that completely invalid JSON returns an error message."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Send invalid JSON
                websocket.send_text("this is not valid json {{{")

                # Should receive error response
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]

    @pytest.mark.unit
    def test_empty_message(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that empty message is handled gracefully."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Send empty string (which is invalid JSON)
                websocket.send_text("")

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]

    @pytest.mark.unit
    def test_json_with_truncated_data(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that truncated JSON data returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Send truncated JSON
                websocket.send_text('{"action": "start_scan", "config": {"start_freq_hz":')

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]

    @pytest.mark.unit
    def test_json_with_single_quotes(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that JSON with single quotes (Python-style) is rejected."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Single quotes are invalid in JSON
                websocket.send_text("{'action': 'start_scan'}")

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]

    @pytest.mark.unit
    def test_json_with_trailing_comma(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that JSON with trailing comma is rejected."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Trailing comma is invalid in JSON
                websocket.send_text('{"action": "start_scan",}')

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]

    @pytest.mark.unit
    def test_binary_data_as_text(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that binary data sent as text is rejected."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Send non-UTF8 compatible data represented as escape sequences
                websocket.send_text("\x00\x01\x02\x03")

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]


# =============================================================================
# Invalid Frequency Tests
# =============================================================================


class TestInvalidFrequencies:
    """Tests for handling invalid frequency values in scan requests."""

    @pytest.mark.unit
    def test_start_freq_greater_than_stop_freq(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that start_freq_hz >= stop_freq_hz returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 700_000_000,  # 700 MHz
                            "stop_freq_hz": 400_000_000,  # 400 MHz (less than start)
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "start_freq_hz must be less than stop_freq_hz" in response["message"]

    @pytest.mark.unit
    def test_start_freq_equals_stop_freq(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that equal start and stop frequencies return an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 500_000_000,
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "start_freq_hz must be less than stop_freq_hz" in response["message"]

    @pytest.mark.unit
    def test_negative_start_frequency(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that negative start frequency returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": -100_000_000,
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "start_freq_hz must be positive" in response["message"]

    @pytest.mark.unit
    def test_non_numeric_frequency_string(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that non-numeric frequency values return an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": "not_a_number",
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert (
                    "Invalid frequency" in response["message"]
                    or "Invalid scan config" in response["message"]
                )

    @pytest.mark.unit
    def test_null_frequency_values(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that null frequency values return an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": None,
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"

    @pytest.mark.unit
    def test_missing_start_freq(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that missing start_freq_hz returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Missing required fields" in response["message"]
                assert "start_freq_hz" in response["message"]

    @pytest.mark.unit
    def test_missing_stop_freq(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that missing stop_freq_hz returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 400_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Missing required fields" in response["message"]
                assert "stop_freq_hz" in response["message"]

    @pytest.mark.unit
    def test_missing_both_frequencies(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that missing both frequencies returns appropriate error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Missing required fields" in response["message"]

    @pytest.mark.unit
    def test_empty_config_object(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that empty config object returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": "start_scan", "config": {}})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Missing required fields" in response["message"]

    @pytest.mark.unit
    def test_missing_config_entirely(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that missing config field returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": "start_scan"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Missing required fields" in response["message"]

    @pytest.mark.unit
    def test_frequency_as_float(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that float frequency values are accepted (converted to int)."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 400_000_000.5,  # Float value
                            "stop_freq_hz": 500_000_000.9,
                            "points": 10,
                        },
                    }
                )

                # Should either work (converted to int) or return scan_started
                response = websocket.receive_json()
                # If scan starts, it should send scan_started
                assert response["type"] in ["scan_started", "error"]


# =============================================================================
# Concurrent Scan Tests
# =============================================================================


class TestConcurrentScans:
    """Tests for handling concurrent scan attempts."""

    @pytest.mark.unit
    def test_start_scan_while_already_scanning(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that starting a scan while one is in progress returns an error."""

        # Create a slow mock that gives us time to send another start_scan
        async def slow_scan_raw(
            start_hz: int, stop_hz: int, points: int = 450
        ) -> AsyncGenerator[tuple[int, float], None]:
            for i in range(points):
                freq_hz = int(start_hz + i * 1000)
                await asyncio.sleep(0.1)  # Slow enough to test concurrent access
                yield (freq_hz, -100.0)

        mock_tinysa_for_ws.scan_raw = slow_scan_raw

        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Start first scan
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 400_000_000,
                            "stop_freq_hz": 500_000_000,
                            "points": 5,  # Few points but slow
                        },
                    }
                )

                # Wait for scan to start
                response = websocket.receive_json()
                assert response["type"] == "scan_started"

                # Try to start another scan immediately
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 600_000_000,
                            "stop_freq_hz": 700_000_000,
                            "points": 100,
                        },
                    }
                )

                # Collect responses - we should get an error about scan in progress
                # among the scan_point messages
                found_error = False
                for _ in range(10):  # Read several messages
                    response = websocket.receive_json()
                    if response["type"] == "error":
                        assert "Scan already in progress" in response["message"]
                        found_error = True
                        break
                    elif response["type"] == "scan_completed":
                        break

                assert found_error, "Expected 'Scan already in progress' error"

    @pytest.mark.unit
    def test_stop_scan_when_not_scanning(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that stopping when no scan is in progress returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Try to stop without starting
                websocket.send_json({"action": "stop_scan"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "No scan in progress" in response["message"]


# =============================================================================
# Unknown Action Tests
# =============================================================================


class TestUnknownActions:
    """Tests for handling unknown WebSocket actions."""

    @pytest.mark.unit
    def test_unknown_action(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that unknown actions return an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": "unknown_action"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]

    @pytest.mark.unit
    def test_missing_action_field(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that missing action field returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"some_field": "some_value"})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]

    @pytest.mark.unit
    def test_null_action(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that null action returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": None})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]

    @pytest.mark.unit
    def test_empty_action_string(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that empty action string returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": ""})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]

    @pytest.mark.unit
    def test_action_with_wrong_type(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that action with wrong type (number) returns an error."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json({"action": 12345})

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Unknown action" in response["message"]


# =============================================================================
# Device Not Connected Tests
# =============================================================================


class TestDeviceNotConnected:
    """Tests for handling scan requests when device is not connected."""

    @pytest.mark.unit
    def test_start_scan_device_not_connected(self, mock_tinysa_disconnected: MagicMock) -> None:
        """Test that starting a scan when device is not connected returns an error."""
        with (
            patch(
                "backend.services.scan_service.get_tinysa", return_value=mock_tinysa_disconnected
            ),
            patch(
                "backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_disconnected
            ),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 400_000_000,
                            "stop_freq_hz": 500_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "not connected" in response["message"].lower()


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_very_large_frequency_values(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test handling of very large frequency values."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 10**18,  # Extremely large
                            "stop_freq_hz": 10**19,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                # Should either work or return an error, but not crash
                assert response["type"] in ["scan_started", "error"]

    @pytest.mark.unit
    def test_zero_start_frequency(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that zero start frequency is handled."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 0,
                            "stop_freq_hz": 100_000_000,
                            "points": 100,
                        },
                    }
                )

                response = websocket.receive_json()
                # Zero is not negative, so should work or return device-level error
                assert response["type"] in ["scan_started", "error"]

    @pytest.mark.unit
    def test_multiple_malformed_messages_in_sequence(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that multiple malformed messages are handled independently."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Send multiple invalid messages
                websocket.send_text("invalid json 1")
                response1 = websocket.receive_json()
                assert response1["type"] == "error"

                websocket.send_text("invalid json 2")
                response2 = websocket.receive_json()
                assert response2["type"] == "error"

                # Connection should still work for valid messages
                websocket.send_json({"action": "stop_scan"})
                response3 = websocket.receive_json()
                assert response3["type"] == "error"
                assert "No scan in progress" in response3["message"]

    @pytest.mark.unit
    def test_extra_fields_in_config_are_ignored(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test that extra fields in config don't cause errors."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                websocket.send_json(
                    {
                        "action": "start_scan",
                        "config": {
                            "start_freq_hz": 400_000_000,
                            "stop_freq_hz": 500_000_000,
                            "points": 10,
                            "extra_field": "should be ignored",
                            "another_extra": 12345,
                        },
                    }
                )

                response = websocket.receive_json()
                # Should start scan successfully
                assert response["type"] == "scan_started"

    @pytest.mark.unit
    def test_deeply_nested_invalid_json(self, mock_tinysa_for_ws: MagicMock) -> None:
        """Test handling of deeply nested but malformed JSON."""
        with (
            patch("backend.services.scan_service.get_tinysa", return_value=mock_tinysa_for_ws),
            patch("backend.api.websocket.scan_ws.get_tinysa", return_value=mock_tinysa_for_ws),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/scan") as websocket:
                # Deeply nested but unclosed
                nested = '{"a":' * 50 + '"value"'  # Missing closing braces
                websocket.send_text(nested)

                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid JSON" in response["message"]
