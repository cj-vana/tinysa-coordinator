"""
FastAPI application for TinySA Ultra Frequency Scanner.

This module sets up the FastAPI application with CORS middleware
and includes all API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the application.
    """
    # Startup: Initialize resources
    # TODO: Initialize database connection
    # TODO: Initialize serial connection to TinySA
    yield
    # Shutdown: Clean up resources
    # TODO: Close database connection
    # TODO: Close serial connection


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Web application for controlling a TinySA Ultra spectrum analyzer",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# Placeholder for router includes
# These will be uncommented as routers are implemented:
#
# from backend.api.routes import scans, exports, device
# app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
# app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
# app.include_router(device.router, prefix="/api/device", tags=["device"])
#
# from backend.api.websocket import handlers
# app.include_router(handlers.router, prefix="/ws", tags=["websocket"])
