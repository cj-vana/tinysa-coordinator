# TinySA Coordinator

[![CI](https://github.com/cj-vana/frequency-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/cj-vana/frequency-scanner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)

A web application for controlling TinySA Ultra spectrum analyzers and exporting scans to professional RF coordination software like Shure Wireless Workbench and Sennheiser WSM.

## Features

- **Real-time Spectrum Display** - Live visualization of RF scans via WebSocket streaming
- **Frequency Presets** - Built-in presets for common wireless bands (UHF, VHF, ISM)
- **Scan History** - Save scans with location, notes, and metadata
- **Multi-format Export**:
  - Shure Wireless Workbench (WWB) CSV
  - Sennheiser Wireless Systems Manager (WSM) CSV
  - Raw CSV with timestamps

## Screenshots

<!-- TODO: Add screenshots of the application -->
*Coming soon - screenshots of the spectrum display, scan history, and export dialogs.*

## Quick Start

### One-liner Install

```bash
curl -sSL https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/scripts/install.sh | bash
```

This script will:
- Check for required dependencies (Python 3.9+, Node.js 18+)
- Clone the repository
- Set up the Python virtual environment
- Install all dependencies
- Provide instructions for running the application

### Docker Quick Start

The fastest way to get started if you have Docker installed:

```bash
# Clone the repository
git clone https://github.com/cj-vana/frequency-scanner.git
cd frequency-scanner

# Start with Docker Compose
docker compose up -d
```

Access the application at http://localhost:3000 (frontend) and http://localhost:8000 (API).

To stop:

```bash
docker compose down
```

### Manual Installation

```bash
# Clone the repo
git clone https://github.com/cj-vana/frequency-scanner.git
cd frequency-scanner

# Install all dependencies
make install

# Start development servers
make dev
```

Open http://localhost:5173 in your browser.

## Development Setup

### Requirements

- TinySA Ultra spectrum analyzer
- Python 3.10+
- Node.js 18+
- macOS, Linux, or Windows

### Using Make (Recommended)

The project includes a comprehensive Makefile for common development tasks:

```bash
make install          # Install all dependencies
make dev              # Start both servers concurrently
make dev-backend      # Start backend only (http://localhost:8000)
make dev-frontend     # Start frontend only (http://localhost:5173)
```

### Available Make Targets

| Command | Description |
|---------|-------------|
| `make help` | Display all available commands |
| **Installation** | |
| `make install` | Install all dependencies (backend + frontend) |
| `make install-backend` | Install Python backend dependencies |
| `make install-frontend` | Install Node.js frontend dependencies |
| **Development** | |
| `make dev` | Start both backend and frontend servers |
| `make dev-backend` | Start FastAPI backend on port 8000 |
| `make dev-frontend` | Start Vite frontend on port 5173 |
| **Building** | |
| `make build` | Build the project for production |
| `make build-frontend` | Build frontend to `frontend/dist` |
| **Code Quality** | |
| `make lint` | Run all linters (backend + frontend) |
| `make lint-backend` | Lint Python code with Ruff |
| `make lint-frontend` | Lint TypeScript/React with ESLint |
| `make typecheck` | Run TypeScript type checking |
| `make format` | Format code (Ruff + Prettier) |
| **Testing** | |
| `make test` | Run all tests |
| **Docker** | |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run with docker-compose |
| `make docker-stop` | Stop containers |
| `make docker-logs` | View container logs |
| **Utilities** | |
| `make clean` | Clean generated files and caches |
| `make clean-all` | Clean everything including node_modules and venv |
| `make check-deps` | Check if required tools are installed |
| `make db-init` | Initialize the SQLite database |

### Manual Setup

If you prefer not to use Make:

**Backend:**

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Run backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
# Install Node dependencies
cd frontend
npm install

# Run frontend
npm run dev
```

### API Documentation

When the backend is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
frequency-scanner/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── api/                # API routes
│   ├── core/               # Core configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API client services
│   │   └── types/          # TypeScript types
│   └── package.json
├── scripts/
│   ├── install.sh          # One-liner install script
│   └── run_dev.sh          # Development server runner
├── Makefile                # Development commands
├── requirements.txt        # Python dependencies
└── README.md
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, pyserial
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **Database**: SQLite
- **Real-time**: WebSockets for live scan streaming

## TinySA Ultra Connection

The application communicates with the TinySA Ultra via USB serial. The device typically appears as:
- **macOS**: `/dev/cu.usbmodem4001`
- **Linux**: `/dev/ttyACM0`
- **Windows**: `COM3` (or similar)

Ensure your user has permission to access the serial port. On Linux, you may need to add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

## Export Formats

### Shure Wireless Workbench (WWB)
- 2-column CSV format
- Frequency in MHz, amplitude in dBm
- No headers

### Sennheiser WSM
- Semicolon-delimited CSV
- Includes header row with metadata

### Raw CSV
- Full CSV with timestamps and all metadata
- Useful for archiving and custom analysis

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up your development environment
- Coding standards and style guides
- Commit message conventions
- Pull request process

## License

MIT
