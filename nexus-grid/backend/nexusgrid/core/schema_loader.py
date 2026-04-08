"""
NEXUS GRID - Schema Loader and Validator
Parses and validates a Nexus schema JSON file into a config dict that the
runtime can consume directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from nexusgrid.core.carbon_profiles import CARBON_PROFILES
from nexusgrid.core.topology import TopologyValidationError, ensure_topology


BUILDING_DEFAULTS = {
    "type": "residential",
    "battery_kwh": 10.0,
    "solar_peak_kw": 5.0,
    "battery_max_rate_kw": 3.0,
}

SCHEMA_DEFAULTS = {
    "district_name": "NEXUS District",
    "carbon_profile": "uk_national_grid",
}

TYPE_LOAD_MULTIPLIERS = {
    "residential": 1.0,
    "commercial": 1.6,
    "industrial": 2.5,
    "campus": 1.3,
    "hospital": 2.0,
    "ev": 1.0,
}

MAX_BUILDINGS = 20
MIN_BUILDINGS = 1


class SchemaValidationError(ValueError):
    """Raised when the user's schema fails validation."""


def _validate_building(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Validate and fill defaults for a single building config."""
    building = dict(BUILDING_DEFAULTS)
    building.update(raw)

    try:
        building["battery_kwh"] = float(building["battery_kwh"])
        building["solar_peak_kw"] = float(building["solar_peak_kw"])
        building["battery_max_rate_kw"] = float(building.get("battery_max_rate_kw", 3.0))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(
            f"Building [{idx}]: battery_kwh, solar_peak_kw, and battery_max_rate_kw must be numbers."
        ) from exc

    if not (0.5 <= building["battery_kwh"] <= 1000):
        raise SchemaValidationError(
            f"Building [{idx}]: battery_kwh must be between 0.5 and 1000 kWh."
        )
    if not (0.1 <= building["solar_peak_kw"] <= 500):
        raise SchemaValidationError(
            f"Building [{idx}]: solar_peak_kw must be between 0.1 and 500 kW."
        )
    if not (0.1 <= building["battery_max_rate_kw"] <= 500):
        raise SchemaValidationError(
            f"Building [{idx}]: battery_max_rate_kw must be between 0.1 and 500 kW."
        )

    if not building.get("name"):
        building["name"] = f"Building_{idx + 1}"

    building["type"] = str(building.get("type", "residential")).lower()
    building["load_multiplier"] = TYPE_LOAD_MULTIPLIERS.get(building["type"], 1.0)
    if building.get("bus_id") is not None:
        building["bus_id"] = str(building["bus_id"])
    return building


def _validate_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Top-level schema validation."""
    schema = dict(SCHEMA_DEFAULTS)
    schema.update({key: value for key, value in raw.items() if key != "buildings"})

    if schema["carbon_profile"] not in CARBON_PROFILES:
        schema["carbon_profile"] = "uk_national_grid"

    raw_buildings = raw.get("buildings")
    if not raw_buildings or not isinstance(raw_buildings, list):
        raise SchemaValidationError("Schema must contain a non-empty 'buildings' list.")

    if len(raw_buildings) < MIN_BUILDINGS:
        raise SchemaValidationError(f"At least {MIN_BUILDINGS} building is required.")
    if len(raw_buildings) > MAX_BUILDINGS:
        raise SchemaValidationError(f"Maximum {MAX_BUILDINGS} buildings allowed.")

    schema["buildings"] = [_validate_building(building, idx) for idx, building in enumerate(raw_buildings)]

    try:
        schema = ensure_topology(schema)
    except TopologyValidationError as exc:
        raise SchemaValidationError(str(exc)) from exc

    return schema


def load_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate a schema from a Python dict."""
    return _validate_schema(data)


def load_from_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Parse and validate a schema from a JSON file path."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return _validate_schema(raw)


def load_from_json_string(json_str: str) -> Dict[str, Any]:
    """Parse and validate a schema from a raw JSON string."""
    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"Invalid JSON: {exc}") from exc
    return _validate_schema(raw)
