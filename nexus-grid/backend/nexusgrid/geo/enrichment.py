"""Weather, carbon, and tariff enrichment for geo-generated schemas."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nexusgrid.core.carbon_profiles import get_profile


DEFAULT_TIMEOUT_SECONDS = float(os.getenv("NEXUS_GEO_TIMEOUT_SECONDS", "4"))
OPEN_METEO_BASE_URL = os.getenv(
    "NEXUS_OPEN_METEO_BASE_URL",
    "https://api.open-meteo.com/v1/forecast",
)
ELECTRICITY_MAPS_BASE_URL = os.getenv(
    "NEXUS_ELECTRICITY_MAPS_BASE_URL",
    "https://api.electricitymaps.com/v3/carbon-intensity/latest",
)
OPENEI_BASE_URL = os.getenv(
    "NEXUS_OPENEI_BASE_URL",
    "https://api.openei.org/utility_rates",
)


class GeoEnrichmentError(ValueError):
    """Raised when a live enrichment provider cannot satisfy a request."""


def _http_get_json(
    url: str,
    params: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    request = Request(
        f"{url}?{urlencode(params, doseq=True)}",
        headers=headers or {"User-Agent": "NEXUS-GRID/1.0 (geo enrichment)"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise GeoEnrichmentError(str(exc)) from exc


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _numeric_mean(values: List[Any]) -> float:
    series = [float(value) for value in values if isinstance(value, (int, float))]
    return mean(series) if series else 0.0


def _band_from_ratio(value: float, baseline: float) -> str:
    baseline = baseline or 1.0
    ratio = value / baseline
    if ratio <= 0.85:
        return "low"
    if ratio >= 1.15:
        return "high"
    return "moderate"


def _country_tariff_defaults(country_code: str) -> Tuple[str, float, float, float]:
    code = country_code.lower()
    if code == "us":
        return "USD", 0.11, 0.18, 0.27
    if code == "gb":
        return "GBP", 0.16, 0.24, 0.33
    if code == "in":
        return "INR", 5.5, 8.0, 11.5
    if code == "sg":
        return "SGD", 0.19, 0.25, 0.31
    if code == "br":
        return "BRL", 0.55, 0.78, 1.05
    return "USD", 0.10, 0.16, 0.23


class HeuristicWeatherProvider:
    name = "heuristic"

    def enrich(self, location: Dict[str, Any]) -> Dict[str, Any]:
        now = _utc_now()
        latitude = float(location.get("latitude", 0.0))
        seasonal_wave = math.cos(2 * math.pi * (now.timetuple().tm_yday - 172) / 365)
        latitude_factor = max(0.55, 1.2 - (min(abs(latitude), 70.0) / 100.0))
        solar_capacity_factor = round(
            max(0.45, min(1.2, 0.85 + (0.18 * seasonal_wave) + (0.22 * latitude_factor))),
            3,
        )
        temperature_c = round(26.0 - (abs(latitude) * 0.18) + (4.0 * seasonal_wave), 1)
        cloud_cover_pct = int(max(10, min(85, 55 - (seasonal_wave * 20))))
        wind_speed_kmh = round(10.0 + (abs(latitude) * 0.12), 1)
        solar_avg = round(280 * solar_capacity_factor, 1)
        solar_peak = round(min(950.0, solar_avg * 2.2), 1)

        return {
            "provider": self.name,
            "live": False,
            "source_detail": "heuristic-latitude-seasonality",
            "timezone": "UTC",
            "current": {
                "temperature_c": temperature_c,
                "cloud_cover_pct": cloud_cover_pct,
                "wind_speed_kmh": wind_speed_kmh,
            },
            "forecast": {
                "next_24h_avg_shortwave_radiation_wm2": solar_avg,
                "next_24h_peak_shortwave_radiation_wm2": solar_peak,
                "next_24h_avg_temperature_c": temperature_c,
                "solar_capacity_factor": solar_capacity_factor,
                "outlook": _solar_outlook(solar_capacity_factor),
            },
            "warnings": [],
        }


class OpenMeteoWeatherProvider:
    name = "open_meteo"

    def enrich(self, location: Dict[str, Any]) -> Dict[str, Any]:
        payload = _http_get_json(
            OPEN_METEO_BASE_URL,
            params={
                "latitude": round(float(location["latitude"]), 6),
                "longitude": round(float(location["longitude"]), 6),
                "current": "temperature_2m,cloud_cover,wind_speed_10m,shortwave_radiation",
                "hourly": "temperature_2m,cloud_cover,wind_speed_10m,shortwave_radiation",
                "forecast_hours": 24,
                "timezone": "auto",
            },
        )

        current = payload.get("current", {})
        hourly = payload.get("hourly", {})
        hourly_radiation = hourly.get("shortwave_radiation", [])
        hourly_temp = hourly.get("temperature_2m", [])

        avg_radiation = round(_numeric_mean(hourly_radiation), 1)
        peak_radiation = round(
            max((float(value) for value in hourly_radiation if isinstance(value, (int, float))), default=0.0),
            1,
        )
        avg_temperature = round(_numeric_mean(hourly_temp), 1)
        solar_capacity_factor = round(
            max(0.35, min(1.25, 0.35 + (avg_radiation / 650.0))),
            3,
        )

        return {
            "provider": self.name,
            "live": True,
            "source_detail": "open-meteo-forecast",
            "timezone": payload.get("timezone", "auto"),
            "current": {
                "temperature_c": round(float(current.get("temperature_2m", avg_temperature or 0.0)), 1),
                "cloud_cover_pct": int(round(float(current.get("cloud_cover", 0.0)))),
                "wind_speed_kmh": round(float(current.get("wind_speed_10m", 0.0)), 1),
                "shortwave_radiation_wm2": round(float(current.get("shortwave_radiation", 0.0)), 1),
            },
            "forecast": {
                "next_24h_avg_shortwave_radiation_wm2": avg_radiation,
                "next_24h_peak_shortwave_radiation_wm2": peak_radiation,
                "next_24h_avg_temperature_c": avg_temperature,
                "solar_capacity_factor": solar_capacity_factor,
                "outlook": _solar_outlook(solar_capacity_factor),
            },
            "warnings": [],
        }


class ProfileCarbonProvider:
    name = "profile"

    def enrich(self, location: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        profile_name = str(schema.get("carbon_profile", "custom"))
        profile = get_profile(profile_name)
        hour = _utc_now().hour
        current = round(float(profile[hour]), 3)
        average = round(float(mean(profile)), 3)

        return {
            "provider": self.name,
            "live": False,
            "source_detail": f"mapped-profile:{profile_name}",
            "carbon_profile": profile_name,
            "current_kg_per_kwh": current,
            "daily_average_kg_per_kwh": average,
            "relative_band": _band_from_ratio(current, average),
            "warnings": [],
        }


class ElectricityMapsCarbonProvider:
    name = "electricity_maps"

    def enrich(self, location: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        api_key = os.getenv("NEXUS_ELECTRICITYMAPS_API_KEY")
        if not api_key:
            raise GeoEnrichmentError(
                "Electricity Maps API key missing. Set NEXUS_ELECTRICITYMAPS_API_KEY."
            )

        payload = _http_get_json(
            ELECTRICITY_MAPS_BASE_URL,
            params={
                "lat": round(float(location["latitude"]), 6),
                "lon": round(float(location["longitude"]), 6),
            },
            headers={
                "auth-token": api_key,
                "User-Agent": "NEXUS-GRID/1.0 (carbon enrichment)",
            },
        )

        intensity_g = float(payload.get("carbonIntensity"))
        intensity_kg = round(intensity_g / 1000.0, 3)

        return {
            "provider": self.name,
            "live": True,
            "source_detail": "electricity-maps-latest",
            "carbon_profile": str(schema.get("carbon_profile", "custom")),
            "current_kg_per_kwh": intensity_kg,
            "current_g_per_kwh": round(intensity_g, 1),
            "zone": payload.get("zone"),
            "is_estimated": bool(payload.get("isEstimated", False)),
            "updated_at": payload.get("updatedAt"),
            "observed_at": payload.get("datetime"),
            "warnings": [],
        }


class RegionalHeuristicTariffProvider:
    name = "heuristic"

    def enrich(self, location: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        currency, off_peak, shoulder, peak = _country_tariff_defaults(
            str(location.get("country_code", "custom"))
        )
        current_hour = _utc_now().hour
        if 0 <= current_hour < 6:
            current_window = "off_peak"
            current_rate = off_peak
        elif 17 <= current_hour < 22:
            current_window = "peak"
            current_rate = peak
        else:
            current_window = "shoulder"
            current_rate = shoulder

        return {
            "provider": self.name,
            "live": False,
            "source_detail": f"regional-heuristic:{location.get('country_code', 'custom')}",
            "currency": currency,
            "current_window": current_window,
            "current_rate": round(current_rate, 4),
            "weekday_schedule": {
                "off_peak": round(off_peak, 4),
                "shoulder": round(shoulder, 4),
                "peak": round(peak, 4),
            },
            "recommended_strategy": (
                "charge_flexible_assets_off_peak"
                if current_window == "off_peak"
                else "shift_load_away_from_peak"
            ),
            "warnings": [],
        }


class OpenEITariffProvider:
    name = "openei"

    def enrich(self, location: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if str(location.get("country_code", "")).lower() != "us":
            raise GeoEnrichmentError(
                "OpenEI tariff lookup is currently wired for U.S. locations only."
            )

        api_key = os.getenv("NEXUS_OPENEI_API_KEY")
        if not api_key:
            raise GeoEnrichmentError("OpenEI API key missing. Set NEXUS_OPENEI_API_KEY.")

        payload = _http_get_json(
            OPENEI_BASE_URL,
            params={
                "version": "latest",
                "format": "json",
                "api_key": api_key,
                "lat": round(float(location["latitude"]), 6),
                "lon": round(float(location["longitude"]), 6),
                "is_default": "true",
                "limit": 1,
                "detail": "full",
                "sector": _schema_sector(schema),
            },
            headers={"User-Agent": "NEXUS-GRID/1.0 (tariff enrichment)"},
        )

        items = payload.get("items", [])
        if not items:
            raise GeoEnrichmentError("OpenEI returned no tariff records for this location.")

        item = items[0]
        energy_rate = _extract_first_energy_rate(item.get("energyratestructure"))

        return {
            "provider": self.name,
            "live": True,
            "source_detail": "openei-utility-rates",
            "utility": item.get("utility"),
            "rate_name": item.get("name"),
            "sector": item.get("sector"),
            "service_type": item.get("servicetype"),
            "energy_rate": energy_rate,
            "fixed_charge": {
                "amount": item.get("fixedchargefirstmeter"),
                "unit": item.get("fixedchargeunits"),
            },
            "distributed_generation_rules": item.get("dgrules"),
            "uri": item.get("uri"),
            "warnings": [],
        }


class GeoEnrichmentService:
    """Facade for location-aware operational enrichment."""

    def __init__(self):
        self.weather_providers = {
            "open_meteo": OpenMeteoWeatherProvider(),
            "heuristic": HeuristicWeatherProvider(),
        }
        self.carbon_providers = {
            "electricity_maps": ElectricityMapsCarbonProvider(),
            "profile": ProfileCarbonProvider(),
        }
        self.tariff_providers = {
            "openei": OpenEITariffProvider(),
            "heuristic": RegionalHeuristicTariffProvider(),
        }

    def list_providers(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "weather": [
                {
                    "id": "auto",
                    "label": "Auto",
                    "requires_api_key": False,
                    "notes": "Tries Open-Meteo first, then falls back to heuristics.",
                },
                {
                    "id": "open_meteo",
                    "label": "Open-Meteo",
                    "requires_api_key": False,
                    "notes": "Live weather and solar context from the public forecast API.",
                },
                {
                    "id": "heuristic",
                    "label": "Heuristic",
                    "requires_api_key": False,
                    "notes": "Offline fallback based on latitude and seasonality.",
                },
            ],
            "carbon": [
                {
                    "id": "auto",
                    "label": "Auto",
                    "requires_api_key": False,
                    "notes": "Tries Electricity Maps first, then mapped static profiles.",
                },
                {
                    "id": "electricity_maps",
                    "label": "Electricity Maps",
                    "requires_api_key": True,
                    "env_var": "NEXUS_ELECTRICITYMAPS_API_KEY",
                    "configured": bool(os.getenv("NEXUS_ELECTRICITYMAPS_API_KEY")),
                    "notes": "Live carbon-intensity lookup by geolocation.",
                },
                {
                    "id": "profile",
                    "label": "Mapped Profile",
                    "requires_api_key": False,
                    "notes": "Uses the sandbox-compatible regional carbon profile.",
                },
            ],
            "tariff": [
                {
                    "id": "auto",
                    "label": "Auto",
                    "requires_api_key": False,
                    "notes": "Tries OpenEI first for U.S. locations, then regional heuristics.",
                },
                {
                    "id": "openei",
                    "label": "OpenEI",
                    "requires_api_key": True,
                    "env_var": "NEXUS_OPENEI_API_KEY",
                    "configured": bool(os.getenv("NEXUS_OPENEI_API_KEY")),
                    "notes": "Utility-rate lookup from the OpenEI utility rates API.",
                },
                {
                    "id": "heuristic",
                    "label": "Regional Heuristic",
                    "requires_api_key": False,
                    "notes": "Country-aware flat and time-of-use tariff fallback.",
                },
            ],
        }

    def enrich(
        self,
        location: Dict[str, Any],
        schema: Dict[str, Any],
        weather_provider: str = "auto",
        carbon_provider: str = "auto",
        tariff_provider: str = "auto",
    ) -> Dict[str, Any]:
        weather, weather_warnings = self._resolve_weather(location, weather_provider)
        carbon, carbon_warnings = self._resolve_carbon(location, schema, carbon_provider)
        tariff, tariff_warnings = self._resolve_tariff(location, schema, tariff_provider)

        warnings = weather_warnings + carbon_warnings + tariff_warnings
        return {
            "weather": weather,
            "carbon": carbon,
            "tariff": tariff,
            "warnings": warnings,
            "applied_providers": {
                "weather": weather["provider"],
                "carbon": carbon["provider"],
                "tariff": tariff["provider"],
            },
        }

    def attach_to_schema(self, schema: Dict[str, Any], enrichment: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(schema)
        enriched["operating_context"] = {
            "weather": enrichment["weather"],
            "carbon": enrichment["carbon"],
            "tariff": enrichment["tariff"],
        }

        data_sources = dict(enriched.get("data_sources", {}))
        data_sources["weather_live"] = enrichment["weather"]["source_detail"]
        data_sources["carbon_live"] = enrichment["carbon"]["source_detail"]
        data_sources["tariffs_live"] = enrichment["tariff"]["source_detail"]
        enriched["data_sources"] = data_sources

        generation_summary = dict(enriched.get("generation_summary", {}))
        generation_summary["enriched"] = True
        generation_summary["applied_weather_provider"] = enrichment["weather"]["provider"]
        generation_summary["applied_carbon_provider"] = enrichment["carbon"]["provider"]
        generation_summary["applied_tariff_provider"] = enrichment["tariff"]["provider"]
        generation_summary["solar_capacity_factor"] = enrichment["weather"]["forecast"].get(
            "solar_capacity_factor"
        )
        generation_summary["carbon_band"] = enrichment["carbon"].get("relative_band")
        generation_summary["tariff_window"] = enrichment["tariff"].get("current_window")
        enriched["generation_summary"] = generation_summary

        if enrichment["warnings"]:
            enriched["enrichment_warnings"] = enrichment["warnings"]

        return enriched

    def _resolve_weather(
        self,
        location: Dict[str, Any],
        provider: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        order = ["open_meteo", "heuristic"] if provider == "auto" else [provider]
        return self._resolve_generic(self.weather_providers, order, location, requested_provider=provider)

    def _resolve_carbon(
        self,
        location: Dict[str, Any],
        schema: Dict[str, Any],
        provider: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        order = ["electricity_maps", "profile"] if provider == "auto" else [provider]
        return self._resolve_generic(
            self.carbon_providers,
            order,
            location,
            schema,
            requested_provider=provider,
        )

    def _resolve_tariff(
        self,
        location: Dict[str, Any],
        schema: Dict[str, Any],
        provider: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        order = ["openei", "heuristic"] if provider == "auto" else [provider]
        return self._resolve_generic(
            self.tariff_providers,
            order,
            location,
            schema,
            requested_provider=provider,
        )

    def _resolve_generic(
        self,
        registry: Dict[str, Any],
        order: List[str],
        location: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
        requested_provider: str = "auto",
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        for provider_name in order:
            if provider_name not in registry:
                raise GeoEnrichmentError(
                    f"Unknown enrichment provider '{provider_name}'."
                )
            provider = registry[provider_name]
            try:
                if schema is None:
                    return provider.enrich(location), warnings
                return provider.enrich(location, schema), warnings
            except GeoEnrichmentError as exc:
                if self._should_warn(requested_provider, provider_name, str(exc)):
                    warnings.append(f"{provider_name}: {exc}")
                continue

        raise GeoEnrichmentError("No enrichment provider could satisfy the request.")

    def _should_warn(self, requested_provider: str, provider_name: str, message: str) -> bool:
        if requested_provider != "auto":
            return True

        normalized = message.lower()
        if provider_name == "electricity_maps" and "api key missing" in normalized:
            return False
        if provider_name == "openei" and (
            "api key missing" in normalized or "wired for u.s. locations only" in normalized
        ):
            return False
        return True


def _schema_sector(schema: Dict[str, Any]) -> str:
    building_types = [str(building.get("type", "")).lower() for building in schema.get("buildings", [])]
    if any(building_type == "industrial" for building_type in building_types):
        return "Industrial"
    if any(building_type in {"commercial", "hospital", "campus"} for building_type in building_types):
        return "Commercial"
    return "Residential"


def _extract_first_energy_rate(structure: Any) -> Dict[str, Any]:
    if not isinstance(structure, list):
        return {"rate": None, "unit": None}

    for period in structure:
        if not isinstance(period, list):
            continue
        for tier in period:
            if not isinstance(tier, dict):
                continue
            if tier.get("rate") is not None:
                return {
                    "rate": tier.get("rate"),
                    "unit": tier.get("unit"),
                    "adjustment": tier.get("adj"),
                    "sell_rate": tier.get("sell"),
                }
    return {"rate": None, "unit": None}


def _solar_outlook(solar_capacity_factor: float) -> str:
    if solar_capacity_factor >= 1.0:
        return "strong"
    if solar_capacity_factor >= 0.75:
        return "balanced"
    return "constrained"


geo_enrichment_service = GeoEnrichmentService()
