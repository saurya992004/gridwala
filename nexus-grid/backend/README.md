# NEXUS GRID Backend

This service exposes the FastAPI API, simulation presets, schema validation, and WebSocket telemetry stream used by the NEXUS GRID dashboard.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python run_test.py
uvicorn main:app --reload --port 8000
```

## Main Responsibilities

- Serve health and status endpoints
- Validate and load simulation schemas
- Stream live simulation steps over WebSockets
- Accept operator control messages for pause, resume, speed, forecast, and emergency scenarios
