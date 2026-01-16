"""
Tests for the export API endpoints.

Tests cover all export formats:
- WWB (Shure Wireless Workbench)
- WSM (Sennheiser WSM)
- Raw CSV with metadata
- JSON export

Also tests error cases for invalid scan IDs and scans without data.
"""

import json
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.database import Base, get_async_session
from backend.db.models import SavedScan, ScanDataPoint
from backend.main import app


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def export_client_with_scan() -> AsyncGenerator[tuple[AsyncClient, int], None]:
    """
    Create a client and scan with data using a file-based test database.

    Uses a temporary file-based SQLite database to ensure data persistence
    across different sessions within the same test.
    """
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_async_engine(db_url, echo=False)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create scan and data points
        async with async_session_maker() as session:
            scan = SavedScan(
                name="Test Export Scan",
                start_freq_hz=470_000_000,
                stop_freq_hz=698_000_000,
                points=10,
                rbw_khz=100.0,
                location="Test Studio",
                notes="Test scan for export",
                tags="test,export",
                preset_name="Test Preset",
            )
            session.add(scan)
            await session.flush()

            # Add data points
            freq_step = (698_000_000 - 470_000_000) / 9
            for i in range(10):
                freq_hz = int(470_000_000 + (i * freq_step))
                point = ScanDataPoint(
                    scan_id=scan.id,
                    index=i,
                    frequency_hz=freq_hz,
                    amplitude_dbm=-100.0 + (i * 2.0),
                )
                session.add(point)

            await session.commit()
            scan_id = scan.id

        async def _get_session_override() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_async_session] = _get_session_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, scan_id

        app.dependency_overrides.clear()
        await engine.dispose()

    finally:
        # Clean up the temp file
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def export_client_with_empty_scan() -> AsyncGenerator[tuple[AsyncClient, int], None]:
    """
    Create a client and scan without data points using a file-based test database.
    """
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_async_engine(db_url, echo=False)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create scan without data points
        async with async_session_maker() as session:
            scan = SavedScan(
                name="Empty Scan",
                start_freq_hz=470_000_000,
                stop_freq_hz=698_000_000,
                points=10,
            )
            session.add(scan)
            await session.commit()
            scan_id = scan.id

        async def _get_session_override() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_async_session] = _get_session_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, scan_id

        app.dependency_overrides.clear()
        await engine.dispose()

    finally:
        # Clean up the temp file
        Path(db_path).unlink(missing_ok=True)


# ============================================================================
# WWB Export Tests
# ============================================================================


@pytest.mark.unit
async def test_export_wwb_success(export_client_with_scan):
    """Test WWB export returns valid CSV data."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wwb")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "_wwb.csv" in response.headers["content-disposition"]

    # Parse the CSV content
    content = response.text
    lines = content.strip().split("\n")

    # WWB format has no headers, just data
    assert len(lines) == 10  # 10 data points

    # Verify first line format: freq_mhz,amplitude_dbm
    first_line = lines[0].split(",")
    assert len(first_line) == 2
    freq_mhz = float(first_line[0])
    amplitude_dbm = float(first_line[1])

    # Verify frequency is in MHz with 6 decimal places
    assert 470.0 <= freq_mhz <= 698.0
    # Verify amplitude is reasonable
    assert -120.0 <= amplitude_dbm <= 0.0


@pytest.mark.unit
async def test_export_wwb_format_precision(export_client_with_scan):
    """Test WWB export uses correct number of decimal places."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wwb")

    assert response.status_code == 200
    content = response.text
    lines = content.strip().split("\n")

    for line in lines:
        parts = line.split(",")
        freq_str = parts[0]
        amp_str = parts[1]

        # Frequency should have 6 decimal places
        if "." in freq_str:
            decimal_part = freq_str.split(".")[1]
            assert len(decimal_part) == 6, f"Frequency should have 6 decimals: {freq_str}"

        # Amplitude should have 1 decimal place
        if "." in amp_str:
            decimal_part = amp_str.split(".")[1]
            assert len(decimal_part) == 1, f"Amplitude should have 1 decimal: {amp_str}"


# ============================================================================
# WSM Export Tests
# ============================================================================


@pytest.mark.unit
async def test_export_wsm_success(export_client_with_scan):
    """Test WSM export returns valid CSV data with headers."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wsm")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "_wsm.csv" in response.headers["content-disposition"]

    content = response.text
    lines = content.strip().split("\n")

    # WSM format has header row
    assert len(lines) == 11  # 1 header + 10 data points

    # Verify header
    assert lines[0] == "Frequency MHz;Level dBm"


@pytest.mark.unit
async def test_export_wsm_format_semicolon_delimiter(export_client_with_scan):
    """Test WSM export uses semicolon delimiter."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wsm")

    assert response.status_code == 200
    content = response.text
    lines = content.strip().split("\n")

    # Check all data lines use semicolon
    for line in lines[1:]:  # Skip header
        assert ";" in line
        assert "," not in line
        parts = line.split(";")
        assert len(parts) == 2


