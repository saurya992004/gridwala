<div align="center">
  <h1>NEXUS GRID</h1>
  <p><strong>City-to-digital-twin grid intelligence platform for live operations, resilience drills, and multi-agent control.</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
  [![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
  [![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)
</div>

## Live Demo

- Frontend control room: [https://gridwala-nexusgrid-frontend.onrender.com](https://gridwala-nexusgrid-frontend.onrender.com)
- Backend health/API: [https://gridwala-nexusgrid-backend.onrender.com/status](https://gridwala-nexusgrid-backend.onrender.com/status)

The frontend link is the main one to share with judges. I am also exposing the backend health link because technical reviewers often want a quick proof that the API is live. On free Render, cold starts can add a short delay, so the app should still open from the frontend link, but the first load may take a little longer after inactivity.

## Problem Statement

Modern grids are no longer simple top-down systems. Demand is volatile, distributed energy resources are fragmented, and operators need to reason across carbon, tariffs, weather, feeder stress, and local resilience at the same time.

Most tools still break this workflow apart into static dashboards, fixed heuristics, and manually configured simulations. That makes it hard to answer a simple operational question:

**If a real city is under changing grid conditions, what should the system do next and why?**

## What NexusGrid Does

NexusGrid turns a city or coordinate into a live operational twin, enriches it with real-world signals, and runs a control loop that can simulate market conditions, topology stress, and emergency events inside a single control room.

Core capabilities:

- City-to-twin generation from place names or coordinates
- Live weather, carbon, and tariff enrichment
- Map-first operator dashboard with WebSocket telemetry
- Feeder and topology stress simulation
- Emergency injection for drills like feeder fault, congestion, and derating
- Multi-entity control with DQN and rule-based fallback
- P2P energy trading signals between control entities

## Architecture At A Glance

- Frontend: Next.js, React, TypeScript, MapLibre
- Backend: FastAPI, WebSockets, Python
- Simulation: custom environment, topology runtime, emergency event engine
- Intelligence layer: PyTorch DQN runtime plus rule-based control fallback
- External context: Electricity Maps, Open-Meteo, OpenEI
- Deployment: Render frontend + Render backend

## Judge Quick Start

If you only want to see the product, open the live frontend:

```text
https://gridwala-nexusgrid-frontend.onrender.com
```

If you want to run it locally, use the boot scripts below.

### One-Click Local Boot

Prerequisites:

- Python 3.11+
- Node.js 20+ with npm

Windows:

```cmd
start.bat
```

Mac/Linux:

```bash
chmod +x start.sh
./start.sh
```

What the scripts do:

- create the backend virtual environment if needed
- install Python dependencies, including PyTorch
- install frontend dependencies
- start the backend on `http://localhost:8000`
- start the frontend on `http://localhost:3000`

First run can take a few minutes because dependencies are installed automatically.

## Manual Local Setup

Backend:

```bash
cd nexus-grid/backend
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd nexus-grid/frontend
npm install
npm run dev
```

## Validation

The project has been smoke-tested across:

- backend health and simulation boot
- city-to-twin generation
- geo enrichment
- topology constraints
- frontend lint/build checks
- live Render deployment

## Project Docs

- [Execution roadmap](docs/nexus-grid-execution-roadmap.md)
- [Render deployment guide](docs/render-deployment.md)
- [Presentation script](presentation.md)

## License

MIT
