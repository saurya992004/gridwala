"""
NEXUS GRID — Schema Loader & Validator
Parses and validates a Nexus Schema JSON file into a config dict
that the NexusGridEnv can consume directly.

Schema format (nexus-schema.json):
{
  "district_name": "Green Valley Housing Society",
  "carbon_profile": "india_west_maharashtra",
  "buildings": [
    {
      "name": "Block A",
      "type": "residential",
      "battery_kwh": 15.0,
      "solar_peak_kw": 8.0
    },
    ...
  ]
}

All fields have defaults — only "buildings" is required.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from nexusgrid.core.carbon_profiles import CARBON_PROFILES

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
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

# Building type → occupancy load multiplier
TYPE_LOAD_MULTIPLIERS = {
    "residential":  1.0,
    "commercial":   1.6,
    "industrial":   2.5,
    "campus":       1.3,
    "hospital":     2.0,
}

MAX_BUILDINGS = 20
MIN_BUILDINGS = 1


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

class SchemaValidationError(ValueError):
    """Raised when the user's schema fails validation."""
    pass


def _validate_building(raw: Dict, idx: int) -> Dict[str, Any]:
    """Validate and fill defaults for a single building config."""
    b = dict(BUILDING_DEFAULTS)
    b.update(raw)

    # Coerce numeric types
    try:
        b["battery_kwh"] = float(b["battery_kwh"])
        b["solar_peak_kw"] = float(b["solar_peak_kw"])
        b["battery_max_rate_kw"] = float(b.get("battery_max_rate_kw", 3.0))
    except (TypeError, ValueError):
        raise SchemaValidationError(
            f"Building [{idx}]: battery_kwh and solar_peak_kw must be numbers."
        )

    # Range checks
    if not (0.5 <= b["battery_kwh"] <= 1000):
        raise SchemaValidationError(
            f"Building [{idx}]: battery_kwh must be between 0.5 and 1000 kWh."
        )
    if not (0.1 <= b["solar_peak_kw"] <= 500):
        raise SchemaValidationError(
            f"Building [{idx}]: solar_peak_kw must be between 0.1 and 500 kW."
        )

    # Default name
    if not b.get("name"):
        b["name"] = f"Building_{idx + 1}"

    # Normalise type
    b["type"] = str(b.get("type", "residential")).lower()
    b["load_multiplier"] = TYPE_LOAD_MULTIPLIERS.get(b["type"], 1.0)

    return b


def _validate_schema(raw: Dict) -> Dict[str, Any]:
    """Top-level schema validation."""
    schema = dict(SCHEMA_DEFAULTS)
    schema.update({k: v for k, v in raw.items() if k != "buildings"})

    # Validate carbon profile
    if schema["carbon_profile"] not in CARBON_PROFILES:
        schema["carbon_profile"] = "uk_national_grid"  # safe fallback

    # Validate buildings array
    raw_buildings = raw.get("buildings")
    if not raw_buildings or not isinstance(raw_buildings, list):
        raise SchemaValidationError("Schema must contain a non-empty 'buildings' list.")

    if len(raw_buildings) < MIN_BUILDINGS:
        raise SchemaValidationError(f"At least {MIN_BUILDINGS} building is required.")
    if len(raw_buildings) > MAX_BUILDINGS:
        raise SchemaValidationError(f"Maximum {MAX_BUILDINGS} buildings allowed.")

    schema["buildings"] = [_validate_building(b, i) for i, b in enumerate(raw_buildings)]
    return schema


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_from_dict(data: Dict) -> Dict[str, Any]:
    """
    Parse and validate a schema from a Python dict (e.g., from JSON POST body).
    Returns a validated config dict.
    """
    return _validate_schema(data)


def load_from_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse and validate a schema from a JSON file path.
    Returns a validated config dict.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return _validate_schema(raw)


def load_from_json_string(json_str: str) -> Dict[str, Any]:
    """Parse and validate a schema from a raw JSON string."""
    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"Invalid JSON: {e}")
    return _validate_schema(raw)
