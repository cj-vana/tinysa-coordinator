"""
Pydantic schemas for health check responses.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status for an individual component."""

    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Optional status message")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")


class HealthCheckResponse(BaseModel):
    """Detailed health check response."""

    status: HealthStatus = Field(..., description="Overall system health status")
    timestamp: datetime = Field(..., description="Timestamp of health check")
    version: str = Field(..., description="Application version")
    components: Dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Individual component health statuses"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "0.1.0",
                "components": {
                    "database": {
                        "status": "healthy",
                        "message": "Database connection successful",
                        "latency_ms": 1.5,
                    }
                },
            }
        }
    }
