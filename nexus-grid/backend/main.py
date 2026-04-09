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
from nexusgrid.geo.enrichment import GeoEnrichmentError
from nexusgrid.geo.service import DISTRICT_LABELS, GeoResolutionError, geo_service
from nexusgrid.core.simulation_runner import SimulationRunner


app = FastAPI(
    title="NEXUS GRID API",
    description="AI-powered plug-and-play smart grid orchestration platform",
    version="2.4.0",
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
        "geo_seed": "London",
        "topology_type": "radial_distribution",
    },
    "university_campus": {
        "label": "University Campus",
        "description": "Mixed campus microgrid: lecture halls, dorms, library, admin building",
        "file": "university_campus.json",
        "geo_seed": "Boston",
        "topology_type": "radial_distribution",
    },
    "industrial_microgrid": {
        "label": "Industrial Microgrid (India)",
        "description": "Factory, warehouses, and EV charging hub on Maharashtra grid",
        "file": "industrial_microgrid.json",
        "geo_seed": "Mumbai",
        "topology_type": "radial_distribution",
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
        "version": "2.4.0",
        **_engine_descriptor(),
    }


@app.get("/status", tags=["Health"])
def status():
    return {
        "status": "ok",
        "service": "nexus-grid-backend",
        "version": "2.4.0",
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
        return {
            "preset_id": preset_id,
            "schema": schema,
            "topology_summary": schema.get("topology_summary"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _load_runtime_preset_schema(preset_id: str) -> Optional[Dict]:
    if preset_id not in PRESET_META:
        return None

    try:
        schema = load_from_file(PRESETS_DIR / PRESET_META[preset_id]["file"])
    except Exception:
        return None

    geo_seed = PRESET_META[preset_id].get("geo_seed")
    if not geo_seed:
        return schema

    try:
        enriched = geo_service.enrich_existing_schema(
            schema=schema,
            query=str(geo_seed),
            provider="catalog",
            weather_provider="auto",
            carbon_provider="auto",
            tariff_provider="auto",
        )
        return enriched["schema"]
    except (GeoResolutionError, GeoEnrichmentError):
        return schema


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
    include_enrichment: bool = True
    weather_provider: str = "auto"
    carbon_provider: str = "auto"
    tariff_provider: str = "auto"


class GeoEnrichmentPayload(BaseModel):
    query: str
    provider: str = "auto"
    weather_provider: str = "auto"
    carbon_provider: str = "auto"
    tariff_provider: str = "auto"


@app.post("/api/validate", tags=["Schema"])
def validate_schema(payload: SchemaPayload):
    try:
        validated = load_from_dict(payload.schema_data)
        return {
            "valid": True,
            "schema": validated,
            "building_count": len(validated["buildings"]),
            "topology_summary": validated.get("topology_summary"),
        }
    except SchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/topology/summary", tags=["Topology"])
def get_topology_summary(payload: SchemaPayload):
    try:
        validated = load_from_dict(payload.schema_data)
        return {
            **_engine_descriptor(),
            "topology_summary": validated.get("topology_summary"),
            "grid_topology": validated.get("grid_topology"),
        }
    except SchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/geo/providers", tags=["Geo"])
def get_geo_providers():
    return {
        **_engine_descriptor(),
        "providers": geo_service.list_providers(),
        "featured_locations": geo_service.list_featured_locations(),
        "enrichment_providers": geo_service.list_enrichment_providers(),
        "district_types": ["auto", *DISTRICT_LABELS.keys()],
        "phase": "2B",
        "recommended_live_apis": [
            "Electricity Maps for live carbon intensity",
            "Open-Meteo or NASA POWER for weather and solar context",
            "OpenEI or utility-specific tariff feeds for price signals",
        ],
    }


@app.get("/api/geo/featured", tags=["Geo"])
def get_featured_geo_locations(limit: int = Query(default=8, ge=1, le=12)):
    return {
        **_engine_descriptor(),
        "phase": "2B",
        "featured_locations": geo_service.list_featured_locations(limit=limit),
    }


@app.post("/api/geo/resolve", tags=["Geo"])
def resolve_geo_location(payload: GeoResolvePayload):
    try:
        result = geo_service.resolve(
            query=payload.query,
            provider=payload.provider,
            limit=payload.limit,
        )
        result["phase"] = "2B"
        return result
    except (GeoResolutionError, GeoEnrichmentError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/geo/enrich", tags=["Geo"])
def enrich_geo_location(payload: GeoEnrichmentPayload):
    try:
        result = geo_service.enrich_location(
            query=payload.query,
            provider=payload.provider,
            weather_provider=payload.weather_provider,
            carbon_provider=payload.carbon_provider,
            tariff_provider=payload.tariff_provider,
        )
        result["phase"] = "2B"
        return result
    except (GeoResolutionError, GeoEnrichmentError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/geo/schema", tags=["Geo"])
def generate_geo_schema(payload: GeoSchemaPayload):
    try:
        result = geo_service.generate_schema(
            query=payload.query,
            provider=payload.provider,
            district_type=payload.district_type,
            building_count=payload.building_count,
            include_enrichment=payload.include_enrichment,
            weather_provider=payload.weather_provider,
            carbon_provider=payload.carbon_provider,
            tariff_provider=payload.tariff_provider,
        )
        result["phase"] = "2B"
        result["building_count"] = len(result["schema"]["buildings"])
        return result
    except (GeoResolutionError, GeoEnrichmentError) as exc:
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
        schema = _load_runtime_preset_schema(active_preset)

    runner = SimulationRunner(schema=schema, preset_id=active_preset)
    grid_signal_spine = runner.env.grid_signal_spine

    await websocket.send_json(
        {
            "type": "connected",
            "district_name": runner.env._district_name,
            "buildings": runner.env.seed_buildings,
            "max_steps": runner.env.max_steps,
            "preset": active_preset or "default",
            "controller_mode": runner.controller_mode,
            "model_id": runner.model_id,
            "engine_mode": runner.engine_mode,
            "engine_name": runner.engine_name,
            "engine_version": runner.engine_version,
            "operating_context_mode": runner.operating_context_mode,
            "operating_context_live": runner.operating_context_live,
            "electricity_maps_zone": grid_signal_spine.get("zone"),
            "electricity_maps_provider_mode": grid_signal_spine.get("provider_mode"),
            "grid_signal_estimated": grid_signal_spine.get("is_estimated"),
            "grid_renewable_share_pct": grid_signal_spine.get("renewable_share_pct"),
            "grid_total_load_mw": grid_signal_spine.get("total_load_mw"),
            "grid_import_mw": grid_signal_spine.get("total_import_mw"),
            "grid_export_mw": grid_signal_spine.get("total_export_mw"),
            "grid_net_interchange_mw": grid_signal_spine.get("net_interchange_mw"),
            "grid_interchange_state": grid_signal_spine.get("interchange_state"),
            "grid_wholesale_price": grid_signal_spine.get("day_ahead_price"),
            "grid_wholesale_price_unit": grid_signal_spine.get("day_ahead_price_unit"),
            "topology_summary": runner.topology_summary,
            "geo_context": runner.env.geo_context,
            "twin_summary": runner.env.twin_summary,
            "atlas_context": runner.env.atlas_context,
            "control_entities": runner.env.control_entities,
            "twin_provenance": runner.env.twin_provenance,
            "data_sources": runner.env.data_sources,
            "enrichment_warnings": runner.env.enrichment_warnings,
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
