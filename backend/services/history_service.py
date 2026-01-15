"""
Service layer for scan history operations.

Provides async database operations for managing saved scans.
"""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import SavedScan, ScanDataPoint
from backend.schemas.scan import SavedScanCreate, SavedScanUpdate


async def list_scans(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
) -> tuple[list[SavedScan], int]:
    """
    List saved scans with pagination, optionally filtered by search term.

    Args:
        session: Database session
        limit: Maximum number of results to return
        offset: Number of results to skip
        search: Optional search term for name or location

    Returns:
        Tuple of (list of scans, total count)
    """
    # Build base query
    query = select(SavedScan)

    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                SavedScan.name.ilike(search_pattern),
                SavedScan.location.ilike(search_pattern),
            )
        )

    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(SavedScan.created_at.desc()).offset(offset).limit(limit)

    # Execute and return results
    result = await session.execute(query)
    scans = list(result.scalars().all())

    return scans, total


async def get_scan_by_id(
    session: AsyncSession,
    scan_id: int,
    include_data_points: bool = True,
) -> Optional[SavedScan]:
    """
    Get a single scan by ID.

    Args:
        session: Database session
        scan_id: ID of the scan to retrieve
        include_data_points: Whether to load data points (default True)

    Returns:
        The scan if found, None otherwise
    """
    query = select(SavedScan).where(SavedScan.id == scan_id)

    if include_data_points:
        query = query.options(selectinload(SavedScan.data_points))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_scan_data_point_count(
    session: AsyncSession,
    scan_id: int,
) -> int:
    """
    Get the count of data points for a scan.

    Args:
        session: Database session
        scan_id: ID of the scan

    Returns:
        Number of data points
    """
    query = select(func.count()).where(ScanDataPoint.scan_id == scan_id)
    result = await session.execute(query)
    return result.scalar() or 0


async def create_scan(
    session: AsyncSession,
    scan_data: SavedScanCreate,
) -> SavedScan:
    """
    Create a new scan with data points.

    Args:
        session: Database session
        scan_data: Scan creation data including data points

    Returns:
        The created scan
    """
    # Create the scan record
    scan = SavedScan(
        name=scan_data.name,
        start_freq_hz=scan_data.start_freq_hz,
        stop_freq_hz=scan_data.stop_freq_hz,
        points=scan_data.points,
        rbw_khz=scan_data.rbw_khz,
        preset_id=scan_data.preset_id,
        preset_name=scan_data.preset_name,
        location=scan_data.location,
        notes=scan_data.notes,
        tags=scan_data.tags,
        scan_started_at=scan_data.scan_started_at,
        scan_completed_at=scan_data.scan_completed_at,
    )

    session.add(scan)
    await session.flush()  # Get the scan ID

    # Create data points
    for dp in scan_data.data_points:
        data_point = ScanDataPoint(
            scan_id=scan.id,
            index=dp.index,
            frequency_hz=dp.frequency_hz,
            amplitude_dbm=dp.amplitude_dbm,
        )
        session.add(data_point)

    await session.flush()

    # Reload with data points
    return await get_scan_by_id(session, scan.id, include_data_points=True)


async def update_scan(
    session: AsyncSession,
    scan_id: int,
    update_data: SavedScanUpdate,
) -> Optional[SavedScan]:
    """
    Update scan metadata.

    Args:
        session: Database session
        scan_id: ID of the scan to update
        update_data: Fields to update

    Returns:
        The updated scan if found, None otherwise
    """
    scan = await get_scan_by_id(session, scan_id, include_data_points=False)
    if not scan:
        return None

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(scan, field, value)

    await session.flush()

    return scan


async def delete_scan(
    session: AsyncSession,
    scan_id: int,
) -> bool:
    """
    Delete a scan and its data points.

    Args:
        session: Database session
        scan_id: ID of the scan to delete

    Returns:
        True if deleted, False if not found
    """
    scan = await get_scan_by_id(session, scan_id, include_data_points=False)
    if not scan:
        return False

    await session.delete(scan)
    await session.flush()

    return True
