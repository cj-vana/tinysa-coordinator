"""
Export service for scan data in various formats.

Supports:
- Shure Wireless Workbench (WWB) CSV format
- Sennheiser WSM CSV format
- Raw CSV with full metadata
- JSON with structured data
"""

import json
import logging
from datetime import datetime
from io import StringIO
from typing import AsyncGenerator

from backend.db.models import SavedScan

logger = logging.getLogger(__name__)


def format_wwb_csv(scan: SavedScan) -> str:
    """
    Format scan data as Shure Wireless Workbench CSV.

    Format:
    - 2 columns: frequency (MHz), amplitude (dBm)
    - NO headers
    - 6 decimal places for frequency
    - 1 decimal place for amplitude

    Example output:
        470.100000,-42.1
        470.150000,-45.3
    """
    logger.debug(f"Formatting scan {scan.id} as WWB CSV")
    output = StringIO()

    for point in scan.data_points:
        freq_mhz = point.frequency_hz / 1_000_000
        output.write(f"{freq_mhz:.6f},{point.amplitude_dbm:.1f}\n")

    result = output.getvalue()
    logger.info(
        f"Exported scan id={scan.id} to WWB format: "
        f"{len(scan.data_points)} points, {len(result)} bytes"
    )
    return result


def format_wsm_csv(scan: SavedScan) -> str:
    """
    Format scan data as Sennheiser WSM CSV.

    Format:
    - Semicolon delimiter
    - Header row: Frequency MHz;Level dBm
    - 3 decimal places for frequency
    - 1 decimal place for amplitude

    Example output:
        Frequency MHz;Level dBm
        470.100;-42.1
        470.150;-45.3
    """
    logger.debug(f"Formatting scan {scan.id} as WSM CSV")
    output = StringIO()

    # Header row
    output.write("Frequency MHz;Level dBm\n")

    for point in scan.data_points:
        freq_mhz = point.frequency_hz / 1_000_000
        output.write(f"{freq_mhz:.3f};{point.amplitude_dbm:.1f}\n")

    result = output.getvalue()
    logger.info(
        f"Exported scan id={scan.id} to WSM format: "
        f"{len(scan.data_points)} points, {len(result)} bytes"
    )
    return result


def format_raw_csv(scan: SavedScan) -> str:
    """
    Format scan data as raw CSV with full metadata.

    Format:
    - Metadata as comment lines (# prefix)
    - Full headers with columns: Index,Frequency_Hz,Frequency_MHz,Amplitude_dBm
    - High precision for all values

    Example output:
        # Scan Name: UHF Survey
        # Scan Timestamp: 2024-01-15T10:30:00
        # Location: Studio A
        # Frequency Range: 470.000000 - 698.000000 MHz
        # Points: 450
        # RBW: 10.0 kHz
        Index,Frequency_Hz,Frequency_MHz,Amplitude_dBm
        0,470000000,470.000000,-42.1
        1,470500000,470.500000,-45.3
    """
    logger.debug(f"Formatting scan {scan.id} as raw CSV with metadata")
    output = StringIO()

    # Metadata comments
    output.write(f"# Scan Name: {scan.name}\n")

    if scan.scan_completed_at:
        timestamp = scan.scan_completed_at.isoformat()
    elif scan.scan_started_at:
        timestamp = scan.scan_started_at.isoformat()
    else:
        timestamp = scan.created_at.isoformat()
    output.write(f"# Scan Timestamp: {timestamp}\n")

    if scan.location:
        output.write(f"# Location: {scan.location}\n")

    start_mhz = scan.start_freq_hz / 1_000_000
    stop_mhz = scan.stop_freq_hz / 1_000_000
    output.write(f"# Frequency Range: {start_mhz:.6f} - {stop_mhz:.6f} MHz\n")
    output.write(f"# Points: {scan.points}\n")

    if scan.rbw_khz:
        output.write(f"# RBW: {scan.rbw_khz:.1f} kHz\n")

    if scan.preset_name:
        output.write(f"# Preset: {scan.preset_name}\n")

    if scan.notes:
        # Handle multi-line notes by prefixing each line
        for line in scan.notes.split("\n"):
            output.write(f"# Notes: {line}\n")

    if scan.tags:
        output.write(f"# Tags: {scan.tags}\n")

    # Header row
    output.write("Index,Frequency_Hz,Frequency_MHz,Amplitude_dBm\n")

    # Data rows
    for point in scan.data_points:
        freq_mhz = point.frequency_hz / 1_000_000
        output.write(f"{point.index},{point.frequency_hz},{freq_mhz:.6f},{point.amplitude_dbm:.1f}\n")

    result = output.getvalue()
    logger.info(
        f"Exported scan id={scan.id} to raw CSV format: "
        f"{len(scan.data_points)} points, {len(result)} bytes"
    )
    return result


