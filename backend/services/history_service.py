"""
Service layer for scan history operations.

Provides async database operations for managing saved scans.
"""

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import SavedScan, ScanDataPoint
from backend.schemas.scan import SavedScanCreate, SavedScanUpdate

logger = logging.getLogger(__name__)


async def list_scans(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
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
    logger.debug(f"Listing scans: limit={limit}, offset={offset}, search={search}")

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
        logger.debug(f"Applied search filter: {search}")

    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(SavedScan.created_at.desc()).offset(offset).limit(limit)

    # Execute and return results
    result = await session.execute(query)
    scans = list(result.scalars().all())

    logger.debug(f"Retrieved {len(scans)} scans (total matching: {total})")
    return scans, total


async def get_scan_by_id(
    session: AsyncSession,
    scan_id: int,
    include_data_points: bool = True,
) -> SavedScan | None:
    """
    Get a single scan by ID.

    Args:
        session: Database session
        scan_id: ID of the scan to retrieve
        include_data_points: Whether to load data points (default True)

    Returns:
        The scan if found, None otherwise
    """
    logger.debug(f"Fetching scan: id={scan_id}, include_data_points={include_data_points}")

    query = select(SavedScan).where(SavedScan.id == scan_id)

    if include_data_points:
        query = query.options(selectinload(SavedScan.data_points))

    result = await session.execute(query)
    scan = result.scalar_one_or_none()

    if scan:
        logger.debug(f"Found scan: id={scan_id}, name={scan.name}")
    else:
        logger.debug(f"Scan not found: id={scan_id}")

    return scan


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
    count = result.scalar() or 0
    logger.debug(f"Scan {scan_id} has {count} data points")
    return count


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
    logger.info(
        f"Creating scan: name={scan_data.name}, "
        f"range={scan_data.start_freq_hz}-{scan_data.stop_freq_hz} Hz, "
        f"points={len(scan_data.data_points)}"
    )

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

    logger.debug(f"Created scan record: id={scan.id}")

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

    logger.info(
        f"Saved scan: id={scan.id}, name={scan.name}, data_points={len(scan_data.data_points)}"
    )

    # Reload with data points
    return await get_scan_by_id(session, scan.id, include_data_points=True)


async def update_scan(
    session: AsyncSession,
    scan_id: int,
    update_data: SavedScanUpdate,
) -> SavedScan | None:
    """
    Update scan metadata.

    Args:
        session: Database session
        scan_id: ID of the scan to update
        update_data: Fields to update

    Returns:
        The updated scan if found, None otherwise
    """
    logger.debug(f"Updating scan: id={scan_id}")

    scan = await get_scan_by_id(session, scan_id, include_data_points=False)
    if not scan:
        logger.warning(f"Cannot update scan: id={scan_id} not found")
        return None

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    updated_fields = list(update_dict.keys())
    for field, value in update_dict.items():
        setattr(scan, field, value)

    await session.flush()

    logger.info(f"Updated scan: id={scan_id}, fields={updated_fields}")
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
    logger.debug(f"Deleting scan: id={scan_id}")

    scan = await get_scan_by_id(session, scan_id, include_data_points=False)
    if not scan:
        logger.warning(f"Cannot delete scan: id={scan_id} not found")
        return False

    scan_name = scan.name
    await session.delete(scan)
    await session.flush()

    logger.info(f"Deleted scan: id={scan_id}, name={scan_name}")
    return True
