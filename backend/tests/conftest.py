"""
Pytest configuration and fixtures for backend tests.

Provides async fixtures for:
- Test database with SQLite in-memory
- Async HTTP client (httpx.AsyncClient)
- Mocked TinySA device
- FastAPI test app
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.db.database import Base, get_async_session
from backend.db.models import FrequencyPreset, SavedScan, ScanDataPoint  # noqa: F401
from backend.main import app

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Specify the async backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def override_get_session(test_engine):
    """Create a session dependency override for the FastAPI app."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _get_session_override() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return _get_session_override


@pytest.fixture
async def client(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP test client with the FastAPI app.

    The database session is overridden to use an in-memory SQLite database.
    """
    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_tinysa() -> MagicMock:
    """
    Create a mock TinySA device.

    This fixture provides a mock TinySA instance with common methods
    already configured with sensible defaults.
    """
    mock = MagicMock()
    mock.is_connected = False
    mock.port = None

    # Configure connect to return device info
    async def mock_connect(port: str) -> dict[str, Any]:
        mock.is_connected = True
        mock.port = port
        return {
            "version": "tinySA4_v1.4-140-g294ba13",
            "hardware": "V0.4.5.1.1",
            "device_type": "tinySA ULTRA",
            "port": port,
        }

    mock.connect = AsyncMock(side_effect=mock_connect)

    # Configure disconnect
    async def mock_disconnect():
        mock.is_connected = False
        mock.port = None

    mock.disconnect = AsyncMock(side_effect=mock_disconnect)

    # Configure list_ports
    mock.list_ports = MagicMock(return_value=[
        {
            "port": "/dev/cu.usbmodem4001",
            "description": "TinySA ULTRA",
            "hwid": "USB VID:PID=0483:5740",
            "manufacturer": "STMicroelectronics",
            "product": "TinySA ULTRA",
            "serial_number": "12345",
            "vid": 0x0483,
            "pid": 0x5740,
        },
    ])

    # Configure set_rbw
    mock.set_rbw = AsyncMock()

    # Configure scan_raw to yield test data
    async def mock_scan_raw(start_hz: int, stop_hz: int, points: int = 450):
        """Generate mock scan data."""
        freq_step = (stop_hz - start_hz) / (points - 1) if points > 1 else 0
        for i in range(points):
            freq_hz = int(start_hz + (i * freq_step))
            # Generate a simple noise floor with some random variation
            amplitude_dbm = -100.0 + (i % 10) * 0.5
            yield (freq_hz, amplitude_dbm)

    mock.scan_raw = mock_scan_raw

    return mock


@pytest.fixture
def mock_tinysa_connected(mock_tinysa) -> MagicMock:
    """Create a mock TinySA device that is already connected."""
    mock_tinysa.is_connected = True
    mock_tinysa.port = "/dev/cu.usbmodem4001"
    return mock_tinysa


@pytest.fixture
def patch_tinysa(mock_tinysa):
    """
    Patch the TinySA singleton with a mock.

    Use this fixture when testing code that uses get_tinysa().
    """
    with patch("backend.core.tinysa.get_tinysa", return_value=mock_tinysa):
        yield mock_tinysa


@pytest.fixture
def patch_tinysa_connected(mock_tinysa_connected):
    """
    Patch the TinySA singleton with a connected mock device.

    Use this fixture when testing code that expects a connected device.
    """
    with patch("backend.core.tinysa.get_tinysa", return_value=mock_tinysa_connected):
        yield mock_tinysa_connected


# Sample data fixtures


@pytest.fixture
def sample_preset_data() -> dict[str, Any]:
    """Sample frequency preset data for testing."""
    return {
        "name": "Test UHF Band",
        "description": "Test preset for UHF frequencies",
        "start_freq_hz": 470_000_000,  # 470 MHz
        "stop_freq_hz": 698_000_000,   # 698 MHz
        "points": 450,
        "rbw_khz": 100.0,
        "category": "UHF",
        "is_builtin": False,
    }


@pytest.fixture
def sample_scan_data() -> dict[str, Any]:
    """Sample scan data for testing."""
    return {
        "name": "Test Scan",
        "start_freq_hz": 470_000_000,
        "stop_freq_hz": 698_000_000,
        "points": 100,
        "rbw_khz": 100.0,
        "location": "Test Location",
        "notes": "Test scan notes",
        "tags": "test,demo",
    }


@pytest.fixture
def sample_scan_points() -> list[dict[str, Any]]:
    """Sample scan data points for testing."""
    points = []
    start_hz = 470_000_000
    stop_hz = 698_000_000
    num_points = 100
    freq_step = (stop_hz - start_hz) / (num_points - 1)

    for i in range(num_points):
        points.append({
            "index": i,
            "frequency_hz": int(start_hz + (i * freq_step)),
            "amplitude_dbm": -100.0 + (i % 20) * 0.5,
        })

    return points


@pytest.fixture
async def preset_in_db(test_session, sample_preset_data) -> FrequencyPreset:
    """Create a preset in the test database and return it."""
    preset = FrequencyPreset(**sample_preset_data)
    test_session.add(preset)
    await test_session.commit()
    await test_session.refresh(preset)
    return preset


@pytest.fixture
async def scan_in_db(test_session, sample_scan_data, sample_scan_points) -> SavedScan:
    """Create a scan with data points in the test database and return it."""
    scan = SavedScan(**sample_scan_data)
    test_session.add(scan)
    await test_session.flush()  # Get the scan ID

    # Add data points
    for point_data in sample_scan_points:
        point = ScanDataPoint(scan_id=scan.id, **point_data)
        test_session.add(point)

    await test_session.commit()
    await test_session.refresh(scan)
    return scan
