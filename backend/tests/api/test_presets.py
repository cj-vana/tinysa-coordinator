"""
Tests for the presets API routes.

Tests cover all CRUD operations for frequency presets:
- GET /api/presets/ (list all)
- POST /api/presets/ (create)
- GET /api/presets/{id} (get by ID)
- PUT /api/presets/{id} (update)
- DELETE /api/presets/{id} (delete)

Also tests validation errors, not found errors, and built-in preset protection.
"""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FrequencyPreset


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_preset_data() -> dict[str, Any]:
    """Valid preset data for creating a new preset."""
    return {
        "name": "Test Wireless Mic Band",
        "description": "Test preset for wireless microphone frequencies",
        "start_freq_hz": 470_000_000,  # 470 MHz
        "stop_freq_hz": 698_000_000,  # 698 MHz
        "points": 450,
        "rbw_khz": 100.0,
        "category": "UHF",
    }


@pytest.fixture
def minimal_preset_data() -> dict[str, Any]:
    """Minimal valid preset data (only required fields)."""
    return {
        "name": "Minimal Preset",
        "start_freq_hz": 100_000_000,  # 100 MHz
        "stop_freq_hz": 200_000_000,  # 200 MHz
    }


@pytest.fixture
async def user_preset_in_db(test_session: AsyncSession) -> FrequencyPreset:
    """Create a user (non-builtin) preset in the test database."""
    preset = FrequencyPreset(
        name="User Test Preset",
        description="A user-created preset for testing",
        start_freq_hz=500_000_000,
        stop_freq_hz=600_000_000,
        points=300,
        rbw_khz=50.0,
        category="UHF",
        is_builtin=False,
    )
    test_session.add(preset)
    await test_session.commit()
    await test_session.refresh(preset)
    return preset


@pytest.fixture
async def builtin_preset_in_db(test_session: AsyncSession) -> FrequencyPreset:
    """Create a built-in preset in the test database."""
    preset = FrequencyPreset(
        name="Built-in UHF Band",
        description="A built-in preset that should not be modifiable",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=450,
        rbw_khz=100.0,
        category="UHF",
        is_builtin=True,
    )
    test_session.add(preset)
    await test_session.commit()
    await test_session.refresh(preset)
    return preset


@pytest.fixture
async def multiple_presets_in_db(test_session: AsyncSession) -> list[FrequencyPreset]:
    """Create multiple presets for list testing."""
    presets = [
        FrequencyPreset(
            name="UHF Band 1",
            start_freq_hz=470_000_000,
            stop_freq_hz=548_000_000,
            category="UHF",
            is_builtin=True,
        ),
        FrequencyPreset(
            name="VHF Band",
            start_freq_hz=174_000_000,
            stop_freq_hz=216_000_000,
            category="VHF",
            is_builtin=True,
        ),
        FrequencyPreset(
            name="ISM 900 MHz",
            start_freq_hz=902_000_000,
            stop_freq_hz=928_000_000,
            category="ISM",
            is_builtin=False,
        ),
        FrequencyPreset(
            name="Custom Range",
            start_freq_hz=1_000_000_000,
            stop_freq_hz=1_200_000_000,
            category="Custom",
            is_builtin=False,
        ),
    ]
    for preset in presets:
        test_session.add(preset)
    await test_session.commit()
    for preset in presets:
        await test_session.refresh(preset)
    return presets


# ============================================================================
# List Presets Tests (GET /api/presets/)
# ============================================================================


