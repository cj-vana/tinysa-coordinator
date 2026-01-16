"""
Tests for the health check endpoint.

These tests verify that the basic API infrastructure is working correctly.
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
