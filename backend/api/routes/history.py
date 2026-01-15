"""
API routes for scan history management.

Provides endpoints for listing, viewing, creating, updating, and deleting saved scans.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_async_session
from backend.schemas.scan import (
    SavedScanCreate,
    SavedScanDetail,
    SavedScanList,
    SavedScanResponse,
    SavedScanSummary,
    SavedScanUpdate,
    ScanDataPointResponse,
)
from backend.services import history_service

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=SavedScanList)
async def list_scans(
    limit: int = Query(default=20, ge=1, le=100, description="Number of scans to return"),
    offset: int = Query(default=0, ge=0, description="Number of scans to skip"),
    search: Optional[str] = Query(
        default=None, min_length=1, max_length=100, description="Search name or location"
    ),
    session: AsyncSession = Depends(get_async_session),
) -> SavedScanList:
    """
    List saved scans with pagination.

    Returns scans ordered by creation date (newest first).
    Optionally filter by search term matching name or location.
    """
    scans, total = await history_service.list_scans(
        session=session,
        limit=limit,
        offset=offset,
        search=search,
    )

    # Convert to summary format
    items = [
        SavedScanSummary(
            id=scan.id,
            name=scan.name,
            start_freq_hz=scan.start_freq_hz,
            stop_freq_hz=scan.stop_freq_hz,
            points=scan.points,
            preset_name=scan.preset_name,
            location=scan.location,
            scan_completed_at=scan.scan_completed_at,
            created_at=scan.created_at,
        )
        for scan in scans
    ]

    return SavedScanList(
        items=items,
        total=total,
        page=(offset // limit) + 1 if limit > 0 else 1,
        per_page=limit,
    )


@router.get("/{scan_id}", response_model=SavedScanDetail)
async def get_scan(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> SavedScanDetail:
    """
    Get a single scan with all its data points.

    Returns full scan details including the complete data point array.
    """
    scan = await history_service.get_scan_by_id(
        session=session,
        scan_id=scan_id,
        include_data_points=True,
    )

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Build response with data points
    data_points = [
        ScanDataPointResponse(
            id=dp.id,
            scan_id=dp.scan_id,
            index=dp.index,
            frequency_hz=dp.frequency_hz,
            amplitude_dbm=dp.amplitude_dbm,
        )
        for dp in (scan.data_points or [])
    ]

    return SavedScanDetail(
        id=scan.id,
        name=scan.name,
        start_freq_hz=scan.start_freq_hz,
        stop_freq_hz=scan.stop_freq_hz,
        points=scan.points,
        rbw_khz=scan.rbw_khz,
        preset_id=scan.preset_id,
        preset_name=scan.preset_name,
        location=scan.location,
        notes=scan.notes,
        tags=scan.tags,
        scan_started_at=scan.scan_started_at,
        scan_completed_at=scan.scan_completed_at,
        created_at=scan.created_at,
        data_point_count=len(data_points),
        data_points=data_points,
    )


@router.post("/", response_model=SavedScanDetail, status_code=201)
async def create_scan(
    scan_data: SavedScanCreate,
    session: AsyncSession = Depends(get_async_session),
) -> SavedScanDetail:
    """
    Save a new scan with its data points.

    Receives the complete scan data including all measurement points.
    """
    scan = await history_service.create_scan(
        session=session,
        scan_data=scan_data,
    )

    # Build response with data points
    data_points = [
        ScanDataPointResponse(
            id=dp.id,
            scan_id=dp.scan_id,
            index=dp.index,
            frequency_hz=dp.frequency_hz,
            amplitude_dbm=dp.amplitude_dbm,
        )
        for dp in (scan.data_points or [])
    ]

    return SavedScanDetail(
        id=scan.id,
        name=scan.name,
        start_freq_hz=scan.start_freq_hz,
        stop_freq_hz=scan.stop_freq_hz,
        points=scan.points,
        rbw_khz=scan.rbw_khz,
        preset_id=scan.preset_id,
        preset_name=scan.preset_name,
        location=scan.location,
        notes=scan.notes,
        tags=scan.tags,
        scan_started_at=scan.scan_started_at,
        scan_completed_at=scan.scan_completed_at,
        created_at=scan.created_at,
        data_point_count=len(data_points),
        data_points=data_points,
    )


@router.put("/{scan_id}", response_model=SavedScanResponse)
async def update_scan(
    scan_id: int,
    update_data: SavedScanUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> SavedScanResponse:
    """
    Update scan metadata.

    Only updates provided fields (name, location, notes, tags).
    Does not modify scan data points.
    """
    scan = await history_service.update_scan(
        session=session,
        scan_id=scan_id,
        update_data=update_data,
    )

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Get data point count
    data_point_count = await history_service.get_scan_data_point_count(
        session=session,
        scan_id=scan_id,
    )

    return SavedScanResponse.from_orm_with_count(scan, data_point_count)


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete a saved scan and all its data points.

    This action is irreversible.
    """
    deleted = await history_service.delete_scan(
        session=session,
        scan_id=scan_id,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found")
