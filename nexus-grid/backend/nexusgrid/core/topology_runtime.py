"""Runtime topology stress evaluation for Phase 2C."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional


STATUS_PRIORITY = {
    "nominal": 0,
    "warning": 1,
    "critical": 2,
    "overload": 3,
    "outage": 4,
}


def prepare_topology_runtime(schema: Dict[str, Any]) -> Dict[str, Any]:
    topology = dict(schema.get("grid_topology", {}))
    lines = [dict(line) for line in topology.get("lines", [])]
    feeders = [dict(feeder) for feeder in topology.get("feeders", [])]
    slack_bus = str(topology.get("slack_bus", "substation_bus"))
    buildings = [dict(building) for building in schema.get("buildings", [])]

    line_by_id = {str(line.get("id")): line for line in lines}
    bus_to_feeder: Dict[str, str] = {}
    for feeder in feeders:
        feeder_id = str(feeder.get("id", "primary_feeder"))
        for bus_id in feeder.get("bus_ids", []):
            bus_to_feeder[str(bus_id)] = feeder_id

    building_to_bus: Dict[str, str] = {}
    building_to_feeder: Dict[str, str] = {}
    feeder_buildings: Dict[str, List[str]] = defaultdict(list)
    asset_line_by_building: Dict[str, str] = {}
    head_line_by_feeder: Dict[str, str] = {}

    for line in lines:
        line_id = str(line.get("id"))
        feeder_id = str(line.get("feeder_id") or bus_to_feeder.get(str(line.get("to_bus")), "unassigned_feeder"))
        line["feeder_id"] = feeder_id
        from_bus = str(line.get("from_bus"))
        to_bus = str(line.get("to_bus"))
        if from_bus == slack_bus or to_bus == slack_bus:
            head_line_by_feeder.setdefault(feeder_id, line_id)

    for building in buildings:
        building_id = str(building.get("name", "asset"))
        bus_id = str(building.get("bus_id", ""))
        feeder_id = bus_to_feeder.get(bus_id, "unassigned_feeder")
        building_to_bus[building_id] = bus_id
        building_to_feeder[building_id] = feeder_id
        feeder_buildings[feeder_id].append(building_id)

    for line in lines:
        line_id = str(line.get("id"))
        from_bus = str(line.get("from_bus"))
        to_bus = str(line.get("to_bus"))
        for building_id, bus_id in building_to_bus.items():
            if bus_id in {from_bus, to_bus}:
                asset_line_by_building[building_id] = line_id

    return {
        "slack_bus": slack_bus,
        "lines": lines,
        "feeders": feeders,
        "line_by_id": line_by_id,
        "building_to_bus": building_to_bus,
        "building_to_feeder": building_to_feeder,
        "feeder_buildings": dict(feeder_buildings),
        "asset_line_by_building": asset_line_by_building,
        "head_line_by_feeder": head_line_by_feeder,
    }


def evaluate_topology_runtime(
    runtime_context: Dict[str, Any],
    buildings_data: List[Dict[str, Any]],
    feeder_capacity_multipliers: Optional[Dict[str, float]] = None,
    line_capacity_multipliers: Optional[Dict[str, float]] = None,
    outaged_feeders: Optional[set[str]] = None,
    outaged_lines: Optional[set[str]] = None,
    active_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    feeder_capacity_multipliers = feeder_capacity_multipliers or {}
    line_capacity_multipliers = line_capacity_multipliers or {}
    outaged_feeders = outaged_feeders or set()
    outaged_lines = outaged_lines or set()
    active_events = active_events or []

    lines = runtime_context.get("lines", [])
    feeders = runtime_context.get("feeders", [])
    building_to_feeder = runtime_context.get("building_to_feeder", {})
    feeder_buildings = runtime_context.get("feeder_buildings", {})
    asset_line_by_building = runtime_context.get("asset_line_by_building", {})
    head_line_by_feeder = runtime_context.get("head_line_by_feeder", {})

    building_net = {
        str(item.get("id", "")): float(item.get("net_electricity_consumption", 0.0))
        for item in buildings_data
    }

    feeder_net_loads: Dict[str, float] = {}
    feeder_absolute_loads: Dict[str, float] = {}
    for feeder in feeders:
        feeder_id = str(feeder.get("id", "primary_feeder"))
        members = feeder_buildings.get(feeder_id, [])
        net_load = sum(building_net.get(building_id, 0.0) for building_id in members)
        feeder_net_loads[feeder_id] = round(net_load, 4)
        feeder_absolute_loads[feeder_id] = round(abs(net_load), 4)

    line_states: List[Dict[str, Any]] = []
    per_feeder_lines: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for line in lines:
        line_id = str(line.get("id", "line"))
        feeder_id = str(line.get("feeder_id", "primary_feeder"))
        base_capacity = float(line.get("capacity_kw", 0.0))
        feeder_multiplier = float(feeder_capacity_multipliers.get(feeder_id, 1.0))
        line_multiplier = float(line_capacity_multipliers.get(line_id, 1.0))
        effective_capacity = round(base_capacity * feeder_multiplier * line_multiplier, 3)
        is_outaged = feeder_id in outaged_feeders or line_id in outaged_lines or effective_capacity <= 0
        flow_kw = _resolve_line_flow(
            line=line,
            feeder_id=feeder_id,
            building_net=building_net,
            feeder_absolute_loads=feeder_absolute_loads,
            asset_line_by_building=asset_line_by_building,
            outaged_feeders=outaged_feeders,
        )
        loading_pct = (
            round(abs(flow_kw) / max(effective_capacity, 0.001), 3)
            if effective_capacity > 0 and not is_outaged
            else 0.0
        )
        state = {
            "line_id": line_id,
            "feeder_id": feeder_id,
            "from_bus": str(line.get("from_bus", "")),
            "to_bus": str(line.get("to_bus", "")),
            "capacity_kw": round(base_capacity, 3),
            "available_capacity_kw": round(max(effective_capacity, 0.0), 3),
            "flow_kw": round(flow_kw, 3),
            "loading_pct": loading_pct,
            "status": _loading_status(loading_pct, is_outaged),
            "is_outaged": is_outaged,
            "is_feeder_head": head_line_by_feeder.get(feeder_id) == line_id,
        }
        line_states.append(state)
        per_feeder_lines[feeder_id].append(state)

    feeder_states: List[Dict[str, Any]] = []
    for feeder in feeders:
        feeder_id = str(feeder.get("id", "primary_feeder"))
        line_group = per_feeder_lines.get(feeder_id, [])
        head_line = next((line for line in line_group if line["is_feeder_head"]), None)
        loading_pct = (
            head_line["loading_pct"]
            if head_line
            else max((line["loading_pct"] for line in line_group), default=0.0)
        )
        status = _worst_status([line["status"] for line in line_group] or ["nominal"])
        headroom_kw = (
            round(max(head_line["available_capacity_kw"] - abs(head_line["flow_kw"]), 0.0), 3)
            if head_line
            else None
        )
        feeder_states.append(
            {
                "feeder_id": feeder_id,
                "label": str(feeder.get("id", feeder_id)).replace("_", " ").title(),
                "n_assets": len(feeder_buildings.get(feeder_id, [])),
                "net_load_kw": feeder_net_loads.get(feeder_id, 0.0),
                "loading_kw": feeder_absolute_loads.get(feeder_id, 0.0),
                "loading_pct": round(loading_pct, 3),
                "headroom_kw": headroom_kw,
                "capacity_kw": head_line["available_capacity_kw"] if head_line else None,
                "status": status,
                "line_count": len(line_group),
                "constrained_lines": len(
                    [line for line in line_group if line["status"] in {"warning", "critical", "overload", "outage"}]
                ),
                "is_outaged": status == "outage",
            }
        )

    constrained_feeders = [feeder for feeder in feeder_states if feeder["status"] != "nominal"]
    overloaded_lines = [line for line in line_states if line["status"] in {"overload", "outage"}]
    max_loading_pct = max((line["loading_pct"] for line in line_states), default=0.0)
    event_weight = 0.18 if active_events else 0.0
    system_stress_index = round(
        min(
            1.0,
            (max_loading_pct * 0.6)
            + ((len(constrained_feeders) / max(len(feeder_states), 1)) * 0.25)
            + ((len(overloaded_lines) / max(len(line_states), 1)) * 0.15)
            + event_weight,
        ),
        3,
    )

    return {
        "system_stress_index": system_stress_index,
        "constrained_feeders": len(constrained_feeders),
        "overloaded_lines": len(overloaded_lines),
        "feeder_states": sorted(feeder_states, key=lambda item: STATUS_PRIORITY.get(item["status"], 0), reverse=True),
        "line_states": sorted(line_states, key=lambda item: STATUS_PRIORITY.get(item["status"], 0), reverse=True),
        "active_events": active_events,
    }


def _resolve_line_flow(
    line: Dict[str, Any],
    feeder_id: str,
    building_net: Dict[str, float],
    feeder_absolute_loads: Dict[str, float],
    asset_line_by_building: Dict[str, str],
    outaged_feeders: set[str],
) -> float:
    if feeder_id in outaged_feeders:
        return 0.0

    line_id = str(line.get("id", "line"))
    if str(line.get("from_bus", "")) == "substation_bus" or str(line.get("to_bus", "")) == "substation_bus":
        return feeder_absolute_loads.get(feeder_id, 0.0)

    for building_id, asset_line_id in asset_line_by_building.items():
        if asset_line_id == line_id:
            return abs(building_net.get(building_id, 0.0))

    return feeder_absolute_loads.get(feeder_id, 0.0)


def _loading_status(loading_pct: float, is_outaged: bool) -> str:
    if is_outaged:
        return "outage"
    if loading_pct >= 1.0:
        return "overload"
    if loading_pct >= 0.9:
        return "critical"
    if loading_pct >= 0.72:
        return "warning"
    return "nominal"


def _worst_status(statuses: List[str]) -> str:
    return max(statuses, key=lambda item: STATUS_PRIORITY.get(item, 0), default="nominal")
