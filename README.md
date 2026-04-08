# Gridwala

Gridwala is the repository wrapper for **NEXUS GRID**, an AI-powered smart-grid orchestration platform designed for sustainable city districts. It turns a simulation-heavy energy system into a polished operator experience with a live digital twin, explainable agent decisions, resilience drills, and a carbon-aware control loop.

Instead of presenting smart-grid optimization as raw backend logic, this project frames it as a real product: a command-center dashboard backed by a FastAPI simulation engine that streams telemetry in real time to a Next.js frontend.

## Problem

Modern energy orchestration tools often struggle in four places:

- decision-making is hard to explain to operators
- carbon optimization is treated as a metric, not an economic system
- simulation outputs are difficult to demo or monitor visually
- resilience under sudden shocks is rarely exposed through a usable interface

Gridwala addresses those gaps through the NEXUS GRID application layer.

## What NEXUS GRID Does

NEXUS GRID models a district-scale smart grid where multiple buildings participate in a shared energy ecosystem. The backend runs a live simulation with preset districts and schema-aware configuration, while the frontend acts as an operations dashboard.

The platform is centered on four product ideas:

1. **Explainable AI operations**
   Every simulation cycle can produce natural-language rationales so operators can understand why the system is shifting load, pausing, reacting to shocks, or prioritizing certain energy behavior.

2. **Carbon-aware economic behavior**
   The platform tracks carbon intensity and peer-to-peer energy activity so optimization is not only technical, but also framed in market and sustainability terms.

3. **Digital twin visualization**
   Instead of terminal output, the system presents live district status through a responsive dashboard, metrics cards, charts, and building-level panels.

4. **Resilience drills**
   Operators can simulate adverse events such as carbon spikes and forecasted heatwaves to observe how the system behaves under stress.

## Key Features

- FastAPI backend for simulation control, presets, validation, and health endpoints
- WebSocket streaming for real-time telemetry
- Next.js dashboard with a district twin view and economy view
- Live status cards for carbon intensity, district load, and P2P volume
- Preset-driven simulation scenarios including residential, university, and industrial districts
- Operator controls for pause, resume, emergency events, forecast events, and speed changes
- Schema validation endpoint for custom district definitions
- AI rationale feed surfaced as an operator-facing stream

## Demo Experience

The intended user flow is:

1. start the backend simulation engine
2. open the frontend dashboard
3. watch the district twin connect over WebSocket
4. observe live carbon, load, and peer-to-peer energy activity
5. trigger a forecast or emergency scenario
6. inspect how the system adapts in the dashboard and rationale stream

## Architecture

```text
Gridwala Repository
|
|-- README.md
|-- LICENSE
|-- docs/
|   `-- implementation-plan-citylearn.md
`-- nexus-grid/
    |-- backend/
    |   |-- main.py                 FastAPI entrypoint
    |   |-- requirements.txt
    |   |-- run_test.py             smoke test
    |   `-- nexusgrid/
    |       |-- core/               simulation and orchestration logic
    |       `-- presets/            district preset schemas
    `-- frontend/
        |-- package.json
        `-- src/
            |-- app/                Next.js app shell
            |-- components/         UI visualizations
            `-- hooks/              WebSocket integration
```

## Presets

The backend currently exposes built-in district presets through the API:

- `residential_district`
- `university_campus`
- `industrial_microgrid`

These are available from `GET /api/presets`, and each schema can be fetched individually for inspection or extension.

## API Surface

- `GET /`
  Returns a basic service health response.
- `GET /status`
  Returns structured backend status metadata.
- `GET /api/presets`
  Lists available built-in presets and carbon profiles.
- `GET /api/presets/{preset_id}`
  Returns a full schema for a named preset.
- `POST /api/validate`
  Validates a custom Nexus schema payload.
- `WS /ws/simulate`
  Streams live simulation events and accepts operator control messages.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, WebSockets
- **Frontend:** Next.js, React, TypeScript
- **Visualization:** Framer Motion, Recharts, custom dashboard components
- **Simulation Layer:** schema-driven district modeling and orchestration logic

## Local Setup

### Backend

```bash
cd nexus-grid/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_test.py
uvicorn main:app --reload --port 8000
```

Backend runs on `http://localhost:8000`.

### Frontend

```bash
cd nexus-grid/frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

## Developer Notes

- The root repository contains product documentation and project framing.
- The main application code lives under `nexus-grid/`.
- The file in `docs/implementation-plan-citylearn.md` captures the original build strategy and product positioning.
- Local caches, virtual environments, generated output, and local tooling folders are excluded from version control.

## Validation

The repository has already been sanity-checked with:

- backend smoke test via `python run_test.py`
- frontend lint via `npm run lint`

## License

MIT
