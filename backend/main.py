"""
FastAPI application entry point for the TinySA frequency scanner.

Run with:
    uvicorn backend.main:app --reload
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from backend.api.middleware import RequestIDMiddleware, register_exception_handlers
from backend.api.routes.device import router as device_router
from backend.api.routes.export import router as export_router
from backend.api.routes.history import router as history_router
from backend.api.routes.presets import router as presets_router
from backend.api.websocket.scan_ws import scan_websocket
from backend.core.connection_manager import get_connection_manager
from backend.core.logging import setup_logging
from backend.core.rate_limit import get_limiter, get_rate_limit_config
from backend.db.database import async_session_maker, close_db, get_async_session, init_db
from backend.db.seed import seed_builtin_presets
from backend.schemas.health import ComponentHealth, HealthCheckResponse, HealthStatus

# Initialize logging before anything else
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT_JSON = os.environ.get("LOG_FORMAT", "text").lower() == "json"
setup_logging(level=LOG_LEVEL, json_format=LOG_FORMAT_JSON)

# CORS configuration
# In production, set ALLOWED_ORIGINS to a comma-separated list of allowed origins
# Example: ALLOWED_ORIGINS="https://myapp.example.com,https://api.example.com"
# If not set, defaults to localhost origins for development
DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
ALLOWED_ORIGINS_ENV = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = (
    [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",") if origin.strip()]
    if ALLOWED_ORIGINS_ENV
    else DEFAULT_ORIGINS
)

logger = logging.getLogger(__name__)

# Static files directory for production builds
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting TinySA Frequency Scanner API")
    logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
    await init_db()
    logger.info("Database initialized")

    # Seed built-in presets
    async for session in get_async_session():
        count = await seed_builtin_presets(session)
        if count > 0:
            logger.info(f"Seeded {count} built-in presets")
        break

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Shutting down application")

    # Gracefully close WebSocket connections before shutting down
    connection_manager = get_connection_manager()
    await connection_manager.graceful_shutdown("Server shutting down")

    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title="TinySA Frequency Scanner",
    description="API for controlling TinySA Ultra spectrum analyzer and managing scan data",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure rate limiting
limiter = get_limiter()
rate_config = get_rate_limit_config()
app.state.limiter = limiter

# Register centralized exception handlers
register_exception_handlers(app)

# Register rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)

# Configure CORS - uses ALLOWED_ORIGINS environment variable in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(device_router)
app.include_router(export_router, prefix="/api")
app.include_router(history_router)
app.include_router(presets_router)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint with detailed component status.

    Returns overall system health including database connectivity verification.
    """
    components: Dict[str, ComponentHealth] = {}
    overall_status = HealthStatus.HEALTHY

    # Check database connectivity
    db_status = await _check_database_health()
    components["database"] = db_status
    if db_status.status == HealthStatus.UNHEALTHY:
        overall_status = HealthStatus.UNHEALTHY
    elif db_status.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=app.version,
        components=components,
    )


async def _check_database_health() -> ComponentHealth:
    """Check database connectivity and return health status."""
    start_time = time.perf_counter()
    try:
        async with async_session_maker() as session:
            # Execute a simple query to verify connectivity
            await session.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Consider database degraded if latency is high (>500ms)
            if latency_ms > 500:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    message="Database connection slow",
                    latency_ms=round(latency_ms, 2),
                )

            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                latency_ms=round(latency_ms, 2),
            )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {type(e).__name__}",
            latency_ms=round(latency_ms, 2),
        )


@app.websocket("/ws/scan")
async def websocket_scan_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time scan data streaming."""
    await scan_websocket(websocket)


# Serve static files in production (when static directory exists)
if STATIC_DIR.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the SPA frontend for all non-API routes."""
        # Check if the file exists in static directory
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")
