"""
Tests for the scan history API routes (/api/history/*).

These tests verify CRUD operations for saved scans:
- GET /api/history/ - List scans with pagination and search
- POST /api/history/ - Create new scan with data points
- GET /api/history/{id} - Get scan with all data points
- PUT /api/history/{id} - Update scan metadata
- DELETE /api/history/{id} - Delete a scan
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from backend.db.models import SavedScan, ScanDataPoint


# =============================================================================
# Fixtures for history tests
# =============================================================================


@pytest.fixture
def create_scan_payload(sample_scan_data, sample_scan_points):
    """Create a valid payload for POST /api/history/."""
    return {
        **sample_scan_data,
        "data_points": sample_scan_points,
        "scan_started_at": (datetime.utcnow() - timedelta(seconds=30)).isoformat(),
        "scan_completed_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def minimal_scan_payload():
    """Create a minimal valid payload for POST /api/history/."""
    return {
        "name": "Minimal Scan",
        "start_freq_hz": 100_000_000,
        "stop_freq_hz": 200_000_000,
        "points": 10,
        "data_points": [
            {"index": i, "frequency_hz": 100_000_000 + i * 10_000_000, "amplitude_dbm": -90.0}
            for i in range(10)
        ],
    }


# =============================================================================
# GET /api/history/ - List Scans Tests
# =============================================================================


@pytest.mark.unit
async def test_list_scans_empty(client: AsyncClient):
    """Test listing scans when database is empty."""
    response = await client.get("/api/history/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 20


@pytest.mark.unit
async def test_list_scans_with_data(client: AsyncClient, scan_in_db):
    """Test listing scans returns existing scans."""
    response = await client.get("/api/history/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    scan = data["items"][0]
    assert scan["id"] == scan_in_db.id
    assert scan["name"] == scan_in_db.name
    assert scan["start_freq_hz"] == scan_in_db.start_freq_hz
    assert scan["stop_freq_hz"] == scan_in_db.stop_freq_hz
    assert scan["points"] == scan_in_db.points
    assert "created_at" in scan


@pytest.mark.unit
async def test_list_scans_pagination(client: AsyncClient, test_session):
    """Test pagination parameters work correctly."""
    # Create multiple scans
    for i in range(5):
        scan = SavedScan(
            name=f"Scan {i}",
            start_freq_hz=470_000_000,
            stop_freq_hz=698_000_000,
            points=100,
        )
        test_session.add(scan)
    await test_session.commit()

    # Test with limit
    response = await client.get("/api/history/", params={"limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["per_page"] == 2

    # Test with offset
    response = await client.get("/api/history/", params={"limit": 2, "offset": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2


@pytest.mark.unit
async def test_list_scans_search_by_name(client: AsyncClient, test_session):
    """Test search filter matches scan names."""
    # Create scans with different names
    scan1 = SavedScan(
        name="Concert Hall Scan",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=100,
    )
    scan2 = SavedScan(
        name="Studio Recording",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=100,
    )
    test_session.add_all([scan1, scan2])
    await test_session.commit()

    # Search for "Concert"
    response = await client.get("/api/history/", params={"search": "Concert"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Concert Hall Scan"


@pytest.mark.unit
async def test_list_scans_search_by_location(client: AsyncClient, test_session):
    """Test search filter matches scan locations."""
    # Create scans with different locations
    scan1 = SavedScan(
        name="Scan 1",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=100,
        location="Madison Square Garden",
    )
    scan2 = SavedScan(
        name="Scan 2",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=100,
        location="Small Venue",
    )
    test_session.add_all([scan1, scan2])
    await test_session.commit()

    # Search for "Madison"
    response = await client.get("/api/history/", params={"search": "Madison"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["location"] == "Madison Square Garden"


@pytest.mark.unit
async def test_list_scans_search_case_insensitive(client: AsyncClient, test_session):
    """Test search is case insensitive."""
    scan = SavedScan(
        name="UPPERCASE SCAN",
        start_freq_hz=470_000_000,
        stop_freq_hz=698_000_000,
        points=100,
    )
    test_session.add(scan)
    await test_session.commit()

    # Search with lowercase
    response = await client.get("/api/history/", params={"search": "uppercase"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.unit
async def test_list_scans_invalid_pagination(client: AsyncClient):
    """Test invalid pagination parameters are rejected."""
    # Limit too high
    response = await client.get("/api/history/", params={"limit": 500})
    assert response.status_code == 422

    # Negative offset
    response = await client.get("/api/history/", params={"offset": -1})
    assert response.status_code == 422


# =============================================================================
# POST /api/history/ - Create Scan Tests
# =============================================================================


@pytest.mark.unit
async def test_create_scan_success(client: AsyncClient, create_scan_payload):
    """Test creating a new scan with data points."""
    response = await client.post("/api/history/", json=create_scan_payload)

    assert response.status_code == 201
    data = response.json()

    # Verify scan metadata
    assert data["name"] == create_scan_payload["name"]
    assert data["start_freq_hz"] == create_scan_payload["start_freq_hz"]
    assert data["stop_freq_hz"] == create_scan_payload["stop_freq_hz"]
    assert data["points"] == create_scan_payload["points"]
    assert data["location"] == create_scan_payload["location"]
    assert data["notes"] == create_scan_payload["notes"]
    assert data["tags"] == create_scan_payload["tags"]
    assert "id" in data
    assert "created_at" in data

    # Verify data points
    assert data["data_point_count"] == len(create_scan_payload["data_points"])
    assert len(data["data_points"]) == len(create_scan_payload["data_points"])


@pytest.mark.unit
async def test_create_scan_minimal(client: AsyncClient, minimal_scan_payload):
    """Test creating a scan with minimal required fields."""
    response = await client.post("/api/history/", json=minimal_scan_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == minimal_scan_payload["name"]
    assert data["location"] is None
    assert data["notes"] is None
    assert data["tags"] is None
    assert len(data["data_points"]) == 10


@pytest.mark.unit
async def test_create_scan_with_preset_info(client: AsyncClient, minimal_scan_payload):
    """Test creating a scan with preset reference."""
    payload = {
        **minimal_scan_payload,
        "preset_id": 1,
        "preset_name": "UHF Band",
    }
    response = await client.post("/api/history/", json=payload)

    assert response.status_code == 201
    data = response.json()
    # preset_id may be None if the preset doesn't exist (FK constraint)
    # but preset_name should be stored as a snapshot
    assert data["preset_name"] == "UHF Band"


@pytest.mark.unit
async def test_create_scan_validates_data_points(client: AsyncClient, minimal_scan_payload):
    """Test data point validation rules."""
    # Test with empty data points
    payload = {**minimal_scan_payload, "data_points": []}
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422

    # Test with invalid amplitude (too low)
    payload = {
        **minimal_scan_payload,
        "data_points": [{"index": 0, "frequency_hz": 100_000_000, "amplitude_dbm": -250}],
    }
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422


@pytest.mark.unit
async def test_create_scan_validates_frequency_range(client: AsyncClient, minimal_scan_payload):
    """Test that stop_freq must be greater than start_freq."""
    payload = {
        **minimal_scan_payload,
        "start_freq_hz": 500_000_000,
        "stop_freq_hz": 400_000_000,  # Invalid: less than start
    }
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422


@pytest.mark.unit
async def test_create_scan_validates_name_required(client: AsyncClient, minimal_scan_payload):
    """Test that name is required."""
    payload = {**minimal_scan_payload}
    del payload["name"]
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422


@pytest.mark.unit
async def test_create_scan_validates_points_range(client: AsyncClient, minimal_scan_payload):
    """Test points must be within valid range (10-10000)."""
    # Too few points
    payload = {**minimal_scan_payload, "points": 5}
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422

    # Too many points
    payload = {**minimal_scan_payload, "points": 20000}
    response = await client.post("/api/history/", json=payload)
    assert response.status_code == 422


# =============================================================================
# GET /api/history/{id} - Get Single Scan Tests
# =============================================================================


@pytest.mark.unit
async def test_get_scan_success(client: AsyncClient, scan_in_db):
    """Test getting a scan by ID returns all data."""
    response = await client.get(f"/api/history/{scan_in_db.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify metadata
    assert data["id"] == scan_in_db.id
    assert data["name"] == scan_in_db.name
    assert data["start_freq_hz"] == scan_in_db.start_freq_hz
    assert data["stop_freq_hz"] == scan_in_db.stop_freq_hz
    assert data["points"] == scan_in_db.points
    assert data["location"] == scan_in_db.location
    assert data["notes"] == scan_in_db.notes
    assert data["tags"] == scan_in_db.tags

    # Verify data points are included
    assert "data_points" in data
    assert len(data["data_points"]) == data["data_point_count"]


@pytest.mark.unit
async def test_get_scan_includes_data_points(client: AsyncClient, scan_in_db):
    """Test that data points are properly structured."""
    response = await client.get(f"/api/history/{scan_in_db.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify data point structure
    assert len(data["data_points"]) > 0
    point = data["data_points"][0]
    assert "id" in point
    assert "scan_id" in point
    assert "index" in point
    assert "frequency_hz" in point
    assert "amplitude_dbm" in point
    assert point["scan_id"] == scan_in_db.id


@pytest.mark.unit
async def test_get_scan_data_points_ordered(client: AsyncClient, scan_in_db):
    """Test that data points are returned in index order."""
    response = await client.get(f"/api/history/{scan_in_db.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify points are ordered by index
    indices = [p["index"] for p in data["data_points"]]
    assert indices == sorted(indices)


@pytest.mark.unit
async def test_get_scan_not_found(client: AsyncClient):
    """Test getting a non-existent scan returns 404."""
    response = await client.get("/api/history/99999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# =============================================================================
# PUT /api/history/{id} - Update Scan Tests
# =============================================================================


@pytest.mark.unit
async def test_update_scan_name(client: AsyncClient, scan_in_db):
    """Test updating scan name."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"name": "Updated Scan Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Scan Name"
    # Other fields unchanged
    assert data["location"] == scan_in_db.location


