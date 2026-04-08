"""
NEXUS GRID — FastAPI Backend
Entry point for the NEXUS GRID API server.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nexusgrid.core.simulation_runner import SimulationRunner
from nexusgrid.core.schema_loader import load_from_dict, load_from_file, SchemaValidationError
from nexusgrid.core.carbon_profiles import list_profiles

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NEXUS GRID API",
    description="AI-powered Plug-and-Play Smart Grid Orchestration Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Presets directory
PRESETS_DIR = Path(__file__).parent / "nexusgrid" / "presets"

PRESET_META = {
    "residential_district": {
        "label": "🏘️ Residential District",
        "description": "5 typical UK residential homes with rooftop solar and home batteries",
        "file": "residential_district.json",
    },
    "university_campus": {
        "label": "🎓 University Campus",
        "description": "Mixed campus microgrid: lecture halls, dorms, library, admin building",
        "file": "university_campus.json",
    },
    "industrial_microgrid": {
        "label": "🏭 Industrial Microgrid (India)",
        "description": "Factory, warehouses, and EV charging hub on Maharashtra grid",
        "file": "industrial_microgrid.json",
    },
}

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {"status": "NEXUS GRID API is running", "version": "2.0.0"}


@app.get("/status", tags=["Health"])
def status():
    return {"status": "ok", "service": "nexus-grid-backend", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# Plug-and-Play API — Presets & Schema
# ---------------------------------------------------------------------------

@app.get("/api/presets", tags=["Schema"])
def get_presets():
    """List all available built-in simulation presets."""
    return {
        "presets": [
            {"id": k, **v}
            for k, v in PRESET_META.items()
        ],
        "carbon_profiles": list_profiles(),
    }


@app.get("/api/presets/{preset_id}", tags=["Schema"])
def get_preset_schema(preset_id: str):
    """Return the full JSON schema for a named preset."""
    if preset_id not in PRESET_META:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    path = PRESETS_DIR / PRESET_META[preset_id]["file"]
    try:
        schema = load_from_file(path)
        return {"preset_id": preset_id, "schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SchemaPayload(BaseModel):
    schema_data: dict


@app.post("/api/validate", tags=["Schema"])
def validate_schema(payload: SchemaPayload):
    """
    Validate a custom Nexus Schema JSON.
    Returns the validated + normalised schema, or validation errors.
    """
    try:
        validated = load_from_dict(payload.schema_data)
        return {
            "valid": True,
            "schema": validated,
            "building_count": len(validated["buildings"]),
        }
    except SchemaValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# WebSocket — Schema-Aware Live Simulation Stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/simulate")
async def ws_simulate(
    websocket: WebSocket,
    preset: Optional[str] = Query(default=None, description="Preset ID to run"),
):
    """
    WebSocket endpoint for live simulation streaming.

    Connect with:
      ws://localhost:8000/ws/simulate               → default demo district
      ws://localhost:8000/ws/simulate?preset=residential_district
      ws://localhost:8000/ws/simulate?preset=university_campus
      ws://localhost:8000/ws/simulate?preset=industrial_microgrid

    After connecting, send a custom schema to override:
      {"action": "load_schema", "schema": { ...nexus schema dict... }}

    Other controls:
      {"action": "pause"}
      {"action": "resume"}
      {"action": "set_speed", "value": 5.0}
      {"action": "emergency", "scenario": "solar_offline|carbon_spike|heatwave"}
      {"action": "clear_emergency"}
    """
    await websocket.accept()

    # Load schema from preset query param if provided
    schema = None
    if preset and preset in PRESET_META:
        try:
            schema = load_from_file(PRESETS_DIR / PRESET_META[preset]["file"])
        except Exception:
            schema = None  # Fall back to default

    runner = SimulationRunner(schema=schema)

    await websocket.send_json({
        "type": "connected",
        "district_name": runner.env._district_name,
        "buildings": runner.env.building_names,
        "max_steps": runner.env.max_steps,
        "preset": preset or "default",
    })

    async def _sender():
        try:
            async for payload in runner.run(speed=runner._speed):
                payload["type"] = "step"
                await websocket.send_json(payload)
            await websocket.send_json({"type": "done"})
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    async def _receiver():
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                    await _handle_control(msg, runner)
                except json.JSONDecodeError:
                    pass
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    sender_task = asyncio.create_task(_sender())
    receiver_task = asyncio.create_task(_receiver())

    done, pending = await asyncio.wait(
        [sender_task, receiver_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def _handle_control(msg: Dict, runner: SimulationRunner):
    """Route control messages from frontend to the runner."""
    action = msg.get("action")
    if action == "pause":
        runner.pause()
    elif action == "resume":
        runner.resume()
    elif action == "set_speed":
        runner._speed = float(msg.get("value", 2.0))
    elif action == "emergency":
        runner.inject_emergency(msg.get("scenario", ""))
    elif action == "forecast_emergency":
        steps = int(msg.get("steps", 4))
        runner.inject_forecast(msg.get("scenario", ""), steps)
    elif action == "clear_emergency":
        runner.clear_emergency()
    elif action == "load_schema":
        # Allows live schema swapping (not mid-simulation, restarts sim)
        raw_schema = msg.get("schema", {})
        try:
            validated = load_from_dict(raw_schema)
            runner.env.__init__(schema=validated)
            runner.env.reset()
        except SchemaValidationError:
            pass  # Keep running existing simulation on bad schema


