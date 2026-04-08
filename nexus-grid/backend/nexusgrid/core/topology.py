"""Topology foundations for Phase 2A."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple


TOPOLOGY_VERSION = "0.1.0"
DEFAULT_SUBSTATION_VOLTAGE_KV = 11.0
DEFAULT_FEEDER_VOLTAGE_KV = 0.415


class TopologyValidationError(ValueError):
    """Raised when a supplied grid topology is invalid."""


def ensure_topology(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Attach a valid topology to the schema, auto-generating one when needed."""
    normalized = dict(schema)
    buildings = [dict(building) for building in schema.get("buildings", [])]
    topology = schema.get("grid_topology")

    if topology:
        validated_buildings, validated_topology = validate_topology(topology, buildings)
    else:
        validated_buildings, validated_topology = generate_default_topology(
            buildings=buildings,
            district_name=str(schema.get("district_name", "nexus-district")),
        )

    normalized["buildings"] = validated_buildings
    normalized["grid_topology"] = validated_topology
    normalized["topology_summary"] = topology_summary(validated_topology, validated_buildings)
    return normalized


def generate_default_topology(buildings: List[Dict[str, Any]], district_name: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Generate a simple radial feeder layout for the current district schema."""
    feeder_count = max(1, math.ceil(len(buildings) / 4))
    buses: List[Dict[str, Any]] = [
        {
            "id": "substation_bus",
            "role": "slack",
            "kind": "substation",
            "voltage_kv": DEFAULT_SUBSTATION_VOLTAGE_KV,
            "label": f"{district_name} Substation",
        }
    ]
    lines: List[Dict[str, Any]] = []
    feeders: List[Dict[str, Any]] = []
    updated_buildings: List[Dict[str, Any]] = []

    for feeder_idx in range(feeder_count):
        feeder_id = f"feeder_{feeder_idx + 1}"
        feeder_bus = f"{feeder_id}_bus"
        buses.append(
            {
                "id": feeder_bus,
                "role": "feeder_head",
                "kind": "distribution",
                "voltage_kv": DEFAULT_FEEDER_VOLTAGE_KV,
                "label": f"Feeder {feeder_idx + 1}",
            }
        )
        lines.append(
            {
                "id": f"line_substation_{feeder_idx + 1}",
                "from_bus": "substation_bus",
                "to_bus": feeder_bus,
                "capacity_kw": round(280 + (feeder_idx * 40), 1),
                "resistance_pu": 0.012,
                "normally_open": False,
                "feeder_id": feeder_id,
            }
        )
        feeders.append(
            {
                "id": feeder_id,
                "root_bus": feeder_bus,
                "nominal_voltage_kv": DEFAULT_FEEDER_VOLTAGE_KV,
                "bus_ids": [feeder_bus],
                "line_ids": [f"line_substation_{feeder_idx + 1}"],
            }
        )

    for idx, building in enumerate(buildings):
        feeder_idx = idx % feeder_count
        feeder_id = f"feeder_{feeder_idx + 1}"
        feeder_bus = f"{feeder_id}_bus"
        asset_bus = f"asset_bus_{idx + 1}"
        battery_kwh = _safe_float(building.get("battery_kwh"), 10.0)
        solar_peak_kw = _safe_float(building.get("solar_peak_kw"), 5.0)
        battery_rate_kw = _safe_float(building.get("battery_max_rate_kw"), 3.0)
        line_capacity = max(25.0, round((solar_peak_kw * 2.0) + (battery_rate_kw * 4.0) + (battery_kwh * 0.35), 1))

        buses.append(
            {
                "id": asset_bus,
                "role": "load_bus",
                "kind": "asset",
                "voltage_kv": DEFAULT_FEEDER_VOLTAGE_KV,
                "label": building.get("name", f"Asset {idx + 1}"),
            }
        )
        lines.append(
            {
                "id": f"line_asset_{idx + 1}",
                "from_bus": feeder_bus,
                "to_bus": asset_bus,
                "capacity_kw": line_capacity,
                "resistance_pu": 0.018,
                "normally_open": False,
                "feeder_id": feeder_id,
            }
        )

        building_with_bus = dict(building)
        building_with_bus["bus_id"] = asset_bus
        updated_buildings.append(building_with_bus)

        feeder = feeders[feeder_idx]
        feeder["bus_ids"].append(asset_bus)
        feeder["line_ids"].append(f"line_asset_{idx + 1}")

    topology = {
        "version": TOPOLOGY_VERSION,
        "topology_type": "radial_distribution",
        "slack_bus": "substation_bus",
        "buses": buses,
        "lines": lines,
        "feeders": feeders,
    }
    return updated_buildings, topology


def validate_topology(topology: Dict[str, Any], buildings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Validate a provided topology and ensure building attachments are consistent."""
    buses = topology.get("buses")
    lines = topology.get("lines")
    feeders = topology.get("feeders", [])

    if not isinstance(buses, list) or not buses:
        raise TopologyValidationError("grid_topology must include a non-empty 'buses' list.")
    if not isinstance(lines, list) or not lines:
        raise TopologyValidationError("grid_topology must include a non-empty 'lines' list.")

    bus_ids: Set[str] = set()
    normalized_buses: List[Dict[str, Any]] = []
    for idx, raw_bus in enumerate(buses):
        if not isinstance(raw_bus, dict):
            raise TopologyValidationError(f"Bus [{idx}] must be an object.")
        bus_id = str(raw_bus.get("id", "")).strip()
        if not bus_id:
            raise TopologyValidationError(f"Bus [{idx}] is missing an id.")
        if bus_id in bus_ids:
            raise TopologyValidationError(f"Duplicate bus id '{bus_id}'.")
        bus_ids.add(bus_id)
        voltage_kv = _safe_float(raw_bus.get("voltage_kv"), DEFAULT_FEEDER_VOLTAGE_KV)
        if voltage_kv <= 0:
            raise TopologyValidationError(f"Bus '{bus_id}' must have a positive voltage_kv.")
        normalized_bus = dict(raw_bus)
        normalized_bus["id"] = bus_id
        normalized_bus["voltage_kv"] = voltage_kv
        normalized_bus["role"] = str(raw_bus.get("role", "load_bus"))
        normalized_buses.append(normalized_bus)

    slack_bus = str(topology.get("slack_bus", normalized_buses[0]["id"]))
    if slack_bus not in bus_ids:
        raise TopologyValidationError(f"slack_bus '{slack_bus}' does not exist in buses.")

    line_ids: Set[str] = set()
    normalized_lines: List[Dict[str, Any]] = []
    adjacency: Dict[str, Set[str]] = defaultdict(set)
    for idx, raw_line in enumerate(lines):
        if not isinstance(raw_line, dict):
            raise TopologyValidationError(f"Line [{idx}] must be an object.")
        line_id = str(raw_line.get("id", "")).strip()
        if not line_id:
            raise TopologyValidationError(f"Line [{idx}] is missing an id.")
        if line_id in line_ids:
            raise TopologyValidationError(f"Duplicate line id '{line_id}'.")
        line_ids.add(line_id)

        from_bus = str(raw_line.get("from_bus", "")).strip()
        to_bus = str(raw_line.get("to_bus", "")).strip()
        if from_bus not in bus_ids or to_bus not in bus_ids:
            raise TopologyValidationError(
                f"Line '{line_id}' must reference existing buses for from_bus and to_bus."
            )

        capacity_kw = _safe_float(raw_line.get("capacity_kw"), 0.0)
        if capacity_kw <= 0:
            raise TopologyValidationError(f"Line '{line_id}' must have a positive capacity_kw.")

        normalized_line = dict(raw_line)
        normalized_line["id"] = line_id
        normalized_line["from_bus"] = from_bus
        normalized_line["to_bus"] = to_bus
        normalized_line["capacity_kw"] = capacity_kw
        normalized_line["resistance_pu"] = _safe_float(raw_line.get("resistance_pu"), 0.015)
        normalized_line["normally_open"] = bool(raw_line.get("normally_open", False))
        normalized_lines.append(normalized_line)

        if not normalized_line["normally_open"]:
          adjacency[from_bus].add(to_bus)
          adjacency[to_bus].add(from_bus)

    connected_buses = _connected_component(adjacency, slack_bus)
    if any(bus_id not in connected_buses for bus_id in bus_ids):
        disconnected = sorted(bus_id for bus_id in bus_ids if bus_id not in connected_buses)
        raise TopologyValidationError(
            f"Topology contains disconnected buses from slack bus '{slack_bus}': {', '.join(disconnected)}."
        )

    normalized_feeders: List[Dict[str, Any]] = []
    if feeders:
        feeder_ids: Set[str] = set()
        for idx, raw_feeder in enumerate(feeders):
            if not isinstance(raw_feeder, dict):
                raise TopologyValidationError(f"Feeder [{idx}] must be an object.")
            feeder_id = str(raw_feeder.get("id", "")).strip()
            if not feeder_id:
                raise TopologyValidationError(f"Feeder [{idx}] is missing an id.")
            if feeder_id in feeder_ids:
                raise TopologyValidationError(f"Duplicate feeder id '{feeder_id}'.")
            feeder_ids.add(feeder_id)
            root_bus = str(raw_feeder.get("root_bus", "")).strip()
            if root_bus not in bus_ids:
                raise TopologyValidationError(f"Feeder '{feeder_id}' references unknown root_bus '{root_bus}'.")

            feeder_bus_ids = [str(bus_id) for bus_id in raw_feeder.get("bus_ids", []) if str(bus_id) in bus_ids]
            feeder_line_ids = [str(line_id) for line_id in raw_feeder.get("line_ids", []) if str(line_id) in line_ids]
            normalized_feeders.append(
                {
                    "id": feeder_id,
                    "root_bus": root_bus,
                    "nominal_voltage_kv": _safe_float(raw_feeder.get("nominal_voltage_kv"), DEFAULT_FEEDER_VOLTAGE_KV),
                    "bus_ids": feeder_bus_ids,
                    "line_ids": feeder_line_ids,
                }
            )
    else:
        normalized_feeders = infer_feeders(normalized_lines, slack_bus)

    candidate_load_buses = [
        bus["id"]
        for bus in normalized_buses
        if bus["id"] != slack_bus and str(bus.get("role", "")).lower() not in {"slack", "substation"}
    ]
    if not candidate_load_buses:
        raise TopologyValidationError("Topology must provide at least one non-slack bus for asset attachment.")

    normalized_buildings: List[Dict[str, Any]] = []
    for idx, building in enumerate(buildings):
        normalized_building = dict(building)
        assigned_bus = str(building.get("bus_id", "")).strip() or candidate_load_buses[idx % len(candidate_load_buses)]
        if assigned_bus not in bus_ids:
            raise TopologyValidationError(
                f"Building '{building.get('name', idx)}' references unknown bus_id '{assigned_bus}'."
            )
        normalized_building["bus_id"] = assigned_bus
        normalized_buildings.append(normalized_building)

    normalized_topology = {
        "version": str(topology.get("version", TOPOLOGY_VERSION)),
        "topology_type": str(topology.get("topology_type", "custom_distribution")),
        "slack_bus": slack_bus,
        "buses": normalized_buses,
        "lines": normalized_lines,
        "feeders": normalized_feeders,
    }
    return normalized_buildings, normalized_topology


def infer_feeders(lines: List[Dict[str, Any]], slack_bus: str) -> List[Dict[str, Any]]:
    """Infer feeders from the first non-slack branches of the slack bus."""
    root_lines = [line for line in lines if line["from_bus"] == slack_bus or line["to_bus"] == slack_bus]
    if not root_lines:
        return [
            {
                "id": "primary_feeder",
                "root_bus": slack_bus,
                "nominal_voltage_kv": DEFAULT_FEEDER_VOLTAGE_KV,
                "bus_ids": [slack_bus],
                "line_ids": [],
            }
        ]

    feeders = []
    for idx, line in enumerate(root_lines):
        root_bus = line["to_bus"] if line["from_bus"] == slack_bus else line["from_bus"]
        feeders.append(
            {
                "id": f"inferred_feeder_{idx + 1}",
                "root_bus": root_bus,
                "nominal_voltage_kv": DEFAULT_FEEDER_VOLTAGE_KV,
                "bus_ids": [root_bus],
                "line_ids": [line["id"]],
            }
        )
    return feeders


def topology_summary(topology: Dict[str, Any], buildings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a lightweight topology summary for API/UI usage."""
    buses = topology.get("buses", [])
    lines = topology.get("lines", [])
    feeders = topology.get("feeders", [])
    slack_bus = topology.get("slack_bus")
    building_bus_ids = [building.get("bus_id") for building in buildings if building.get("bus_id")]
    max_line_capacity = max((_safe_float(line.get("capacity_kw"), 0.0) for line in lines), default=0.0)

    return {
        "version": topology.get("version", TOPOLOGY_VERSION),
        "topology_type": topology.get("topology_type", "distribution"),
        "slack_bus": slack_bus,
        "n_buses": len(buses),
        "n_lines": len(lines),
        "n_feeders": len(feeders),
        "n_assets_attached": len(building_bus_ids),
        "max_line_capacity_kw": round(max_line_capacity, 2),
        "radial": True,
    }


def _connected_component(adjacency: Dict[str, Set[str]], root: str) -> Set[str]:
    visited: Set[str] = set()
    queue = deque([root])

    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbour in adjacency.get(node, set()):
            if neighbour not in visited:
                queue.append(neighbour)

    return visited


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)
