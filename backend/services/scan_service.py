"""Scan service for real-time spectrum scanning.

Provides functionality to run scans on TinySA device and stream
data points to WebSocket clients in real-time.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from backend.core.tinysa import (
    TinySA,
    TinySACommandError,
    TinySAConnectionError,
    get_tinysa,
)

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = logging.getLogger(__name__)

# TinySA Ultra hardware constraints
MIN_FREQ_HZ = 100_000  # 100 kHz minimum frequency
MAX_FREQ_HZ = 6_000_000_000  # 6 GHz maximum frequency
MIN_POINTS = 10
MAX_POINTS = 10000
MIN_RBW_KHZ = 0.2  # 200 Hz minimum RBW
MAX_RBW_KHZ = 850.0  # 850 kHz maximum RBW

# Valid RBW values for TinySA Ultra (in kHz)
# These are the discrete RBW settings supported by the hardware
VALID_RBW_VALUES_KHZ = [
    0.2,
    0.5,
    1.0,
    2.0,
    3.0,
    5.0,
    10.0,
    30.0,
    100.0,
    300.0,
    600.0,
    850.0,
]


class ScanConfigError(ValueError):
    """Raised when scan configuration is invalid."""

    pass


@dataclass
class ScanConfig:
    """Configuration for a spectrum scan."""

    start_freq_hz: int
    stop_freq_hz: int
    points: int = 450
    rbw_khz: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "start_freq_hz": self.start_freq_hz,
            "stop_freq_hz": self.stop_freq_hz,
            "points": self.points,
            "rbw_khz": self.rbw_khz,
        }

    def validate(self) -> list[str]:
        """Validate scan configuration against hardware constraints.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Validate frequency range
        if self.start_freq_hz < MIN_FREQ_HZ:
            errors.append(
                f"start_freq_hz must be at least {MIN_FREQ_HZ} Hz ({MIN_FREQ_HZ / 1e3:.1f} kHz)"
            )
        if self.start_freq_hz > MAX_FREQ_HZ:
            errors.append(
                f"start_freq_hz must be at most {MAX_FREQ_HZ} Hz ({MAX_FREQ_HZ / 1e9:.1f} GHz)"
            )
        if self.stop_freq_hz < MIN_FREQ_HZ:
            errors.append(
                f"stop_freq_hz must be at least {MIN_FREQ_HZ} Hz ({MIN_FREQ_HZ / 1e3:.1f} kHz)"
            )
        if self.stop_freq_hz > MAX_FREQ_HZ:
            errors.append(
                f"stop_freq_hz must be at most {MAX_FREQ_HZ} Hz ({MAX_FREQ_HZ / 1e9:.1f} GHz)"
            )
        if self.start_freq_hz >= self.stop_freq_hz:
            errors.append("start_freq_hz must be less than stop_freq_hz")

        # Validate points
        if self.points < MIN_POINTS:
            errors.append(f"points must be at least {MIN_POINTS}")
        if self.points > MAX_POINTS:
            errors.append(f"points must be at most {MAX_POINTS}")

        # Validate RBW if specified
        if self.rbw_khz is not None:
            if self.rbw_khz < MIN_RBW_KHZ:
                errors.append(
                    f"rbw_khz must be at least {MIN_RBW_KHZ} kHz ({MIN_RBW_KHZ * 1000:.0f} Hz)"
                )
            if self.rbw_khz > MAX_RBW_KHZ:
                errors.append(f"rbw_khz must be at most {MAX_RBW_KHZ} kHz")

            # Check if RBW is close to a valid value (within 10% tolerance)
            # This allows for slight variations in user input
            if not any(abs(self.rbw_khz - valid) / valid < 0.1 for valid in VALID_RBW_VALUES_KHZ):
                valid_str = ", ".join(str(v) for v in VALID_RBW_VALUES_KHZ)
                errors.append(f"rbw_khz should be one of the valid values: {valid_str} kHz")

        return errors

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanConfig:
        """Create config from dictionary.

        Args:
            data: Dictionary with scan configuration

        Returns:
            ScanConfig instance

        Raises:
            ScanConfigError: If configuration is invalid
        """
        # Convert rbw_khz to float if provided (handles string values from JSON)
        rbw_khz_raw = data.get("rbw_khz")
        rbw_khz = float(rbw_khz_raw) if rbw_khz_raw is not None else None

        config = cls(
            start_freq_hz=int(data["start_freq_hz"]),
            stop_freq_hz=int(data["stop_freq_hz"]),
            points=int(data.get("points", 450)),
            rbw_khz=rbw_khz,
        )

        # Validate the config
        errors = config.validate()
        if errors:
            raise ScanConfigError("; ".join(errors))

        return config