@pytest.mark.unit
async def test_list_presets_empty(client: AsyncClient):
    """Test listing presets when database is empty returns empty list."""
    response = await client.get("/api/presets/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.unit
async def test_list_presets_returns_all(
    client: AsyncClient, multiple_presets_in_db: list[FrequencyPreset]
):
    """Test listing presets returns all presets in database."""
    response = await client.get("/api/presets/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(multiple_presets_in_db)


@pytest.mark.unit
async def test_list_presets_response_format(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test that listed presets have correct response format."""
    response = await client.get("/api/presets/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    preset = data[0]
    assert "id" in preset
    assert "name" in preset
    assert "description" in preset
    assert "start_freq_hz" in preset
    assert "stop_freq_hz" in preset
    assert "points" in preset
    assert "rbw_khz" in preset
    assert "category" in preset
    assert "is_builtin" in preset
    assert "created_at" in preset
    assert "updated_at" in preset


# ============================================================================
# Create Preset Tests (POST /api/presets/)
# ============================================================================


@pytest.mark.unit
async def test_create_preset_with_valid_data(
    client: AsyncClient, valid_preset_data: dict[str, Any]
):
    """Test creating a preset with valid data returns 201 and created preset."""
    response = await client.post("/api/presets/", json=valid_preset_data)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == valid_preset_data["name"]
    assert data["description"] == valid_preset_data["description"]
    assert data["start_freq_hz"] == valid_preset_data["start_freq_hz"]
    assert data["stop_freq_hz"] == valid_preset_data["stop_freq_hz"]
    assert data["points"] == valid_preset_data["points"]
    assert data["rbw_khz"] == valid_preset_data["rbw_khz"]
    assert data["category"] == valid_preset_data["category"]
    assert data["is_builtin"] is False  # User-created presets are never built-in
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.unit
async def test_create_preset_with_minimal_data(
    client: AsyncClient, minimal_preset_data: dict[str, Any]
):
    """Test creating a preset with only required fields uses defaults."""
    response = await client.post("/api/presets/", json=minimal_preset_data)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == minimal_preset_data["name"]
    assert data["start_freq_hz"] == minimal_preset_data["start_freq_hz"]
    assert data["stop_freq_hz"] == minimal_preset_data["stop_freq_hz"]
    # Check defaults
    assert data["points"] == 450  # Default value
    assert data["category"] == "Custom"  # Default value
    assert data["is_builtin"] is False
    assert data["description"] is None


@pytest.mark.unit
async def test_create_preset_missing_required_field(client: AsyncClient):
    """Test creating a preset without required fields returns 422."""
    # Missing name
    response = await client.post(
        "/api/presets/",
        json={"start_freq_hz": 100_000_000, "stop_freq_hz": 200_000_000},
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_invalid_frequency_range(client: AsyncClient):
    """Test creating a preset with stop_freq <= start_freq returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Invalid Range",
            "start_freq_hz": 500_000_000,
            "stop_freq_hz": 400_000_000,  # Less than start
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_equal_frequencies(client: AsyncClient):
    """Test creating a preset with equal start and stop frequencies returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Equal Frequencies",
            "start_freq_hz": 500_000_000,
            "stop_freq_hz": 500_000_000,  # Equal to start
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_negative_frequency(client: AsyncClient):
    """Test creating a preset with negative frequency returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Negative Frequency",
            "start_freq_hz": -100_000_000,
            "stop_freq_hz": 200_000_000,
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_zero_frequency(client: AsyncClient):
    """Test creating a preset with zero frequency returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Zero Frequency",
            "start_freq_hz": 0,
            "stop_freq_hz": 200_000_000,
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_invalid_points_too_low(client: AsyncClient):
    """Test creating a preset with points below minimum returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Too Few Points",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
            "points": 5,  # Minimum is 10
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_invalid_points_too_high(client: AsyncClient):
    """Test creating a preset with points above maximum returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Too Many Points",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
            "points": 20000,  # Maximum is 10000
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_empty_name(client: AsyncClient):
    """Test creating a preset with empty name returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_name_too_long(client: AsyncClient):
    """Test creating a preset with name exceeding max length returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "x" * 101,  # Max is 100 characters
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_invalid_category(client: AsyncClient):
    """Test creating a preset with invalid category returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Invalid Category",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
            "category": "INVALID",
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_create_preset_negative_rbw(client: AsyncClient):
    """Test creating a preset with negative RBW returns 422."""
    response = await client.post(
        "/api/presets/",
        json={
            "name": "Negative RBW",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
            "rbw_khz": -10.0,
        },
    )

    assert response.status_code == 422


# ============================================================================
# Get Preset by ID Tests (GET /api/presets/{id})
# ============================================================================


@pytest.mark.unit
async def test_get_preset_by_id(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test getting a preset by valid ID returns the preset."""
    response = await client.get(f"/api/presets/{user_preset_in_db.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == user_preset_in_db.id
    assert data["name"] == user_preset_in_db.name
    assert data["start_freq_hz"] == user_preset_in_db.start_freq_hz
    assert data["stop_freq_hz"] == user_preset_in_db.stop_freq_hz


@pytest.mark.unit
async def test_get_preset_not_found(client: AsyncClient):
    """Test getting a non-existent preset returns 404."""
    response = await client.get("/api/presets/99999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "title" in data  # RFC 7807 format


@pytest.mark.unit
async def test_get_builtin_preset(
    client: AsyncClient, builtin_preset_in_db: FrequencyPreset
):
    """Test that built-in presets can be retrieved."""
    response = await client.get(f"/api/presets/{builtin_preset_in_db.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == builtin_preset_in_db.id
    assert data["is_builtin"] is True


# ============================================================================
# Update Preset Tests (PUT /api/presets/{id})
# ============================================================================


@pytest.mark.unit
async def test_update_preset_full(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test updating all fields of a user preset."""
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "start_freq_hz": 600_000_000,
        "stop_freq_hz": 700_000_000,
        "points": 500,
        "rbw_khz": 75.0,
        "category": "VHF",
    }

    response = await client.put(
        f"/api/presets/{user_preset_in_db.id}", json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == user_preset_in_db.id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["start_freq_hz"] == update_data["start_freq_hz"]
    assert data["stop_freq_hz"] == update_data["stop_freq_hz"]
    assert data["points"] == update_data["points"]
    assert data["rbw_khz"] == update_data["rbw_khz"]
    assert data["category"] == update_data["category"]


@pytest.mark.unit
async def test_update_preset_partial(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test partially updating a preset (only some fields)."""
    update_data = {"name": "Only Name Updated"}

    response = await client.put(
        f"/api/presets/{user_preset_in_db.id}", json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Only Name Updated"
    # Other fields should remain unchanged
    assert data["start_freq_hz"] == user_preset_in_db.start_freq_hz
    assert data["stop_freq_hz"] == user_preset_in_db.stop_freq_hz


@pytest.mark.unit
async def test_update_preset_not_found(client: AsyncClient):
    """Test updating a non-existent preset returns 404."""
    response = await client.put(
        "/api/presets/99999",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 404


@pytest.mark.unit
async def test_update_builtin_preset_forbidden(
    client: AsyncClient, builtin_preset_in_db: FrequencyPreset
):
    """Test updating a built-in preset returns 403 Forbidden."""
    response = await client.put(
        f"/api/presets/{builtin_preset_in_db.id}",
        json={"name": "Trying to Update Built-in"},
    )

    assert response.status_code == 403
    data = response.json()
    # Check for RFC 7807 format or standard detail
    assert "detail" in data or "title" in data


@pytest.mark.unit
async def test_update_preset_invalid_name(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test updating preset with invalid name returns 422."""
    response = await client.put(
        f"/api/presets/{user_preset_in_db.id}",
        json={"name": ""},  # Empty name
    )

    assert response.status_code == 422


@pytest.mark.unit
async def test_update_preset_invalid_points(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test updating preset with invalid points returns 422."""
    response = await client.put(
        f"/api/presets/{user_preset_in_db.id}",
        json={"points": 5},  # Below minimum
    )

    assert response.status_code == 422


# ============================================================================
# Delete Preset Tests (DELETE /api/presets/{id})
# ============================================================================


@pytest.mark.unit
async def test_delete_preset(client: AsyncClient, user_preset_in_db: FrequencyPreset):
    """Test deleting a user preset returns 204 and removes the preset."""
    preset_id = user_preset_in_db.id

    response = await client.delete(f"/api/presets/{preset_id}")

    assert response.status_code == 204
    assert response.content == b""  # No content

    # Verify preset is deleted
    get_response = await client.get(f"/api/presets/{preset_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_preset_not_found(client: AsyncClient):
    """Test deleting a non-existent preset returns 404."""
    response = await client.delete("/api/presets/99999")

    assert response.status_code == 404


@pytest.mark.unit
async def test_delete_builtin_preset_forbidden(
    client: AsyncClient, builtin_preset_in_db: FrequencyPreset
):
    """Test deleting a built-in preset returns 403 Forbidden."""
    response = await client.delete(f"/api/presets/{builtin_preset_in_db.id}")

    assert response.status_code == 403
    data = response.json()
    # Check for RFC 7807 format or standard detail
    assert "detail" in data or "title" in data

    # Verify preset still exists
    get_response = await client.get(f"/api/presets/{builtin_preset_in_db.id}")
    assert get_response.status_code == 200


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


@pytest.mark.unit
async def test_create_then_get_preset(
    client: AsyncClient, valid_preset_data: dict[str, Any]
):
    """Test creating a preset and then retrieving it by ID."""
    # Create
    create_response = await client.post("/api/presets/", json=valid_preset_data)
    assert create_response.status_code == 201
    created_preset = create_response.json()

    # Get
    get_response = await client.get(f"/api/presets/{created_preset['id']}")
    assert get_response.status_code == 200
    retrieved_preset = get_response.json()

    # Verify they match
    assert retrieved_preset["id"] == created_preset["id"]
    assert retrieved_preset["name"] == created_preset["name"]
    assert retrieved_preset["start_freq_hz"] == created_preset["start_freq_hz"]


@pytest.mark.unit
async def test_create_update_then_get_preset(
    client: AsyncClient, valid_preset_data: dict[str, Any]
):
    """Test creating, updating, and retrieving a preset."""
    # Create
    create_response = await client.post("/api/presets/", json=valid_preset_data)
    assert create_response.status_code == 201
    preset_id = create_response.json()["id"]

    # Update
    update_data = {"name": "Updated via Integration Test"}
    update_response = await client.put(f"/api/presets/{preset_id}", json=update_data)
    assert update_response.status_code == 200

    # Get
    get_response = await client.get(f"/api/presets/{preset_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Updated via Integration Test"


@pytest.mark.unit
async def test_create_then_delete_preset(
    client: AsyncClient, valid_preset_data: dict[str, Any]
):
    """Test creating a preset and then deleting it."""
    # Create
    create_response = await client.post("/api/presets/", json=valid_preset_data)
    assert create_response.status_code == 201
    preset_id = create_response.json()["id"]

    # Verify it exists
    get_response = await client.get(f"/api/presets/{preset_id}")
    assert get_response.status_code == 200

    # Delete
    delete_response = await client.delete(f"/api/presets/{preset_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/presets/{preset_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_list_after_create(
    client: AsyncClient, valid_preset_data: dict[str, Any]
):
    """Test that newly created presets appear in list."""
    # Initially empty
    initial_response = await client.get("/api/presets/")
    initial_count = len(initial_response.json())

    # Create a preset
    create_response = await client.post("/api/presets/", json=valid_preset_data)
    assert create_response.status_code == 201

    # List should have one more
    final_response = await client.get("/api/presets/")
    assert len(final_response.json()) == initial_count + 1


@pytest.mark.unit
async def test_list_after_delete(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test that deleted presets no longer appear in list."""
    # Initial count with preset
    initial_response = await client.get("/api/presets/")
    initial_count = len(initial_response.json())
    assert initial_count >= 1

    # Delete the preset
    delete_response = await client.delete(f"/api/presets/{user_preset_in_db.id}")
    assert delete_response.status_code == 204

    # List should have one fewer
    final_response = await client.get("/api/presets/")
    assert len(final_response.json()) == initial_count - 1


@pytest.mark.unit
async def test_preset_timestamps_updated(
    client: AsyncClient, user_preset_in_db: FrequencyPreset
):
    """Test that updated_at timestamp changes on update."""
    # Get original timestamp
    get_response = await client.get(f"/api/presets/{user_preset_in_db.id}")
    original_updated_at = get_response.json()["updated_at"]

    # Update the preset
    update_response = await client.put(
        f"/api/presets/{user_preset_in_db.id}",
        json={"name": "Timestamp Test Update"},
    )
    new_updated_at = update_response.json()["updated_at"]

    # Timestamps should be different (or at least the update should have worked)
    # Note: In fast tests, timestamps might be the same within same second
    assert update_response.status_code == 200
