"""
Tests to verify that the test fixtures work correctly.

These tests ensure the database fixtures, mock objects, and client
are properly configured.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FrequencyPreset, SavedScan


@pytest.mark.unit
async def test_test_session_works(test_session: AsyncSession):
    """Test that the test database session is properly configured."""
    # Simple query to verify the session works
    result = await test_session.execute(select(FrequencyPreset))
    presets = result.scalars().all()
    # Should be empty initially
    assert presets == []


@pytest.mark.unit
async def test_preset_in_db_fixture(preset_in_db: FrequencyPreset):
    """Test that the preset_in_db fixture creates a preset."""
    assert preset_in_db.id is not None
    assert preset_in_db.name == "Test UHF Band"
    assert preset_in_db.start_freq_hz == 470_000_000
    assert preset_in_db.stop_freq_hz == 698_000_000
    assert preset_in_db.category == "UHF"


@pytest.mark.unit
async def test_scan_in_db_fixture(scan_in_db: SavedScan):
    """Test that the scan_in_db fixture creates a scan with data points."""
    assert scan_in_db.id is not None
    assert scan_in_db.name == "Test Scan"
    assert len(scan_in_db.data_points) == 100
    # Verify data points are ordered by index
    for i, point in enumerate(scan_in_db.data_points):
        assert point.index == i


@pytest.mark.unit
async def test_database_isolation(test_session: AsyncSession, sample_preset_data: dict):
    """Test that database changes are isolated between tests."""
    # Create a preset in this test
    preset = FrequencyPreset(**sample_preset_data)
    test_session.add(preset)
    await test_session.commit()

    # Verify it exists
    result = await test_session.execute(select(FrequencyPreset))
    presets = result.scalars().all()
    assert len(presets) == 1


@pytest.mark.unit
async def test_database_isolation_empty(test_session: AsyncSession):
    """Test that database is clean at start of each test."""
    # This test runs after test_database_isolation
    # The database should be empty due to rollback
    result = await test_session.execute(select(FrequencyPreset))
    presets = result.scalars().all()
    # Should be empty - the previous test's changes were rolled back
    assert presets == []


@pytest.mark.unit
def test_mock_tinysa_default_state(mock_tinysa):
    """Test that mock_tinysa is in expected default state."""
    assert mock_tinysa.is_connected is False
    assert mock_tinysa.port is None


@pytest.mark.unit
def test_mock_tinysa_connected_state(mock_tinysa_connected):
    """Test that mock_tinysa_connected is properly configured."""
    assert mock_tinysa_connected.is_connected is True
    assert mock_tinysa_connected.port == "/dev/cu.usbmodem4001"


@pytest.mark.unit
async def test_mock_tinysa_connect(mock_tinysa):
    """Test that mock_tinysa.connect() works correctly."""
    result = await mock_tinysa.connect("/dev/test")

    assert mock_tinysa.is_connected is True
    assert mock_tinysa.port == "/dev/test"
    assert result["device_type"] == "tinySA ULTRA"
    assert "version" in result


@pytest.mark.unit
async def test_mock_tinysa_disconnect(mock_tinysa_connected):
    """Test that mock_tinysa.disconnect() works correctly."""
    await mock_tinysa_connected.disconnect()

    assert mock_tinysa_connected.is_connected is False
    assert mock_tinysa_connected.port is None


@pytest.mark.unit
async def test_mock_tinysa_scan_raw(mock_tinysa):
    """Test that mock_tinysa.scan_raw() generates expected data."""
    start_hz = 470_000_000
    stop_hz = 698_000_000
    points = 10

    data = []
    async for freq_hz, amplitude_dbm in mock_tinysa.scan_raw(start_hz, stop_hz, points):
        data.append((freq_hz, amplitude_dbm))

    assert len(data) == points
    assert data[0][0] == start_hz
    assert data[-1][0] == stop_hz
    # All amplitudes should be in reasonable dBm range
    for _, amplitude in data:
        assert -120 <= amplitude <= 0