def format_json_export(scan: SavedScan) -> str:
    """
    Format scan data as JSON with full metadata.

    Returns a structured JSON document with all scan information.
    """
    logger.debug(f"Formatting scan {scan.id} as JSON")
    data = {
        "scan": {
            "id": scan.id,
            "name": scan.name,
            "parameters": {
                "start_freq_hz": scan.start_freq_hz,
                "stop_freq_hz": scan.stop_freq_hz,
                "start_freq_mhz": scan.start_freq_hz / 1_000_000,
                "stop_freq_mhz": scan.stop_freq_hz / 1_000_000,
                "points": scan.points,
                "rbw_khz": scan.rbw_khz,
            },
            "metadata": {
                "location": scan.location,
                "notes": scan.notes,
                "tags": scan.tag_list,
                "preset_id": scan.preset_id,
                "preset_name": scan.preset_name,
            },
            "timing": {
                "scan_started_at": scan.scan_started_at.isoformat() if scan.scan_started_at else None,
                "scan_completed_at": scan.scan_completed_at.isoformat() if scan.scan_completed_at else None,
                "created_at": scan.created_at.isoformat(),
                "duration_seconds": scan.duration_seconds,
            },
        },
        "data": [
            {
                "index": point.index,
                "frequency_hz": point.frequency_hz,
                "frequency_mhz": point.frequency_hz / 1_000_000,
                "amplitude_dbm": point.amplitude_dbm,
            }
            for point in scan.data_points
        ],
        "export_info": {
            "format": "json",
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_points": len(scan.data_points),
        },
    }

    result = json.dumps(data, indent=2)
    logger.info(
        f"Exported scan id={scan.id} to JSON format: "
        f"{len(scan.data_points)} points, {len(result)} bytes"
    )
    return result


async def generate_wwb_stream(scan: SavedScan) -> AsyncGenerator[str, None]:
    """
    Generate WWB CSV as a stream for large exports.
    Yields chunks of CSV data.
    """
    logger.debug(f"Streaming scan {scan.id} as WWB CSV")
    for point in scan.data_points:
        freq_mhz = point.frequency_hz / 1_000_000
        yield f"{freq_mhz:.6f},{point.amplitude_dbm:.1f}\n"


async def generate_wsm_stream(scan: SavedScan) -> AsyncGenerator[str, None]:
    """
    Generate WSM CSV as a stream for large exports.
    Yields chunks of CSV data.
    """
    logger.debug(f"Streaming scan {scan.id} as WSM CSV")
    yield "Frequency MHz;Level dBm\n"

    for point in scan.data_points:
        freq_mhz = point.frequency_hz / 1_000_000
        yield f"{freq_mhz:.3f};{point.amplitude_dbm:.1f}\n"


def get_export_filename(scan: SavedScan, format_type: str) -> str:
    """
    Generate a safe filename for the export.

    Args:
        scan: The scan being exported
        format_type: One of 'wwb', 'wsm', 'raw', 'json'

    Returns:
        A sanitized filename with appropriate extension
    """
    # Sanitize the scan name for use in filename
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in scan.name)
    safe_name = safe_name.strip().replace(" ", "_")

    # Limit filename length
    if len(safe_name) > 100:
        safe_name = safe_name[:100]

    # Apply format-specific suffix
    suffixes = {
        "wwb": "_wwb.csv",
        "wsm": "_wsm.csv",
        "raw": "_raw.csv",
        "json": ".json",
    }

    suffix = suffixes.get(format_type, ".csv")
    filename = f"{safe_name}{suffix}"
    logger.debug(f"Generated export filename: {filename}")
    return filename


def get_content_type(format_type: str) -> str:
    """
    Get the appropriate MIME type for the export format.
    """
    if format_type == "json":
        return "application/json"
    return "text/csv"
