# TinySA Coordinator

A web application for controlling TinySA Ultra spectrum analyzers and exporting scans to professional RF coordination software like Shure Wireless Workbench and Sennheiser WSM.

## Features

- **Real-time Spectrum Display** - Live visualization of RF scans via WebSocket streaming
- **Frequency Presets** - Built-in presets for common wireless bands (UHF, VHF, ISM)
- **Scan History** - Save scans with location, notes, and metadata
- **Multi-format Export**:
  - Shure Wireless Workbench (WWB) CSV
  - Sennheiser Wireless Systems Manager (WSM) CSV
  - Raw CSV with timestamps

## Requirements

- TinySA Ultra spectrum analyzer
- Python 3.9+
- Node.js 18+
- macOS, Linux, or Windows

## Quick Start

```bash
# Clone the repo
git clone https://github.com/cj-vana/frequency-scanner.git
cd frequency-scanner

# Backend setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Run development servers
./scripts/run_dev.sh
```

Open http://localhost:5173 in your browser.

## Development Setup

### Prerequisites

1. **Python 3.9+** - Download from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/) or use nvm
3. **TinySA Ultra** - Connected via USB (typically appears as `/dev/cu.usbmodem4001` on macOS)

### Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install
cd ..
```

### Running Development Servers

The easiest way to run both servers is with the provided script:

```bash
./scripts/run_dev.sh
```

This will:
- Start the FastAPI backend on http://localhost:8000
- Start the Vite frontend on http://localhost:5173
- Handle graceful shutdown of both when you press Ctrl+C

#### Running Servers Individually

If you prefer to run the servers separately:

**Backend:**
```bash
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
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
│   └── run_dev.sh          # Development server runner
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

## License

MIT