@pytest.mark.unit
async def test_export_wsm_format_precision(export_client_with_scan):
    """Test WSM export uses 3 decimal places for frequency."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wsm")

    assert response.status_code == 200
    content = response.text
    lines = content.strip().split("\n")

    for line in lines[1:]:  # Skip header
        parts = line.split(";")
        freq_str = parts[0]

        # Frequency should have 3 decimal places
        if "." in freq_str:
            decimal_part = freq_str.split(".")[1]
            assert len(decimal_part) == 3, f"Frequency should have 3 decimals: {freq_str}"


# ============================================================================
# Raw CSV Export Tests
# ============================================================================


@pytest.mark.unit
async def test_export_raw_success(export_client_with_scan):
    """Test raw CSV export includes metadata comments and headers."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "_raw.csv" in response.headers["content-disposition"]

    content = response.text
    lines = content.strip().split("\n")

    # Find metadata comments
    comment_lines = [line for line in lines if line.startswith("#")]
    assert len(comment_lines) > 0

    # Check for expected metadata
    metadata_content = "\n".join(comment_lines)
    assert "# Scan Name:" in metadata_content
    assert "# Frequency Range:" in metadata_content
    assert "# Points:" in metadata_content


@pytest.mark.unit
async def test_export_raw_has_headers(export_client_with_scan):
    """Test raw CSV export includes column headers."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 200
    content = response.text

    # Find header row (first non-comment line)
    lines = content.strip().split("\n")
    header_line = None
    for line in lines:
        if not line.startswith("#"):
            header_line = line
            break

    assert header_line is not None
    assert "Index" in header_line
    assert "Frequency_Hz" in header_line
    assert "Frequency_MHz" in header_line
    assert "Amplitude_dBm" in header_line


@pytest.mark.unit
async def test_export_raw_includes_location(export_client_with_scan):
    """Test raw CSV export includes location in metadata."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 200
    content = response.text

    assert "# Location: Test Studio" in content


@pytest.mark.unit
async def test_export_raw_data_format(export_client_with_scan):
    """Test raw CSV export data rows have correct format."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 200
    content = response.text
    lines = content.strip().split("\n")

    # Find data rows (after comments and header)
    data_lines = []
    found_header = False
    for line in lines:
        if line.startswith("#"):
            continue
        if not found_header:
            found_header = True  # Skip header
            continue
        data_lines.append(line)

    assert len(data_lines) == 10

    # Verify first data row
    first_row = data_lines[0].split(",")
    assert len(first_row) == 4  # Index, Frequency_Hz, Frequency_MHz, Amplitude_dBm
    assert first_row[0] == "0"  # First index


# ============================================================================
# JSON Export Tests
# ============================================================================


@pytest.mark.unit
async def test_export_json_success(export_client_with_scan):
    """Test JSON export returns valid JSON data."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert ".json" in response.headers["content-disposition"]

    # Parse JSON
    data = json.loads(response.text)

    # Verify structure
    assert "scan" in data
    assert "data" in data
    assert "export_info" in data


@pytest.mark.unit
async def test_export_json_scan_metadata(export_client_with_scan):
    """Test JSON export includes scan metadata."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 200
    data = json.loads(response.text)

    scan_info = data["scan"]
    assert scan_info["id"] == scan_id
    assert scan_info["name"] == "Test Export Scan"

    # Check parameters
    params = scan_info["parameters"]
    assert params["start_freq_hz"] == 470_000_000
    assert params["stop_freq_hz"] == 698_000_000
    assert params["points"] == 10
    assert params["rbw_khz"] == 100.0

    # Check metadata
    metadata = scan_info["metadata"]
    assert metadata["location"] == "Test Studio"
    assert metadata["notes"] == "Test scan for export"


@pytest.mark.unit
async def test_export_json_data_points(export_client_with_scan):
    """Test JSON export includes all data points with correct structure."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 200
    data = json.loads(response.text)

    data_points = data["data"]
    assert len(data_points) == 10

    # Verify first point structure
    first_point = data_points[0]
    assert "index" in first_point
    assert "frequency_hz" in first_point
    assert "frequency_mhz" in first_point
    assert "amplitude_dbm" in first_point

    assert first_point["index"] == 0
    assert first_point["frequency_hz"] == 470_000_000
    assert first_point["frequency_mhz"] == 470.0


@pytest.mark.unit
async def test_export_json_export_info(export_client_with_scan):
    """Test JSON export includes export metadata."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 200
    data = json.loads(response.text)

    export_info = data["export_info"]
    assert export_info["format"] == "json"
    assert export_info["version"] == "1.0"
    assert "exported_at" in export_info
    assert export_info["total_points"] == 10


# ============================================================================
# Generic Export Endpoint Tests
# ============================================================================


@pytest.mark.unit
async def test_export_generic_wwb(export_client_with_scan):
    """Test generic export endpoint routes to WWB handler."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wwb")

    assert response.status_code == 200
    assert "_wwb.csv" in response.headers["content-disposition"]


