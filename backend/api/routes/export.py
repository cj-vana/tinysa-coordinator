"""
Export API routes for downloading scan data in various formats.

Endpoints:
- GET /api/export/{scan_id}/wwb - Shure Wireless Workbench format
- GET /api/export/{scan_id}/wsm - Sennheiser WSM format
- GET /api/export/{scan_id}/raw - Raw CSV with metadata
- GET /api/export/{scan_id}/json - Full JSON export
"""

from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.exceptions import ExportDataError, ExportFormatError, ScanNotFoundError
from backend.db.database import get_async_session
from backend.db.models import SavedScan
from backend.services.export_service import (
    format_json_export,
    format_raw_csv,
    format_wsm_csv,
    format_wwb_csv,
    get_content_type,
    get_export_filename,
)

router = APIRouter(prefix="/export", tags=["export"])

ExportFormat = Literal["wwb", "wsm", "raw", "json"]


async def get_scan_with_data(
    scan_id: int, session: AsyncSession
) -> SavedScan:
    """
    Retrieve a scan with all its data points.
    Raises 404 if not found.
    """
    stmt = (
        select(SavedScan)
        .where(SavedScan.id == scan_id)
        .options(selectinload(SavedScan.data_points))
    )
    result = await session.execute(stmt)
    scan = result.scalar_one_or_none()

    if not scan:
        raise ScanNotFoundError(scan_id=scan_id)

    if not scan.data_points:
        raise ExportDataError(
            message=f"Scan {scan_id} has no data points to export",
            scan_id=scan_id,
        )

    return scan


@router.get("/{scan_id}/wwb")
async def export_wwb(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export scan data in Shure Wireless Workbench (WWB) format.

    Format:
    - 2 columns: frequency (MHz), amplitude (dBm)
    - NO headers
    - Comma-separated values
    """
    scan = await get_scan_with_data(scan_id, session)

    content = format_wwb_csv(scan)
    filename = get_export_filename(scan, "wwb")

    return StreamingResponse(
        iter([content]),
        media_type=get_content_type("wwb"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{scan_id}/wsm")
async def export_wsm(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export scan data in Sennheiser WSM format.

    Format:
    - Semicolon delimiter
    - Header row: Frequency MHz;Level dBm
    - 3 decimal places for frequency
    """
    scan = await get_scan_with_data(scan_id, session)

    content = format_wsm_csv(scan)
    filename = get_export_filename(scan, "wsm")

    return StreamingResponse(
        iter([content]),
        media_type=get_content_type("wsm"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{scan_id}/raw")
async def export_raw(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export scan data in raw CSV format with full metadata.

    Format:
    - Metadata as comment lines (# prefix)
    - Headers: Index,Frequency_Hz,Frequency_MHz,Amplitude_dBm
    - Full precision for all values
    """
    scan = await get_scan_with_data(scan_id, session)

    content = format_raw_csv(scan)
    filename = get_export_filename(scan, "raw")

    return StreamingResponse(
        iter([content]),
        media_type=get_content_type("raw"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{scan_id}/json")
async def export_json(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export scan data as JSON with full structured metadata.

    Returns a JSON document containing:
    - Scan parameters and metadata
    - All data points with frequencies and amplitudes
    - Export information
    """
    scan = await get_scan_with_data(scan_id, session)

    content = format_json_export(scan)
    filename = get_export_filename(scan, "json")

    return StreamingResponse(
        iter([content]),
        media_type=get_content_type("json"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{scan_id}/{format}")
async def export_generic(
    scan_id: int,
    format: ExportFormat,
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Generic export endpoint that routes to the appropriate format handler.

    Supported formats:
    - wwb: Shure Wireless Workbench
    - wsm: Sennheiser WSM
    - raw: Raw CSV with metadata
    - json: Full JSON export
    """
    # Route to appropriate handler
    handlers = {
        "wwb": export_wwb,
        "wsm": export_wsm,
        "raw": export_raw,
        "json": export_json,
    }

    if format not in handlers:
        raise ExportFormatError(
            message=f"Unknown export format: {format}",
            requested_format=format,
            supported_formats=["wwb", "wsm", "raw", "json"],
        )

    return await handlers[format](scan_id, session)
