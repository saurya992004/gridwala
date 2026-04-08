"""
NEXUS GRID - FastAPI Backend
Entry point for the NEXUS GRID API server.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nexusgrid.core.carbon_profiles import list_profiles
from nexusgrid.core.environment import ENGINE_MODE, ENGINE_NAME, ENGINE_VERSION
from nexusgrid.core.model_registry import get_model, list_models
from nexusgrid.core.schema_loader import (
    SchemaValidationError,
    load_from_dict,
    load_from_file,
)
from nexusgrid.geo.service import DISTRICT_LABELS, GeoResolutionError, geo_service
from nexusgrid.core.simulation_runner import SimulationRunner


app = FastAPI(
    title="NEXUS GRID API",
    description="AI-powered plug-and-play smart grid orchestration platform",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRESETS_DIR = Path(__file__).parent / "nexusgrid" / "presets"

PRESET_META = {
    "residential_district": {
        "label": "Residential District",
        "description": "5 typical UK residential homes with rooftop solar and home batteries",
        "file": "residential_district.json",
    },
    "university_campus": {
        "label": "University Campus",
        "description": "Mixed campus microgrid: lecture halls, dorms, library, admin building",
        "file": "university_campus.json",
    },
    "industrial_microgrid": {
        "label": "Industrial Microgrid (India)",
        "description": "Factory, warehouses, and EV charging hub on Maharashtra grid",
        "file": "industrial_microgrid.json",
    },
}


def _engine_descriptor():
    return {
        "engine_mode": ENGINE_MODE,
        "engine_name": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "NEXUS GRID API is running",
        "version": "2.1.0",
        **_engine_descriptor(),
    }


@app.get("/status", tags=["Health"])
def status():
    return {
        "status": "ok",
        "service": "nexus-grid-backend",
        "version": "2.1.0",
        **_engine_descriptor(),
        "available_models": len(list_models()),
    }


@app.get("/api/presets", tags=["Schema"])
def get_presets():
    return {
        "presets": [{"id": preset_id, **meta} for preset_id, meta in PRESET_META.items()],
        "carbon_profiles": list_profiles(),
    }


@app.get("/api/presets/{preset_id}", tags=["Schema"])
def get_preset_schema(preset_id: str):
    if preset_id not in PRESET_META:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")

    path = PRESETS_DIR / PRESET_META[preset_id]["file"]
    try:
        schema = load_from_file(path)
        return {"preset_id": preset_id, "schema": schema}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class SchemaPayload(BaseModel):
    schema_data: dict


class GeoResolvePayload(BaseModel):
    query: str
    provider: str = "auto"
    limit: int = 5


class GeoSchemaPayload(BaseModel):
    query: str
    provider: str = "auto"
    district_type: str = "auto"
    building_count: Optional[int] = None


@app.post("/api/validate", tags=["Schema"])
def validate_schema(payload: SchemaPayload):
    try:
        validated = load_from_dict(payload.schema_data)
        return {
            "valid": True,
            "schema": validated,
            "building_count": len(validated["buildings"]),
        }
    except SchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/geo/providers", tags=["Geo"])
def get_geo_providers():
    return {
        **_engine_descriptor(),
        "providers": geo_service.list_providers(),
        "district_types": ["auto", *DISTRICT_LABELS.keys()],
        "phase": "1A",
        "recommended_future_apis": [
            "Electricity Maps for live carbon intensity",
            "Open-Meteo or NASA POWER for weather and solar context",
            "OpenEI or utility-specific tariff feeds for price signals",
        ],
    }


@app.post("/api/geo/resolve", tags=["Geo"])
def resolve_geo_location(payload: GeoResolvePayload):
    try:
        result = geo_service.resolve(
            query=payload.query,
            provider=payload.provider,
            limit=payload.limit,
        )
        result["phase"] = "1A"
        return result
    except GeoResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/geo/schema", tags=["Geo"])
def generate_geo_schema(payload: GeoSchemaPayload):
    try:
        result = geo_service.generate_schema(
            query=payload.query,
            provider=payload.provider,
            district_type=payload.district_type,
            building_count=payload.building_count,
        )
        result["phase"] = "1A"
        result["building_count"] = len(result["schema"]["buildings"])
        return result
    except GeoResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/models", tags=["Models"])
def get_models():
    return {
        **_engine_descriptor(),
        "models": list_models(),
    }


@app.get("/api/models/{model_id}", tags=["Models"])
def get_model_detail(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")

    return {
        **_engine_descriptor(),
        "model": model,
    }


@app.websocket("/ws/simulate")
async def ws_simulate(
    websocket: WebSocket,
    preset: Optional[str] = Query(default=None, description="Preset ID to run"),
):
    await websocket.accept()

    active_preset = preset if preset in PRESET_META else None
    schema = None
    if active_preset:
        try:
            schema = load_from_file(PRESETS_DIR / PRESET_META[active_preset]["file"])
        except Exception:
            schema = None

    runner = SimulationRunner(schema=schema, preset_id=active_preset)

    await websocket.send_json(
        {
            "type": "connected",
            "district_name": runner.env._district_name,
            "buildings": runner.env.building_names,
            "max_steps": runner.env.max_steps,
            "preset": active_preset or "default",
            "controller_mode": runner.controller_mode,
            "model_id": runner.model_id,
            "engine_mode": runner.engine_mode,
            "engine_name": runner.engine_name,
            "engine_version": runner.engine_version,
        }
    )

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
        raw_schema = msg.get("schema", {})
        try:
            validated = load_from_dict(raw_schema)
            runner.update_schema(validated)
        except SchemaValidationError:
            pass
