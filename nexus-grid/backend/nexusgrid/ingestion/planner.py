"""Architecture contract for future radius-based asset ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class AssetProviderDescriptor:
    id: str
    label: str
    role: str
    status: str
    priority: int
    requires_api_key: bool
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AssetIngestionPlanner:
    """Plans how a future 50 km asset-ingestion slice should plug into the twin pipeline."""

    default_radius_km = 50

    def __init__(self) -> None:
        self.providers: List[AssetProviderDescriptor] = [
            AssetProviderDescriptor(
                id="overture",
                label="Overture Maps",
                role="regional asset and land-use enrichment",
                status="planned_primary",
                priority=1,
                requires_api_key=False,
                notes="Best open candidate for scalable base geography and built-world enrichment.",
            ),
            AssetProviderDescriptor(
                id="utility_open_data",
                label="Utility / Government GIS",
                role="high-confidence substations, feeders, and service territories",
                status="planned_opportunistic",
                priority=2,
                requires_api_key=False,
                notes="Use whenever city- or country-specific open power datasets exist.",
            ),
            AssetProviderDescriptor(
                id="osm_overpass",
                label="OSM / Overpass",
                role="fallback map objects for substations, lines, chargers, and POIs",
                status="planned_fallback",
                priority=3,
                requires_api_key=False,
                notes="Useful for prototyping and patch coverage, but not dependable as the backbone.",
            ),
            AssetProviderDescriptor(
                id="manual_upload",
                label="Operator Upload",
                role="manual override for utility shapefiles or asset CSVs",
                status="planned_override",
                priority=4,
                requires_api_key=False,
                notes="Ensures we can ingest real utility data without redesigning the twin stack.",
            ),
        ]

    def list_providers(self) -> List[Dict[str, Any]]:
        return [provider.to_dict() for provider in self.providers]

    def build_plan(
        self,
        *,
        query: str,
        latitude: float,
        longitude: float,
        country_code: str,
        district_type: str,
        radius_km: int | None = None,
    ) -> Dict[str, Any]:
        actual_radius = max(5, min(radius_km or self.default_radius_km, 150))
        normalized_country_code = (country_code or "unknown").lower()

        return {
            "phase": "asset_radius_architecture",
            "status": "planned",
            "query": query,
            "radius_km": actual_radius,
            "center": {
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
            },
            "country_code": normalized_country_code,
            "district_type": district_type,
            "provider_stack": self._provider_stack_for_country(normalized_country_code),
            "normalized_layers": [
                "substations",
                "feeders",
                "lines",
                "generation_assets",
                "storage_assets",
                "ev_charging_assets",
                "demand_clusters",
                "critical_loads",
            ],
            "control_principle": {
                "visible_assets_are_not_all_agents": True,
                "twin_population_scope": "all important assets inside the selected radius",
                "agent_scope": [
                    "feeder_coordinator",
                    "storage_fleet_dispatch",
                    "ev_fleet_dispatch",
                    "industrial_cluster_dispatch",
                    "campus_or_microgrid_dispatch",
                ],
                "cto_rationale": (
                    "Every important asset should exist in the twin, but RL agents should map to real control authorities, "
                    "not every physical marker."
                ),
            },
            "runtime_contract": {
                "ingestion_output": "normalized_asset_graph",
                "twin_builder_input": "normalized_asset_graph + live_signal_spine",
                "controller_input": "aggregated controllable clusters + feeder constraints + market signals",
                "ui_input": "all visible assets + aggregated control entities + provenance",
            },
            "phase_gates": [
                "Phase 2/3: keep generated topology and clustered agents",
                "Phase 4: ingest 50 km radius assets into normalized graph",
                "Phase 4: map raw assets to visual layers and clustered control entities",
                "Phase 5: extend RL observations/actions to topology-aware aggregated entities",
            ],
            "success_metrics": [
                "city selection can expand into a 50 km asset graph without schema rewrites",
                "new data providers plug into the normalized graph adapter instead of the simulator core",
                "raw assets appear on the map even when they are not RL agents",
            ],
        }

    def _provider_stack_for_country(self, country_code: str) -> List[Dict[str, Any]]:
        providers = sorted(self.providers, key=lambda provider: provider.priority)
        stack = [provider.to_dict() for provider in providers]
        if country_code in {"us", "gb", "de", "fr", "sg", "in"}:
            stack.insert(
                1,
                {
                    "id": "country_open_power_data",
                    "label": "Country-Specific Open Power Data",
                    "role": "power-network uplift where public infrastructure datasets exist",
                    "status": "planned_opportunistic",
                    "priority": 2,
                    "requires_api_key": False,
                    "notes": "Prefer this when national or city GIS power datasets are discoverable.",
                },
            )
        return stack


asset_ingestion_planner = AssetIngestionPlanner()