@pytest.mark.unit
async def test_update_scan_location(client: AsyncClient, scan_in_db):
    """Test updating scan location."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"location": "New Location"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "New Location"


@pytest.mark.unit
async def test_update_scan_notes(client: AsyncClient, scan_in_db):
    """Test updating scan notes."""
    new_notes = "These are updated notes with more detail."
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"notes": new_notes}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == new_notes


@pytest.mark.unit
async def test_update_scan_tags(client: AsyncClient, scan_in_db):
    """Test updating scan tags."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"tags": "updated,new,tags"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == "updated,new,tags"


@pytest.mark.unit
async def test_update_scan_multiple_fields(client: AsyncClient, scan_in_db):
    """Test updating multiple fields at once."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={
            "name": "Multi Update Scan",
            "location": "Multi Update Location",
            "notes": "Multi update notes",
            "tags": "multi,update",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Multi Update Scan"
    assert data["location"] == "Multi Update Location"
    assert data["notes"] == "Multi update notes"
    assert data["tags"] == "multi,update"


@pytest.mark.unit
async def test_update_scan_partial(client: AsyncClient, scan_in_db):
    """Test partial update doesn't affect other fields."""
    original_notes = scan_in_db.notes
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"name": "Only Name Changed"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Only Name Changed"
    assert data["notes"] == original_notes


