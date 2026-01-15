"""
FastAPI application entry point for the TinySA frequency scanner.

Run with:
    uvicorn backend.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes.device import router as device_router
from backend.api.routes.history import router as history_router
from backend.api.routes.presets import router as presets_router
from backend.api.websocket.scan_ws import scan_websocket
from backend.db.database import close_db, get_async_session, init_db
from backend.db.seed import seed_builtin_presets

# Static files directory for production builds
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    await init_db()
    # Seed built-in presets
    async for session in get_async_session():
        count = await seed_builtin_presets(session)
        if count > 0:
            print(f"Seeded {count} built-in presets")
        break
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="TinySA Frequency Scanner",
    description="API for controlling TinySA Ultra spectrum analyzer and managing scan data",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(device_router)
app.include_router(history_router)
app.include_router(presets_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


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
