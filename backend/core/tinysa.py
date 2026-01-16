"""TinySA Ultra serial communication class.

Provides async-safe methods for communicating with TinySA Ultra spectrum analyzers
via USB serial connection.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)

# TinySA communication constants
BAUDRATE = 115200
TIMEOUT = 2.0  # seconds
PROMPT = b"ch> "
DEFAULT_POINTS = 450


class TinySAError(Exception):
    """Base exception for TinySA communication errors."""

    pass


class TinySAConnectionError(TinySAError):
    """Raised when connection to the device fails."""

    pass


class TinySACommandError(TinySAError):
    """Raised when a command fails or returns unexpected data."""

    pass


class TinySA:
    """Async-safe serial communication with TinySA Ultra spectrum analyzer.

    This class provides methods for connecting to and controlling a TinySA Ultra
    device via USB serial. All methods that communicate with the device are
    protected by an asyncio lock to ensure thread safety.

    Example:
        tinysa = TinySA()
        info = await tinysa.connect("/dev/cu.usbmodem4001")
        print(f"Connected to {info['device_type']} v{info['version']}")

        async for freq_hz, amplitude_dbm in tinysa.scan_raw(470_000_000, 698_000_000):
            print(f"{freq_hz / 1e6:.3f} MHz: {amplitude_dbm:.1f} dBm")

        await tinysa.disconnect()
    """

    def __init__(self) -> None:
        """Initialize the TinySA instance."""
        self._serial: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()
        self._port: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Check if the device is currently connected."""
        return self._serial is not None and self._serial.is_open

    @property
    def port(self) -> Optional[str]:
        """Get the current serial port, or None if not connected."""
        return self._port

    @staticmethod
    def list_ports() -> list[dict[str, Any]]:
        """List available serial ports.

        Returns:
            List of dictionaries containing port information with keys:
            - port: Device path
            - description: Human-readable description
            - hwid: Hardware ID
            - manufacturer: Device manufacturer (if available)
            - product: Product name (if available)
            - serial_number: Serial number (if available)
            - vid: USB Vendor ID (if available)
            - pid: USB Product ID (if available)
        """
        logger.debug("Enumerating serial ports")
        ports = []
        for port_info in serial.tools.list_ports.comports():
            ports.append({
                "port": port_info.device,
                "description": port_info.description or "",
                "hwid": port_info.hwid or "",
                "manufacturer": port_info.manufacturer,
                "product": port_info.product,
                "serial_number": port_info.serial_number,
                "vid": port_info.vid,
                "pid": port_info.pid,
            })
        logger.debug(f"Found {len(ports)} serial ports")
        return ports

    async def connect(self, port: str) -> dict[str, Any]:
        """Connect to a TinySA device on the specified serial port.

        Args:
            port: Serial port device path (e.g., "/dev/cu.usbmodem4001")

        Returns:
            Dictionary containing device information:
            - version: Firmware version string
            - hardware: Hardware revision (if available)
            - device_type: Device type identifier
            - port: Connected serial port

        Raises:
            TinySAConnectionError: If connection fails or device doesn't respond
        """
        logger.info(f"Attempting to connect to TinySA on port {port}")
        async with self._lock:
            if self._serial is not None and self._serial.is_open:
                logger.debug("Closing existing serial connection before reconnect")
                self._serial.close()

            try:
                logger.debug(f"Opening serial port {port} at {BAUDRATE} baud")
                self._serial = serial.Serial(
                    port=port,
                    baudrate=BAUDRATE,
                    timeout=TIMEOUT,
                    write_timeout=TIMEOUT,
                )
                self._port = port

                # Clear any pending data
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()

                # Small delay for device to be ready
                await asyncio.sleep(0.1)

                # Send a newline to get a fresh prompt
                self._serial.write(b"\r\n")
                await asyncio.sleep(0.1)
                self._serial.reset_input_buffer()

                # Get version info
                version_info = await self._send_command_internal("version")
                info_data = await self._send_command_internal("info")

                device_info = self._parse_device_info(version_info, info_data)
                device_info["port"] = port

                logger.info(f"Connected to TinySA on {port}: {device_info}")
                return device_info

            except serial.SerialException as e:
                logger.error(f"Serial connection failed for {port}: {e}")
                self._serial = None
                self._port = None
                raise TinySAConnectionError(f"Failed to connect to {port}: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the TinySA device."""
        async with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except serial.SerialException as e:
                    logger.debug(f"Error closing serial connection (ignored): {e}")
                finally:
                    self._serial = None
                    self._port = None
                    logger.info("Disconnected from TinySA")

    async def set_rbw(self, rbw_khz: Optional[float]) -> None:
        """Set the resolution bandwidth.

        Args:
            rbw_khz: Resolution bandwidth in kHz, or None for auto

        Raises:
            TinySAConnectionError: If not connected
            TinySACommandError: If command fails
        """
        async with self._lock:
            self._check_connected()
            if rbw_khz is None:
                logger.debug("Setting RBW to auto")
                await self._send_command_internal("rbw auto")
            else:
                # TinySA expects RBW in Hz for the command
                rbw_hz = int(rbw_khz * 1000)
                logger.debug(f"Setting RBW to {rbw_khz} kHz ({rbw_hz} Hz)")
                await self._send_command_internal(f"rbw {rbw_hz}")

    async def scan_raw(
        self,
        start_hz: int,
        stop_hz: int,
        points: int = DEFAULT_POINTS,
    ) -> AsyncIterator[tuple[int, float]]:
        """Perform a raw scan and yield frequency/amplitude pairs.

        This is an async generator that yields scan data points as they are
        received from the device. The scan uses the binary 'scanraw' command
        for efficient data transfer.

        Args:
            start_hz: Start frequency in Hz
            stop_hz: Stop frequency in Hz
            points: Number of scan points (default 450)

        Yields:
            Tuples of (frequency_hz, amplitude_dbm)

        Raises:
            TinySAConnectionError: If not connected
            TinySACommandError: If scan fails or returns invalid data
        """
        logger.info(
            f"Starting raw scan: {start_hz/1e6:.3f}-{stop_hz/1e6:.3f} MHz, {points} points"
        )
        async with self._lock:
            self._check_connected()

            # Send scanraw command
            cmd = f"scanraw {start_hz} {stop_hz} {points}\r\n"
            self._serial.write(cmd.encode())
            logger.debug(f"Sent scanraw command to device")

            # Read until we find the '{' marker that indicates binary data start
            buffer = b""
            timeout_count = 0
            max_timeouts = 50  # 50 * 0.1s = 5 seconds max wait

            while b"{" not in buffer:
                await asyncio.sleep(0.1)
                chunk = self._serial.read(self._serial.in_waiting or 1)
                if chunk:
                    buffer += chunk
                    timeout_count = 0
                else:
                    timeout_count += 1
                    if timeout_count > max_timeouts:
                        logger.error("Timeout waiting for scan data from device")
                        raise TinySACommandError("Timeout waiting for scan data")

            # Find the start of binary data
            start_idx = buffer.index(b"{") + 1
            remaining = buffer[start_idx:]

            # Calculate expected bytes: 3 bytes per point
            expected_bytes = points * 3
            data = remaining

            # Read remaining binary data
            while len(data) < expected_bytes:
                await asyncio.sleep(0.01)
                bytes_needed = expected_bytes - len(data)
                chunk = self._serial.read(min(bytes_needed, 1024))
                if chunk:
                    data += chunk

            # Calculate frequency step
            freq_step = (stop_hz - start_hz) / (points - 1) if points > 1 else 0

            # Parse binary data and yield results
            for i in range(points):
                offset = i * 3
                if offset + 2 >= len(data):
                    break

                # Skip first byte, read 2-byte little-endian unsigned int
                raw_value = struct.unpack("<H", data[offset + 1 : offset + 3])[0]

                # Convert to dBm: (raw / 32) - 128
                amplitude_dbm = (raw_value / 32.0) - 128.0

                # Calculate frequency for this point
                freq_hz = int(start_hz + (i * freq_step))

                yield (freq_hz, amplitude_dbm)

            # Read until we get the prompt back (to clear the buffer)
            await self._read_until_prompt()
            logger.debug(f"Scan complete, yielded {points} data points")

    async def _send_command_internal(self, command: str) -> str:
        """Send a command and return the response (internal, no lock).

        Args:
            command: Command string to send

        Returns:
            Response string from the device (without prompt)

        Raises:
            TinySACommandError: If command fails
        """
        self._check_connected()

        # Send command
        cmd_bytes = f"{command}\r\n".encode()
        self._serial.write(cmd_bytes)
        logger.debug(f"Sent command: {command}")

        # Read response
        response = await self._read_until_prompt()
        return response

    async def _read_until_prompt(self) -> str:
        """Read serial data until the prompt is received.

        Returns:
            Response string (without the prompt)
        """
        buffer = b""
        timeout_count = 0
        max_timeouts = 50  # 5 seconds max

        while not buffer.endswith(PROMPT):
            await asyncio.sleep(0.1)
            chunk = self._serial.read(self._serial.in_waiting or 1)
            if chunk:
                buffer += chunk
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout_count > max_timeouts:
                    logger.warning(f"Timeout reading response, got: {buffer}")
                    break

        # Remove the prompt and decode
        if buffer.endswith(PROMPT):
            buffer = buffer[: -len(PROMPT)]

        # Clean up the response
        response = buffer.decode("utf-8", errors="replace").strip()
        logger.debug(f"Response: {response[:100]}...")
        return response

    def _check_connected(self) -> None:
        """Check if connected and raise if not."""
        if not self.is_connected:
            raise TinySAConnectionError("Not connected to TinySA device")

    def _parse_device_info(
        self, version_response: str, info_response: str
    ) -> dict[str, Any]:
        """Parse version and info responses into device info dict.

        Args:
            version_response: Response from 'version' command
            info_response: Response from 'info' command

        Returns:
            Dictionary with parsed device information
        """
        info: dict[str, Any] = {
            "version": None,
            "hardware": None,
            "device_type": None,
        }

        # Parse version response
        # Response format (command is echoed):
        # "version\r\ntinySA4_v1.4-140-g294ba13\r\nHW Version:V0.4.5.1.1"
        version_lines = version_response.strip().split("\n")
        for line in version_lines:
            line = line.strip()
            # Skip empty lines and the echoed command
            if not line or line.lower() == "version":
                continue

            # Check for hardware version line
            if "hw version" in line.lower() or "hw:" in line.lower():
                parts = line.split(":", 1)
                if len(parts) > 1:
                    info["hardware"] = parts[1].strip()
                continue

            # This should be the version string (e.g., "tinySA4_v1.4-140-g294ba13")
            if info["version"] is None:
                info["version"] = line
                # Try to extract device type
                if "tinysa4" in line.lower() or "ultra" in line.lower():
                    info["device_type"] = "tinySA ULTRA"
                elif "tinysa" in line.lower():
                    info["device_type"] = "tinySA"

        # Parse info response for additional details (if not found in version)
        if info["hardware"] is None:
            info_lines = info_response.strip().split("\n")
            for line in info_lines:
                line_lower = line.strip().lower()
                if "hardware" in line_lower or "hw" in line_lower:
                    # Extract hardware version
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        info["hardware"] = parts[1].strip()
                        break

        return info


# Singleton instance for application-wide use
_tinysa_instance: Optional[TinySA] = None


def get_tinysa() -> TinySA:
    """Get the singleton TinySA instance.

    Returns:
        The global TinySA instance
    """
    global _tinysa_instance
    if _tinysa_instance is None:
        _tinysa_instance = TinySA()
    return _tinysa_instance