class ScanSession:
    """Manages a single scan session for a WebSocket client.

    Handles starting, stopping, and streaming scan data to the client.
    """

    def __init__(
        self,
        websocket: WebSocket,
        send_callback: Callable[[dict[str, Any]], Any],
        tinysa: TinySA | None = None,
    ) -> None:
        """Initialize a scan session.

        Args:
            websocket: The WebSocket connection for this session
            send_callback: Async callback to send messages to the client
            tinysa: TinySA instance to use (defaults to singleton)
        """
        self._websocket = websocket
        self._send = send_callback
        self._tinysa = tinysa or get_tinysa()
        self._scanning = False
        self._cancel_requested = False
        self._current_task: asyncio.Task | None = None

    @property
    def is_scanning(self) -> bool:
        """Check if a scan is currently in progress."""
        return self._scanning

    async def start_scan(self, config: ScanConfig) -> None:
        """Start a new scan with the given configuration.

        Args:
            config: Scan configuration parameters
        """
        logger.info(
            f"Starting scan: range={config.start_freq_hz / 1e6:.3f}-{config.stop_freq_hz / 1e6:.3f} MHz, "
            f"points={config.points}, rbw={config.rbw_khz} kHz"
        )

        if self._scanning:
            logger.warning("Cannot start scan: scan already in progress")
            await self._send({"type": "error", "message": "Scan already in progress"})
            return

        self._scanning = True
        self._cancel_requested = False

        try:
            # Check device connection
            if not self._tinysa.is_connected:
                logger.error("Cannot start scan: TinySA device not connected")
                await self._send({"type": "error", "message": "TinySA device not connected"})
                return

            # Set RBW if specified
            if config.rbw_khz is not None:
                logger.debug(f"Setting RBW to {config.rbw_khz} kHz")
                try:
                    await self._tinysa.set_rbw(config.rbw_khz)
                except (TinySAConnectionError, TinySACommandError) as e:
                    logger.error(f"Failed to set RBW: {e}")
                    await self._send({"type": "error", "message": f"Failed to set RBW: {e}"})
                    return

            logger.debug("Scan started, streaming data points")
            # Notify client that scan is starting
            await self._send({"type": "scan_started", "config": config.to_dict()})

            # Run the scan and stream points
            point_count = 0
            try:
                async for freq_hz, amplitude_dbm in self._tinysa.scan_raw(
                    start_hz=config.start_freq_hz,
                    stop_hz=config.stop_freq_hz,
                    points=config.points,
                ):
                    # Check for cancellation
                    if self._cancel_requested:
                        await self._send({"type": "scan_stopped"})
                        logger.info("Scan cancelled by user")
                        return

                    # Send the data point
                    await self._send(
                        {
                            "type": "scan_point",
                            "index": point_count,
                            "frequency_hz": freq_hz,
                            "amplitude_dbm": round(amplitude_dbm, 2),
                        }
                    )
                    point_count += 1

                # Scan completed successfully
                await self._send({"type": "scan_completed", "total_points": point_count})
                logger.info(f"Scan completed: {point_count} points")

            except (TinySAConnectionError, TinySACommandError) as e:
                logger.error(f"Scan error: {e}")
                await self._send({"type": "error", "message": f"Scan failed: {e}"})

        finally:
            self._scanning = False
            self._cancel_requested = False

    async def stop_scan(self) -> None:
        """Request to stop the current scan."""
        if self._scanning:
            self._cancel_requested = True
            logger.info("Scan stop requested")
        else:
            await self._send({"type": "error", "message": "No scan in progress"})


class ScanService:
    """Service for managing scan sessions across WebSocket connections.

    Maintains a mapping of WebSocket connections to scan sessions and
    coordinates scanning operations.
    """

    def __init__(self) -> None:
        """Initialize the scan service."""
        self._sessions: dict[WebSocket, ScanSession] = {}

    def get_session(
        self,
        websocket: WebSocket,
        send_callback: Callable[[dict[str, Any]], Any],
    ) -> ScanSession:
        """Get or create a scan session for a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            send_callback: Callback for sending messages to the client

        Returns:
            The scan session for this connection
        """
        if websocket not in self._sessions:
            self._sessions[websocket] = ScanSession(websocket, send_callback)
            logger.debug(f"Created new scan session, total active sessions: {len(self._sessions)}")
        return self._sessions[websocket]

    def remove_session(self, websocket: WebSocket) -> None:
        """Remove a scan session when a WebSocket disconnects.

        Args:
            websocket: The disconnected WebSocket
        """
        if websocket in self._sessions:
            session = self._sessions.pop(websocket)
            # Request stop if scan is in progress
            if session.is_scanning:
                session._cancel_requested = True
                logger.info("Cancelling in-progress scan due to session removal")
            logger.debug(f"Scan session removed, remaining active sessions: {len(self._sessions)}")

    @property
    def active_session_count(self) -> int:
        """Get the number of active scan sessions."""
        return len(self._sessions)


# Singleton instance for application-wide use
_scan_service: ScanService | None = None


def get_scan_service() -> ScanService:
    """Get the singleton ScanService instance.

    Returns:
        The global ScanService instance
    """
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService()
    return _scan_service
