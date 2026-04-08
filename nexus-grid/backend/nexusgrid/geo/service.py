"""Location resolution and atlas-seed schema generation for Phases 1A and 1B."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nexusgrid.core.schema_loader import MAX_BUILDINGS, load_from_dict
from nexusgrid.geo.catalog import search_catalog
from nexusgrid.geo.enrichment import geo_enrichment_service


COORDINATE_PATTERN = re.compile(
    r"^\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$"
)

DEFAULT_TIMEOUT_SECONDS = float(os.getenv("NEXUS_GEO_TIMEOUT_SECONDS", "8"))
DEFAULT_NOMINATIM_URL = os.getenv(
    "NEXUS_NOMINATIM_BASE_URL",
    "https://nominatim.openstreetmap.org/search",
)
DEFAULT_NOMINATIM_USER_AGENT = os.getenv(
    "NEXUS_NOMINATIM_USER_AGENT",
    "NEXUS-GRID/1.0 (atlas-seed geocoder)",
)
DEFAULT_NOMINATIM_EMAIL = os.getenv("NEXUS_NOMINATIM_EMAIL")


class GeoResolutionError(ValueError):
    """Raised when a location query cannot be resolved into a candidate."""


@dataclass
class LocationCandidate:
    display_name: str
    latitude: float
    longitude: float
    country: str
    country_code: str
    state: str
    city: str
    locality: str
    category: str
    type: str
    importance: float
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LocationProvider(Protocol):
    name: str

    def resolve(self, query: str, limit: int = 5) -> List[LocationCandidate]:
        ...


class CoordinateLocationProvider:
    name = "coordinates"

    def resolve(self, query: str, limit: int = 5) -> List[LocationCandidate]:
        match = COORDINATE_PATTERN.match(query)
        if not match:
            return []

        latitude = float(match.group(1))
        longitude = float(match.group(2))
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return []

        label = f"{latitude:.4f}, {longitude:.4f}"
        return [
            LocationCandidate(
                display_name=f"Coordinates {label}",
                latitude=latitude,
                longitude=longitude,
                country="Unknown",
                country_code="custom",
                state="Unknown",
                city="Unknown",
                locality="Geo Coordinate Site",
                category="coordinate",
                type="coordinate",
                importance=1.0,
                source=self.name,
            )
        ]


class CatalogLocationProvider:
    name = "catalog"

    def resolve(self, query: str, limit: int = 5) -> List[LocationCandidate]:
        matches = search_catalog(query=query, limit=limit)
        return [self._to_candidate(item) for item in matches]

    def _to_candidate(self, item: Dict[str, Any]) -> LocationCandidate:
        return LocationCandidate(
            display_name=str(item.get("display_name", "Unknown location")),
            latitude=float(item.get("latitude", 0.0)),
            longitude=float(item.get("longitude", 0.0)),
            country=str(item.get("country", "Unknown")),
            country_code=str(item.get("country_code", "custom")),
            state=str(item.get("state", "Unknown")),
            city=str(item.get("city", "Unknown")),
            locality=str(item.get("locality", item.get("city", "Unknown"))),
            category=str(item.get("category", "place")),
            type=str(item.get("type", "place")),
            importance=float(item.get("importance", 0.0)),
            source=self.name,
        )


class NominatimLocationProvider:
    name = "nominatim"

    def __init__(
        self,
        base_url: str = DEFAULT_NOMINATIM_URL,
        user_agent: str = DEFAULT_NOMINATIM_USER_AGENT,
        email: Optional[str] = DEFAULT_NOMINATIM_EMAIL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url
        self.user_agent = user_agent
        self.email = email
        self.timeout_seconds = timeout_seconds

    def resolve(self, query: str, limit: int = 5) -> List[LocationCandidate]:
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": max(1, min(limit, 10)),
        }
        if self.email:
            params["email"] = self.email

        request = Request(
            f"{self.base_url}?{urlencode(params)}",
            headers={
                "User-Agent": self.user_agent,
                "Accept-Language": "en",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise GeoResolutionError(f"Nominatim lookup failed: {exc}") from exc

        results: List[LocationCandidate] = []
        for item in payload:
            address = item.get("address", {})
            locality = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("suburb")
                or address.get("county")
                or address.get("state")
                or item.get("name")
                or "Unknown"
            )
            results.append(
                LocationCandidate(
                    display_name=str(item.get("display_name", locality)),
                    latitude=float(item.get("lat", 0.0)),
                    longitude=float(item.get("lon", 0.0)),
                    country=str(address.get("country", "Unknown")),
                    country_code=str(address.get("country_code", "custom")),
                    state=str(address.get("state", address.get("county", "Unknown"))),
                    city=str(address.get("city", address.get("town", locality))),
                    locality=str(locality),
                    category=str(item.get("category", "place")),
                    type=str(item.get("type", "place")),
                    importance=float(item.get("importance", 0.0)),
                    source=self.name,
                )
            )

        return results


class GeoTwinBuilder:
    """Generate a validated atlas-seed schema from a resolved world location."""

    generator_version = "atlas-seed-v0.1"

    def build(
        self,
        location: LocationCandidate,
        district_type: str = "auto",
        building_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        resolved_type = self._resolve_district_type(location, district_type)
        template = DISTRICT_TEMPLATES[resolved_type]
        requested_count = building_count or len(template)
        count = max(1, min(int(requested_count), MAX_BUILDINGS))

        carbon_profile, carbon_reason = self._infer_carbon_profile(location)
        solar_scale = self._infer_solar_scale(location.latitude)
        battery_scale = self._infer_battery_scale(location)

        buildings = []
        for idx in range(count):
            base = template[idx % len(template)]
            jitter = self._stable_scale(location, idx)
            buildings.append(
                {
                    "name": self._building_name(base["label"], idx),
                    "type": base["type"],
                    "battery_kwh": round(base["battery_kwh"] * battery_scale * jitter, 1),
                    "solar_peak_kw": round(base["solar_peak_kw"] * solar_scale * jitter, 1),
                    "battery_max_rate_kw": round(
                        base["battery_max_rate_kw"] * max(0.85, jitter),
                        1,
                    ),
                }
            )

        locality = location.locality if location.locality != "Unknown" else "Global"
        descriptor = DISTRICT_LABELS[resolved_type]
        schema = {
            "district_name": f"{locality} {descriptor}",
            "carbon_profile": carbon_profile,
            "description": (
                f"Auto-generated atlas seed for {location.display_name}. "
                f"Built as a {resolved_type.replace('_', ' ')} district without manual schema edits."
            ),
            "schema_version": "0.2.0",
            "source_mode": "atlas_seed",
            "geo_context": {
                "display_name": location.display_name,
                "latitude": round(location.latitude, 6),
                "longitude": round(location.longitude, 6),
                "country": location.country,
                "country_code": location.country_code,
                "state": location.state,
                "city": location.city,
                "locality": location.locality,
                "category": location.category,
                "type": location.type,
            },
            "data_sources": {
                "geocoding": location.source,
                "carbon_profile": carbon_reason,
                "weather": "heuristic-solar-scaling",
                "tariffs": "not-yet-attached",
            },
            "generation_summary": {
                "generator": self.generator_version,
                "district_type": resolved_type,
                "building_count": count,
                "solar_scale": round(solar_scale, 3),
                "battery_scale": round(battery_scale, 3),
            },
            "buildings": buildings,
        }
        return load_from_dict(schema)

    def _resolve_district_type(self, location: LocationCandidate, district_type: str) -> str:
        if district_type and district_type != "auto":
            if district_type not in DISTRICT_TEMPLATES:
                raise GeoResolutionError(
                    f"Unsupported district_type '{district_type}'. "
                    f"Use one of: {', '.join(sorted(DISTRICT_TEMPLATES))}, auto."
                )
            return district_type

        lowered = " ".join(
            [
                location.display_name.lower(),
                location.category.lower(),
                location.type.lower(),
            ]
        )
        if "university" in lowered or "campus" in lowered:
            return "campus"
        if "industrial" in lowered or "factory" in lowered or "port" in lowered:
            return "industrial"
        if location.type.lower() in {"suburb", "neighbourhood", "village", "residential"}:
            return "residential"
        return "mixed_use"

    def _infer_carbon_profile(self, location: LocationCandidate) -> Tuple[str, str]:
        country_code = location.country_code.lower()
        state = location.state.lower()

        if country_code == "gb":
            return "uk_national_grid", "mapped-from-country:gb"
        if country_code == "us":
            return "us_eastern_pjm", "closest-available-profile:us_eastern_pjm"
        if country_code == "in":
            if "tamil" in state:
                return "india_south_tneb", "mapped-from-state:tamil_nadu"
            return "india_west_maharashtra", "closest-available-profile:india_west_maharashtra"
        return "custom", "fallback:custom"

    def _infer_solar_scale(self, latitude: float) -> float:
        distance_from_equator = min(abs(latitude), 70.0)
        latitude_penalty = distance_from_equator / 120.0
        return max(0.75, round(1.25 - latitude_penalty, 3))

    def _infer_battery_scale(self, location: LocationCandidate) -> float:
        country_code = location.country_code.lower()
        if country_code == "in":
            return 1.2
        if country_code == "gb":
            return 0.95
        if country_code == "us":
            return 1.0
        return 1.05

    def _stable_scale(self, location: LocationCandidate, idx: int) -> float:
        seed = (
            f"{location.display_name}|{location.latitude:.4f}|"
            f"{location.longitude:.4f}|{idx}"
        )
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        raw = int(digest[:8], 16) / 0xFFFFFFFF
        return round(0.92 + (raw * 0.18), 3)

    def _building_name(self, label: str, idx: int) -> str:
        if idx < 26:
            suffix = chr(ord("A") + idx)
        else:
            suffix = str(idx + 1)
        return f"{label} {suffix}"


class GeoService:
    """Provider orchestration and geo-to-schema service facade."""

    def __init__(self):
        self.providers: Dict[str, LocationProvider] = {
            "coordinates": CoordinateLocationProvider(),
            "catalog": CatalogLocationProvider(),
            "nominatim": NominatimLocationProvider(),
        }
        self.builder = GeoTwinBuilder()
        self._cache: Dict[Tuple[str, str, int], Dict[str, Any]] = {}

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "auto",
                "label": "Auto",
                "kind": "composite",
                "requires_api_key": False,
                "notes": "Tries coordinates, then catalog, then Nominatim.",
            },
            {
                "id": "coordinates",
                "label": "Coordinates",
                "kind": "local",
                "requires_api_key": False,
                "notes": "Accepts lat,lon directly without external APIs.",
            },
            {
                "id": "catalog",
                "label": "Global Catalog",
                "kind": "local",
                "requires_api_key": False,
                "notes": "Offline-friendly seeded locations for demos and tests.",
            },
            {
                "id": "nominatim",
                "label": "Nominatim",
                "kind": "remote",
                "requires_api_key": False,
                "notes": "Public OSM geocoder. Respect rate limits and set a valid user agent.",
            },
        ]

    def list_enrichment_providers(self) -> Dict[str, List[Dict[str, Any]]]:
        return geo_enrichment_service.list_providers()

    def resolve(self, query: str, provider: str = "auto", limit: int = 5) -> Dict[str, Any]:
        normalized_query = query.strip()
        if not normalized_query:
            raise GeoResolutionError("Location query cannot be empty.")

        safe_limit = max(1, min(int(limit), 10))
        cache_key = (provider, normalized_query.lower(), safe_limit)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        provider_order = self._provider_order(provider)
        warnings: List[str] = []

        for provider_name in provider_order:
            try:
                candidates = self.providers[provider_name].resolve(normalized_query, safe_limit)
            except GeoResolutionError as exc:
                warnings.append(str(exc))
                continue
            if candidates:
                result = {
                    "query": normalized_query,
                    "requested_provider": provider,
                    "provider": provider_name,
                    "candidates": [candidate.to_dict() for candidate in candidates],
                    "warnings": warnings,
                }
                self._cache[cache_key] = result
                return result

        if provider == "auto":
            warnings.append(
                "No provider produced a match. Try a more specific place name or raw coordinates."
            )

        result = {
            "query": normalized_query,
            "requested_provider": provider,
            "provider": provider,
            "candidates": [],
            "warnings": warnings,
        }
        self._cache[cache_key] = result
        return result

    def generate_schema(
        self,
        query: str,
        provider: str = "auto",
        district_type: str = "auto",
        building_count: Optional[int] = None,
        include_enrichment: bool = True,
        weather_provider: str = "auto",
        carbon_provider: str = "auto",
        tariff_provider: str = "auto",
    ) -> Dict[str, Any]:
        resolution = self.resolve(query=query, provider=provider, limit=5)
        if not resolution["candidates"]:
            raise GeoResolutionError(
                f"Could not resolve '{query}'. Try a more specific query or coordinates."
            )

        location = LocationCandidate(**resolution["candidates"][0])
        schema = self.builder.build(
            location=location,
            district_type=district_type,
            building_count=building_count,
        )
        enrichment = None
        warnings = list(resolution["warnings"])

        if include_enrichment:
            enrichment = geo_enrichment_service.enrich(
                location=location.to_dict(),
                schema=schema,
                weather_provider=weather_provider,
                carbon_provider=carbon_provider,
                tariff_provider=tariff_provider,
            )
            schema = geo_enrichment_service.attach_to_schema(schema=schema, enrichment=enrichment)
            warnings.extend(enrichment["warnings"])

        return {
            "query": query,
            "provider": resolution["provider"],
            "location": location.to_dict(),
            "schema": schema,
            "enrichment": enrichment,
            "warnings": warnings,
        }

    def enrich_existing_schema(
        self,
        schema: Dict[str, Any],
        query: str,
        provider: str = "auto",
        weather_provider: str = "auto",
        carbon_provider: str = "auto",
        tariff_provider: str = "auto",
    ) -> Dict[str, Any]:
        resolution = self.resolve(query=query, provider=provider, limit=5)
        if not resolution["candidates"]:
            raise GeoResolutionError(
                f"Could not resolve '{query}'. Try a more specific query or coordinates."
            )

        location = LocationCandidate(**resolution["candidates"][0])
        enrichment = geo_enrichment_service.enrich(
            location=location.to_dict(),
            schema=schema,
            weather_provider=weather_provider,
            carbon_provider=carbon_provider,
            tariff_provider=tariff_provider,
        )
        enriched_schema = geo_enrichment_service.attach_to_schema(schema=schema, enrichment=enrichment)

        return {
            "query": query,
            "provider": resolution["provider"],
            "location": location.to_dict(),
            "schema": enriched_schema,
            "enrichment": enrichment,
            "warnings": [*resolution["warnings"], *enrichment["warnings"]],
        }

    def enrich_location(
        self,
        query: str,
        provider: str = "auto",
        weather_provider: str = "auto",
        carbon_provider: str = "auto",
        tariff_provider: str = "auto",
    ) -> Dict[str, Any]:
        resolution = self.resolve(query=query, provider=provider, limit=5)
        if not resolution["candidates"]:
            raise GeoResolutionError(
                f"Could not resolve '{query}'. Try a more specific query or coordinates."
            )

        location = LocationCandidate(**resolution["candidates"][0])
        schema = self.builder.build(location=location, district_type="auto", building_count=None)
        enrichment = geo_enrichment_service.enrich(
            location=location.to_dict(),
            schema=schema,
            weather_provider=weather_provider,
            carbon_provider=carbon_provider,
            tariff_provider=tariff_provider,
        )

        return {
            "query": query,
            "provider": resolution["provider"],
            "location": location.to_dict(),
            "enrichment": enrichment,
            "warnings": [*resolution["warnings"], *enrichment["warnings"]],
        }

    def _provider_order(self, provider: str) -> List[str]:
        if provider == "auto":
            return ["coordinates", "catalog", "nominatim"]
        if provider not in self.providers:
            raise GeoResolutionError(
                f"Unknown geo provider '{provider}'. Use one of: auto, coordinates, catalog, nominatim."
            )
        return [provider]


DISTRICT_LABELS = {
    "residential": "Adaptive Residential Grid",
    "mixed_use": "Adaptive Urban Grid",
    "industrial": "Adaptive Industrial Grid",
    "campus": "Adaptive Campus Grid",
}

DISTRICT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "residential": [
        {"label": "Home Cluster", "type": "residential", "battery_kwh": 12.0, "solar_peak_kw": 5.5, "battery_max_rate_kw": 3.0},
        {"label": "Villa Cluster", "type": "residential", "battery_kwh": 14.0, "solar_peak_kw": 6.2, "battery_max_rate_kw": 3.6},
        {"label": "Apartment Block", "type": "residential", "battery_kwh": 18.0, "solar_peak_kw": 8.0, "battery_max_rate_kw": 4.2},
        {"label": "Community Hub", "type": "commercial", "battery_kwh": 28.0, "solar_peak_kw": 12.0, "battery_max_rate_kw": 5.0},
        {"label": "EV Mobility Hub", "type": "ev", "battery_kwh": 70.0, "solar_peak_kw": 16.0, "battery_max_rate_kw": 18.0},
        {"label": "Senior Care Block", "type": "hospital", "battery_kwh": 26.0, "solar_peak_kw": 10.0, "battery_max_rate_kw": 5.0},
    ],
    "mixed_use": [
        {"label": "Residential Tower", "type": "residential", "battery_kwh": 18.0, "solar_peak_kw": 8.0, "battery_max_rate_kw": 4.0},
        {"label": "Retail Podium", "type": "commercial", "battery_kwh": 32.0, "solar_peak_kw": 14.0, "battery_max_rate_kw": 6.0},
        {"label": "Office Spine", "type": "commercial", "battery_kwh": 36.0, "solar_peak_kw": 15.0, "battery_max_rate_kw": 6.5},
        {"label": "Civic Services", "type": "hospital", "battery_kwh": 30.0, "solar_peak_kw": 11.0, "battery_max_rate_kw": 5.5},
        {"label": "Transit EV Hub", "type": "ev", "battery_kwh": 90.0, "solar_peak_kw": 18.0, "battery_max_rate_kw": 22.0},
        {"label": "Education Block", "type": "campus", "battery_kwh": 28.0, "solar_peak_kw": 12.0, "battery_max_rate_kw": 5.0},
        {"label": "Cold Chain Node", "type": "industrial", "battery_kwh": 45.0, "solar_peak_kw": 20.0, "battery_max_rate_kw": 8.0},
        {"label": "Neighborhood Hub", "type": "commercial", "battery_kwh": 24.0, "solar_peak_kw": 9.0, "battery_max_rate_kw": 4.5},
    ],
    "industrial": [
        {"label": "Factory Line", "type": "industrial", "battery_kwh": 90.0, "solar_peak_kw": 32.0, "battery_max_rate_kw": 18.0},
        {"label": "Assembly Hall", "type": "industrial", "battery_kwh": 78.0, "solar_peak_kw": 28.0, "battery_max_rate_kw": 16.0},
        {"label": "Warehouse Block", "type": "industrial", "battery_kwh": 62.0, "solar_peak_kw": 24.0, "battery_max_rate_kw": 12.0},
        {"label": "Admin Core", "type": "commercial", "battery_kwh": 28.0, "solar_peak_kw": 10.0, "battery_max_rate_kw": 5.0},
        {"label": "Logistics EV Yard", "type": "ev", "battery_kwh": 120.0, "solar_peak_kw": 24.0, "battery_max_rate_kw": 26.0},
        {"label": "Utility Support", "type": "commercial", "battery_kwh": 34.0, "solar_peak_kw": 12.0, "battery_max_rate_kw": 6.0},
    ],
    "campus": [
        {"label": "Lecture Hall", "type": "campus", "battery_kwh": 30.0, "solar_peak_kw": 12.0, "battery_max_rate_kw": 5.5},
        {"label": "Research Lab", "type": "campus", "battery_kwh": 34.0, "solar_peak_kw": 14.0, "battery_max_rate_kw": 6.0},
        {"label": "Dormitory", "type": "residential", "battery_kwh": 22.0, "solar_peak_kw": 9.0, "battery_max_rate_kw": 4.5},
        {"label": "Library", "type": "commercial", "battery_kwh": 24.0, "solar_peak_kw": 9.5, "battery_max_rate_kw": 4.5},
        {"label": "Admin Block", "type": "commercial", "battery_kwh": 20.0, "solar_peak_kw": 8.0, "battery_max_rate_kw": 4.0},
        {"label": "Campus EV Court", "type": "ev", "battery_kwh": 85.0, "solar_peak_kw": 18.0, "battery_max_rate_kw": 20.0},
    ],
}


geo_service = GeoService()
