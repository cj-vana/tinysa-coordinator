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
git clone https://github.com/yourusername/tinysa-coordinator.git
cd tinysa-coordinator

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

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, pyserial
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **Database**: SQLite

## License

MIT