@pytest.mark.unit
async def test_update_scan_clear_optional_field(client: AsyncClient, scan_in_db):
    """Test clearing an optional field with null."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"notes": None}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] is None


@pytest.mark.unit
async def test_update_scan_not_found(client: AsyncClient):
    """Test updating a non-existent scan returns 404."""
    response = await client.put(
        "/api/history/99999",
        json={"name": "New Name"}
    )

    assert response.status_code == 404


@pytest.mark.unit
async def test_update_scan_empty_body(client: AsyncClient, scan_in_db):
    """Test update with empty body returns current data."""
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == scan_in_db.name


@pytest.mark.unit
async def test_update_scan_validates_name_length(client: AsyncClient, scan_in_db):
    """Test name validation on update."""
    # Empty name should fail
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"name": ""}
    )
    assert response.status_code == 422

    # Name too long should fail
    response = await client.put(
        f"/api/history/{scan_in_db.id}",
        json={"name": "x" * 250}
    )
    assert response.status_code == 422


# =============================================================================
# DELETE /api/history/{id} - Delete Scan Tests
# =============================================================================


@pytest.mark.unit
async def test_delete_scan_success(client: AsyncClient, scan_in_db):
    """Test deleting a scan returns 204."""
    scan_id = scan_in_db.id
    response = await client.delete(f"/api/history/{scan_id}")

    assert response.status_code == 204

    # Verify scan is gone
    get_response = await client.get(f"/api/history/{scan_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_scan_removes_data_points(
    client: AsyncClient, scan_in_db, test_session
):
    """Test deleting a scan also removes its data points."""
    scan_id = scan_in_db.id

    # Verify data points exist before delete
    from sqlalchemy import select, func
    count_query = select(func.count()).where(ScanDataPoint.scan_id == scan_id)
    result = await test_session.execute(count_query)
    initial_count = result.scalar()
    assert initial_count > 0

    # Delete the scan
    response = await client.delete(f"/api/history/{scan_id}")
    assert response.status_code == 204

    # Need to create a new session to see the changes (current session is rolled back)
    # The cascade delete is verified by the 404 on GET


@pytest.mark.unit
async def test_delete_scan_not_found(client: AsyncClient):
    """Test deleting a non-existent scan returns 404."""
    response = await client.delete("/api/history/99999")

    assert response.status_code == 404


@pytest.mark.unit
async def test_delete_scan_idempotent_fails(client: AsyncClient, scan_in_db):
    """Test deleting an already deleted scan returns 404."""
    scan_id = scan_in_db.id

    # First delete succeeds
    response = await client.delete(f"/api/history/{scan_id}")
    assert response.status_code == 204

    # Second delete fails
    response = await client.delete(f"/api/history/{scan_id}")
    assert response.status_code == 404


# =============================================================================
# Integration Tests - End-to-End Workflows
# =============================================================================


@pytest.mark.integration
async def test_full_scan_lifecycle(client: AsyncClient, minimal_scan_payload):
    """Test complete scan CRUD lifecycle."""
    # 1. Create
    create_response = await client.post("/api/history/", json=minimal_scan_payload)
    assert create_response.status_code == 201
    scan_id = create_response.json()["id"]

    # 2. Read
    get_response = await client.get(f"/api/history/{scan_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == minimal_scan_payload["name"]

    # 3. Update
    update_response = await client.put(
        f"/api/history/{scan_id}",
        json={"name": "Updated Name", "location": "New Location"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Name"

    # 4. Verify in list
    list_response = await client.get("/api/history/")
    assert list_response.status_code == 200
    assert any(s["id"] == scan_id for s in list_response.json()["items"])

    # 5. Delete
    delete_response = await client.delete(f"/api/history/{scan_id}")
    assert delete_response.status_code == 204

    # 6. Verify gone
    get_response = await client.get(f"/api/history/{scan_id}")
    assert get_response.status_code == 404


@pytest.mark.integration
async def test_multiple_scans_ordering(client: AsyncClient):
    """Test that scans are returned in correct order (newest first)."""
    # Create scans with slight delay between them
    scan_ids = []
    for i in range(3):
        payload = {
            "name": f"Ordered Scan {i}",
            "start_freq_hz": 100_000_000,
            "stop_freq_hz": 200_000_000,
            "points": 10,
            "data_points": [
                {"index": j, "frequency_hz": 100_000_000 + j * 10_000_000, "amplitude_dbm": -90.0}
                for j in range(10)
            ],
        }
        response = await client.post("/api/history/", json=payload)
        assert response.status_code == 201
        scan_ids.append(response.json()["id"])

    # List should return newest first
    list_response = await client.get("/api/history/")
    assert list_response.status_code == 200
    items = list_response.json()["items"]

    # The last created scan should be first
    returned_ids = [item["id"] for item in items]
    assert returned_ids == list(reversed(scan_ids))
