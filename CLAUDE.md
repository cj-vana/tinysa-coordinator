# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TinySA Coordinator is a full-stack web application for controlling TinySA Ultra spectrum analyzers and exporting scan data to professional RF coordination software (Shure WWB, Sennheiser WSM). It features real-time spectrum visualization via WebSockets, scan history management, and frequency presets.

## Architecture

### Backend (Python/FastAPI)
- **Entry Point**: `backend/main.py` - FastAPI app with lifespan management
- **API Routes**: `backend/api/routes/` - REST endpoints (device, history, presets, export)
- **WebSocket**: `backend/api/websocket/scan_ws.py` - Real-time scan streaming
- **Services**: `backend/services/` - Business logic layer
- **Core**: `backend/core/tinysa.py` - TinySA serial communication, `connection_manager.py` - WebSocket management
- **Database**: `backend/db/` - SQLAlchemy models with SQLite, async sessions

### Frontend (React/TypeScript/Vite)
- **Entry Point**: `frontend/src/main.tsx`
- **Pages**: `frontend/src/pages/` - ScanPage, HistoryPage, SettingsPage
- **Components**: `frontend/src/components/` - Organized by feature (scan, history, device, export, presets)
- **Hooks**: `frontend/src/hooks/` - Custom hooks for data fetching (useDevice, useHistory, usePresets, useScanData)
- **API Layer**: `frontend/src/lib/api.ts` - REST client, `websocket.ts` - WebSocket client

## Build and Development Commands

```bash
# Using Makefile (recommended)
make install          # Install all dependencies
make dev              # Start both servers concurrently
make dev-backend      # Start backend only (http://localhost:8000)
make dev-frontend     # Start frontend only (http://localhost:5173)
make build            # Build frontend for production
make lint             # Run all linters
make typecheck        # TypeScript type checking
make clean            # Clean generated files

# Manual commands
source venv/bin/activate                    # Activate Python venv
uvicorn backend.main:app --reload --port 8000  # Run backend
cd frontend && npm run dev                  # Run frontend
cd frontend && npm run build                # Build frontend
cd frontend && npm run lint                 # ESLint
```

## Code Quality

### Backend Linting/Formatting
- **Ruff**: Linting (`ruff check backend/`) and formatting (`ruff format backend/`)
- **MyPy**: Type checking (`mypy backend/ --ignore-missing-imports`)

### Frontend Linting/Formatting
- **ESLint**: `npm run lint` in frontend/
- **TypeScript**: `npx tsc -b --noEmit` for type checking

## Key Patterns

### Backend
- Async/await throughout (FastAPI, SQLAlchemy, pyserial operations)
- Pydantic schemas in `backend/schemas/` for request/response validation
- Service layer pattern - routes call services, services handle business logic
- WebSocket for real-time scan data streaming to frontend

### Frontend
- React Query (@tanstack/react-query) for server state management
- Custom hooks abstract data fetching logic
- Tailwind CSS for styling
- Recharts for spectrum visualization

## API Documentation

When backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

- SQLite database at `data/scanner.db`
- Auto-initialized on first run with built-in presets seeded
- Models in `backend/db/models.py` (Scan, ScanPoint, Preset)

## Docker

```bash
make docker-build     # Build production image
make docker-run       # Run with docker-compose
make docker-stop      # Stop containers
```

The Dockerfile uses multi-stage builds: Node.js builds frontend, Python serves both backend API and static files.

## Hardware Communication

TinySA Ultra connects via USB serial:
- macOS: `/dev/cu.usbmodem4001`
- Linux: `/dev/ttyACM0`
- Windows: `COM3` (varies)

Serial communication handled in `backend/core/tinysa.py` using pyserial.
