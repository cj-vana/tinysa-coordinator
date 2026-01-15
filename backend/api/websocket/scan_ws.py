"""WebSocket endpoint for real-time scan streaming.

Handles WebSocket connections at /ws/scan for streaming spectrum scan
data in real-time from the TinySA device to connected clients.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from backend.core.connection_manager import get_connection_manager
from backend.services.scan_service import ScanConfig, get_scan_service

logger = logging.getLogger(__name__)


async def scan_websocket(websocket: WebSocket) -> None:
    """Handle WebSocket connections for real-time scan streaming.

    This endpoint accepts WebSocket connections and handles JSON messages
    for controlling spectrum scans on the TinySA device.

    Incoming messages:
        - {action: 'start_scan', config: {start_freq_hz, stop_freq_hz, points, rbw_khz}}
        - {action: 'stop_scan'}

    Outgoing messages:
        - {type: 'scan_started', config: {...}}
        - {type: 'scan_point', index, frequency_hz, amplitude_dbm}
        - {type: 'scan_completed', total_points}
        - {type: 'scan_stopped'}
        - {type: 'error', message}

    Args:
        websocket: The WebSocket connection
    """
    connection_manager = get_connection_manager()
    scan_service = get_scan_service()

    await connection_manager.connect(websocket)

    async def send_message(data: dict[str, Any]) -> None:
        """Send a JSON message to the WebSocket client."""
        await connection_manager.send_json(websocket, data)

    # Create a scan session for this connection
    session = scan_service.get_session(websocket, send_message)

    try:
        while True:
            # Wait for incoming message
            try:
                raw_data = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break

            # Parse JSON message
            try:
                message = json.loads(raw_data)
            except json.JSONDecodeError as e:
                await send_message({
                    "type": "error",
                    "message": f"Invalid JSON: {e}"
                })
                continue

            # Handle different actions
            action = message.get("action")

            if action == "start_scan":
                config_data = message.get("config", {})

                # Validate required fields
                required = ["start_freq_hz", "stop_freq_hz"]
                missing = [f for f in required if f not in config_data]
                if missing:
                    await send_message({
                        "type": "error",
                        "message": f"Missing required fields: {', '.join(missing)}"
                    })
                    continue

                # Validate frequency range
                try:
                    start_freq = int(config_data["start_freq_hz"])
                    stop_freq = int(config_data["stop_freq_hz"])
                    if start_freq >= stop_freq:
                        await send_message({
                            "type": "error",
                            "message": "start_freq_hz must be less than stop_freq_hz"
                        })
                        continue
                    if start_freq < 0:
                        await send_message({
                            "type": "error",
                            "message": "start_freq_hz must be positive"
                        })
                        continue
                except (ValueError, TypeError) as e:
                    await send_message({
                        "type": "error",
                        "message": f"Invalid frequency value: {e}"
                    })
                    continue

                # Create scan config
                try:
                    config = ScanConfig.from_dict(config_data)
                except (ValueError, KeyError) as e:
                    await send_message({
                        "type": "error",
                        "message": f"Invalid scan config: {e}"
                    })
                    continue

                # Start the scan
                await session.start_scan(config)

            elif action == "stop_scan":
                await session.stop_scan()

            else:
                await send_message({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await send_message({
                "type": "error",
                "message": f"Internal server error: {e}"
            })
        except Exception:
            pass  # Client may already be disconnected

    finally:
        # Clean up on disconnect
        scan_service.remove_session(websocket)
        connection_manager.disconnect(websocket)