@pytest.mark.unit
async def test_export_generic_wsm(export_client_with_scan):
    """Test generic export endpoint routes to WSM handler."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wsm")

    assert response.status_code == 200
    assert "_wsm.csv" in response.headers["content-disposition"]


@pytest.mark.unit
async def test_export_generic_raw(export_client_with_scan):
    """Test generic export endpoint routes to raw handler."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 200
    assert "_raw.csv" in response.headers["content-disposition"]


@pytest.mark.unit
async def test_export_generic_json(export_client_with_scan):
    """Test generic export endpoint routes to JSON handler."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 200
    assert ".json" in response.headers["content-disposition"]


# ============================================================================
# Error Case Tests
# ============================================================================


@pytest.mark.unit
async def test_export_scan_not_found(client: AsyncClient):
    """Test export returns 404 for non-existent scan."""
    response = await client.get("/api/export/99999/wwb")

    assert response.status_code == 404
    data = response.json()
    # RFC 7807 format uses 'type' URL containing error code
    assert "resource_not_found" in data["type"]
    assert data["status"] == 404


@pytest.mark.unit
async def test_export_scan_not_found_wsm(client: AsyncClient):
    """Test WSM export returns 404 for non-existent scan."""
    response = await client.get("/api/export/99999/wsm")

    assert response.status_code == 404


@pytest.mark.unit
async def test_export_scan_not_found_raw(client: AsyncClient):
    """Test raw export returns 404 for non-existent scan."""
    response = await client.get("/api/export/99999/raw")

    assert response.status_code == 404


@pytest.mark.unit
async def test_export_scan_not_found_json(client: AsyncClient):
    """Test JSON export returns 404 for non-existent scan."""
    response = await client.get("/api/export/99999/json")

    assert response.status_code == 404


@pytest.mark.unit
async def test_export_scan_without_data(export_client_with_empty_scan):
    """Test export returns 400 for scan without data points."""
    client, scan_id = export_client_with_empty_scan
    response = await client.get(f"/api/export/{scan_id}/wwb")

    assert response.status_code == 400
    data = response.json()
    # RFC 7807 format uses 'type' URL containing error code
    assert "export_data_error" in data["type"]
    assert data["status"] == 400


@pytest.mark.unit
async def test_export_scan_without_data_wsm(export_client_with_empty_scan):
    """Test WSM export returns 400 for scan without data points."""
    client, scan_id = export_client_with_empty_scan
    response = await client.get(f"/api/export/{scan_id}/wsm")

    assert response.status_code == 400


@pytest.mark.unit
async def test_export_scan_without_data_raw(export_client_with_empty_scan):
    """Test raw export returns 400 for scan without data points."""
    client, scan_id = export_client_with_empty_scan
    response = await client.get(f"/api/export/{scan_id}/raw")

    assert response.status_code == 400


@pytest.mark.unit
async def test_export_scan_without_data_json(export_client_with_empty_scan):
    """Test JSON export returns 400 for scan without data points."""
    client, scan_id = export_client_with_empty_scan
    response = await client.get(f"/api/export/{scan_id}/json")

    assert response.status_code == 400


@pytest.mark.unit
async def test_export_invalid_scan_id_type(client: AsyncClient):
    """Test export returns 422 for invalid scan ID type."""
    response = await client.get("/api/export/not-a-number/wwb")

    assert response.status_code == 422


# ============================================================================
# Filename Tests
# ============================================================================


@pytest.mark.unit
async def test_export_filename_contains_scan_name(export_client_with_scan):
    """Test exported filename includes scan name."""
    client, scan_id = export_client_with_scan
    response = await client.get(f"/api/export/{scan_id}/wwb")

    assert response.status_code == 200
    content_disposition = response.headers["content-disposition"]

    # Should contain sanitized scan name
    assert "Test_Export_Scan" in content_disposition or "Test Export Scan" in content_disposition


@pytest.mark.unit
async def test_export_filename_format_suffix(export_client_with_scan):
    """Test exported filename has correct format suffix."""
    client, scan_id = export_client_with_scan

    # WWB format
    response = await client.get(f"/api/export/{scan_id}/wwb")
    assert "_wwb.csv" in response.headers["content-disposition"]

    # WSM format
    response = await client.get(f"/api/export/{scan_id}/wsm")
    assert "_wsm.csv" in response.headers["content-disposition"]

    # Raw format
    response = await client.get(f"/api/export/{scan_id}/raw")
    assert "_raw.csv" in response.headers["content-disposition"]

    # JSON format
    response = await client.get(f"/api/export/{scan_id}/json")
    assert ".json" in response.headers["content-disposition"]
