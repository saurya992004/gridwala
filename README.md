# Gridwala

Gridwala is a full-stack smart-grid simulation repository built around the NEXUS GRID platform: an AI-assisted control room experience for modeling district energy usage, carbon intensity, and resilience scenarios in real time.

The project pairs a FastAPI backend that runs the simulation and streams telemetry over WebSockets with a Next.js dashboard that visualizes district behavior, operator controls, and live rationale feeds.

## Highlights

- Real-time smart-grid telemetry streamed over WebSockets
- FastAPI backend with schema validation and preset-driven simulations
- Next.js dashboard for district visualization, metrics, and operator controls
- Scenario controls for emergency injection and forecast-based drills
- Carbon and energy analytics designed for demos, experimentation, and product storytelling

## Repository Layout

```text
devpost/
|-- README.md
|-- .gitignore
|-- LICENSE
|-- docs/
|   `-- implementation-plan-citylearn.md
`-- nexus-grid/
    |-- backend/
    |   |-- main.py
    |   |-- requirements.txt
    |   |-- run_test.py
    |   `-- nexusgrid/
    |       |-- core/
    |       `-- presets/
    `-- frontend/
        |-- package.json
        `-- src/
            |-- app/
            |-- components/
            `-- hooks/
```

## Tech Stack

- Backend: Python, FastAPI, Uvicorn, WebSockets
- Simulation: custom smart-grid environment, reinforcement-learning-oriented orchestration, schema presets
- Frontend: Next.js, React, TypeScript, Framer Motion, Recharts
- Tooling: ESLint, npm, pip

## Getting Started

### 1. Backend

```bash
cd nexus-grid/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_test.py
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

### 2. Frontend

```bash
cd nexus-grid/frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## API Surface

- `GET /` - basic service health
- `GET /status` - structured status response
- `GET /api/presets` - list built-in simulation presets and carbon profiles
- `GET /api/presets/{preset_id}` - fetch a preset schema
- `POST /api/validate` - validate a custom simulation schema
- `WS /ws/simulate` - stream live simulation telemetry and control messages

## Development Notes

- The product-facing application lives in `nexus-grid/`; the root `docs/` folder contains planning and supporting material.
- Start the backend before the frontend so the dashboard can connect to the simulation stream immediately.
- Local caches, virtual environments, and generated assets are intentionally excluded from version control.

## Scripts

### Backend

- `python run_test.py` - smoke test the simulation engine
- `uvicorn main:app --reload --port 8000` - run the API locally

### Frontend

- `npm run dev` - start the Next.js development server
- `npm run build` - create a production build
- `npm run start` - run the production build
- `npm run lint` - run lint checks

## License

MIT
