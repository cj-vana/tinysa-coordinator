"""
Tests for the health check endpoint.

These tests verify that the basic API infrastructure is working correctly,
including database connectivity verification.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_health_check(client: AsyncClient):
    """Test that the health check endpoint returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.unit
async def test_health_check_response_format(client: AsyncClient):
    """Test that health check returns expected JSON format."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert "status" in data


@pytest.mark.unit
async def test_health_check_detailed_response(client: AsyncClient):
    """Test that health check returns detailed component status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "components" in data

    # Status should be one of the valid values
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

    # Version should match app version
    assert data["version"] == "0.1.0"


@pytest.mark.unit
async def test_health_check_database_component(client: AsyncClient):
    """Test that health check includes database component status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Database component should be present
    assert "database" in data["components"]

    db_component = data["components"]["database"]
    assert "status" in db_component
    assert "message" in db_component
    assert "latency_ms" in db_component

    # Database should be healthy in test environment
    assert db_component["status"] == "healthy"
    assert db_component["latency_ms"] >= 0


@pytest.mark.unit
async def test_health_check_timestamp_format(client: AsyncClient):
    """Test that health check timestamp is in ISO 8601 format."""
    from datetime import datetime

    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Timestamp should be parseable as ISO 8601
    timestamp = data["timestamp"]
    # Should not raise an exception
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
