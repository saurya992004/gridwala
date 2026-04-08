# NEXUS GRID

NEXUS GRID is the core application inside the Gridwala repository. It combines a FastAPI simulation backend with a Next.js operator dashboard for experimenting with district energy orchestration, carbon-aware controls, and resilience scenarios.

## Services

- `backend/` hosts the FastAPI app, simulation engine, preset loading, and smoke tests
- `frontend/` hosts the Next.js dashboard, visualization components, and WebSocket client hooks

## Local Runbook

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_test.py
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Key Endpoints

- `GET /status`
- `GET /api/presets`
- `GET /api/presets/{preset_id}`
- `POST /api/validate`
- `WS /ws/simulate`
