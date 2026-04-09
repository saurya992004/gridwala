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
    "https://api.electricitymaps.com/v4",
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


def _electricity_maps_headers(api_key: str) -> Dict[str, str]:
    return {
        "auth-token": api_key,
        "User-Agent": "NEXUS-GRID/1.0 (electricity maps signal spine)",
    }


def _electricity_maps_latest(
    path: str,
    location: Dict[str, Any],
    api_key: str,
) -> Dict[str, Any]:
    return _http_get_json(
        f"{ELECTRICITY_MAPS_BASE_URL.rstrip('/')}/{path.lstrip('/')}",
        params={
            "lat": round(float(location["latitude"]), 6),
            "lon": round(float(location["longitude"]), 6),
        },
        headers=_electricity_maps_headers(api_key),
    )


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


def _safe_optional_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_mapping_values(values: Any) -> Optional[float]:
    if not isinstance(values, dict):
        return None

    numeric_values: List[float] = []
    for value in values.values():
        numeric = _safe_optional_float(value)
        if numeric is not None:
            numeric_values.append(numeric)

    if not numeric_values:
        return None

    return round(sum(numeric_values), 1)


def _interchange_state(net_interchange_mw: Optional[float]) -> Optional[str]:
    if net_interchange_mw is None:
        return None
    if abs(net_interchange_mw) < 1.0:
        return "balanced"
    if net_interchange_mw > 0:
        return "net_importing"
    return "net_exporting"


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

        payload = _electricity_maps_latest("carbon-intensity/latest", location, api_key)

        intensity_g = float(payload.get("carbonIntensity"))
        intensity_kg = round(intensity_g / 1000.0, 3)
        warnings: List[str] = []
        disclaimer = payload.get("_disclaimer")
        if disclaimer:
            warnings.append(str(disclaimer))

        renewable_payload: Dict[str, Any] = {}
        load_payload: Dict[str, Any] = {}
        flows_payload: Dict[str, Any] = {}
        price_payload: Dict[str, Any] = {}

        try:
            renewable_payload = _electricity_maps_latest("renewable-energy/latest", location, api_key)
        except GeoEnrichmentError:
            renewable_payload = {}

        try:
            load_payload = _electricity_maps_latest("total-load/latest", location, api_key)
        except GeoEnrichmentError:
            load_payload = {}

        try:
            flows_payload = _electricity_maps_latest("electricity-flows/latest", location, api_key)
        except GeoEnrichmentError:
            flows_payload = {}

        try:
            price_payload = _electricity_maps_latest("price-day-ahead/latest", location, api_key)
        except GeoEnrichmentError:
            price_payload = {}

        flow_data = flows_payload.get("data")
        flow_snapshot = flow_data[0] if isinstance(flow_data, list) and flow_data else {}
        total_import_mw = _sum_mapping_values(flow_snapshot.get("import"))
        total_export_mw = _sum_mapping_values(flow_snapshot.get("export"))
        net_interchange_mw = (
            round(total_import_mw - total_export_mw, 1)
            if total_import_mw is not None and total_export_mw is not None
            else None
        )
        renewable_share_pct = _safe_optional_float(renewable_payload.get("value"))
        total_load_mw = _safe_optional_float(load_payload.get("value"))
        day_ahead_price = _safe_optional_float(price_payload.get("value"))
        provider_mode = "sandbox" if disclaimer else "live"

        signal_spine = {
            "provider": self.name,
            "provider_mode": provider_mode,
            "api_version": "v4",
            "source_detail": "electricity-maps-v4-signal-spine",
            "zone": payload.get("zone"),
            "renewable_share_pct": round(renewable_share_pct, 1) if renewable_share_pct is not None else None,
            "total_load_mw": round(total_load_mw, 2) if total_load_mw is not None else None,
            "total_import_mw": total_import_mw,
            "total_export_mw": total_export_mw,
            "net_interchange_mw": net_interchange_mw,
            "interchange_state": _interchange_state(net_interchange_mw),
            "day_ahead_price": round(day_ahead_price, 2) if day_ahead_price is not None else None,
            "day_ahead_price_unit": price_payload.get("unit"),
            "day_ahead_price_source": price_payload.get("source"),
            "is_estimated": bool(payload.get("isEstimated", False)),
            "estimation_method": payload.get("estimationMethod"),
            "updated_at": payload.get("updatedAt"),
            "observed_at": payload.get("datetime"),
        }

        return {
            "provider": self.name,
            "live": True,
            "source_detail": "electricity-maps-v4-carbon-intensity",
            "carbon_profile": str(schema.get("carbon_profile", "custom")),
            "current_kg_per_kwh": intensity_kg,
            "current_g_per_kwh": round(intensity_g, 1),
            "zone": payload.get("zone"),
            "is_estimated": bool(payload.get("isEstimated", False)),
            "updated_at": payload.get("updatedAt"),
            "observed_at": payload.get("datetime"),
            "provider_mode": provider_mode,
            "signal_spine": signal_spine,
            "warnings": warnings,
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

        requested_sector = _schema_sector(schema)
        candidate_sectors = _candidate_openei_sectors(requested_sector)
        item = None
        matched_sector = None

        for sector in candidate_sectors:
            params = {
                "version": "latest",
                "format": "json",
                "api_key": api_key,
                "lat": round(float(location["latitude"]), 6),
                "lon": round(float(location["longitude"]), 6),
                "is_default": "true",
                "limit": 1,
                "detail": "full",
            }
            if sector:
                params["sector"] = sector

            payload = _http_get_json(
                OPENEI_BASE_URL,
                params=params,
                headers={"User-Agent": "NEXUS-GRID/1.0 (tariff enrichment)"},
            )
            items = payload.get("items", [])
            if items:
                item = items[0]
                matched_sector = sector or item.get("sector")
                break

        if not item:
            raise GeoEnrichmentError("OpenEI returned no tariff records for this location.")

        energy_rate = _extract_first_energy_rate(item.get("energyratestructure"))
        current_window, current_rate, rate_band, period_rates, weekday_schedule, weekend_schedule = (
            _extract_openei_tariff_runtime(item)
        )
        warnings: List[str] = []
        if matched_sector and requested_sector != matched_sector:
            warnings.append(
                f"OpenEI matched sector '{matched_sector}' after '{requested_sector}' returned no default tariff."
            )

        return {
            "provider": self.name,
            "live": True,
            "source_detail": "openei-utility-rates",
            "utility": item.get("utility"),
            "rate_name": item.get("name"),
            "sector": item.get("sector"),
            "requested_sector": requested_sector,
            "matched_sector": matched_sector,
            "service_type": item.get("servicetype"),
            "energy_rate": energy_rate,
            "currency": "USD",
            "current_window": current_window,
            "current_rate": current_rate,
            "rate_band": rate_band,
            "period_rates": period_rates,
            "weekday_period_schedule": weekday_schedule,
            "weekend_period_schedule": weekend_schedule,
            "fixed_charge": {
                "amount": item.get("fixedchargefirstmeter"),
                "unit": item.get("fixedchargeunits"),
            },
            "distributed_generation_rules": item.get("dgrules"),
            "uri": item.get("uri"),
            "warnings": warnings,
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
        carbon_signal_spine = enrichment["carbon"].get("signal_spine", {})
        if isinstance(carbon_signal_spine, dict) and carbon_signal_spine.get("source_detail"):
            data_sources["grid_signal_spine"] = carbon_signal_spine["source_detail"]
        enriched["data_sources"] = data_sources

        generation_summary = dict(enriched.get("generation_summary", {}))
        generation_summary["enriched"] = True
        generation_summary["applied_weather_provider"] = enrichment["weather"]["provider"]
        generation_summary["applied_carbon_provider"] = enrichment["carbon"]["provider"]
        generation_summary["applied_tariff_provider"] = enrichment["tariff"]["provider"]
        generation_summary["electricity_maps_provider_mode"] = enrichment["carbon"].get(
            "provider_mode"
        )
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


def _candidate_openei_sectors(primary_sector: str) -> List[Optional[str]]:
    ordered = [primary_sector, "Residential", "Commercial", "Industrial", None]
    unique: List[Optional[str]] = []
    for sector in ordered:
        if sector not in unique:
            unique.append(sector)
    return unique


def _extract_openei_tariff_runtime(item: Dict[str, Any]) -> Tuple[str, Optional[float], str, Dict[str, float], List[int], List[int]]:
    period_rates = _extract_period_rates(item.get("energyratestructure"))
    weekday_schedule = _extract_hour_schedule(item.get("energyweekdayschedule"))
    weekend_schedule = _extract_hour_schedule(item.get("energyweekendschedule"))
    is_weekend = _utc_now().weekday() >= 5
    active_schedule = weekend_schedule if is_weekend else weekday_schedule
    hour = _utc_now().hour
    period = active_schedule[hour] if hour < len(active_schedule) else None
    current_rate = period_rates.get(period) if period is not None else None
    rate_band = _band_from_reference(current_rate, list(period_rates.values()))
    window = f"period_{period}" if period is not None else "utility_schedule"
    return window, current_rate, rate_band, period_rates, weekday_schedule, weekend_schedule


def _extract_period_rates(structure: Any) -> Dict[int, float]:
    period_rates: Dict[int, float] = {}
    if not isinstance(structure, list):
        return period_rates

    for period_idx, period in enumerate(structure):
        if not isinstance(period, list):
            continue
        rates = [
            float(tier.get("rate"))
            for tier in period
            if isinstance(tier, dict) and tier.get("rate") is not None
        ]
        if rates:
            period_rates[period_idx] = round(rates[0], 6)
    return period_rates


def _extract_hour_schedule(raw_schedule: Any) -> List[int]:
    if not isinstance(raw_schedule, list) or not raw_schedule:
        return []
    month_index = max(0, min(_utc_now().month - 1, len(raw_schedule) - 1))
    month_schedule = raw_schedule[month_index]
    if not isinstance(month_schedule, list):
        return []
    return [int(value) for value in month_schedule[:24]]


def _band_from_reference(current_rate: Optional[float], reference_rates: List[float]) -> str:
    if current_rate is None:
        return "unknown"
    clean_rates = [float(rate) for rate in reference_rates if rate is not None]
    if not clean_rates:
        return "moderate"

    minimum = min(clean_rates)
    maximum = max(clean_rates)
    if abs(maximum - minimum) < 1e-9:
        return "flat"

    midpoint = minimum + ((maximum - minimum) * 0.5)
    if current_rate <= minimum + ((maximum - minimum) * 0.2):
        return "low"
    if current_rate >= midpoint + ((maximum - midpoint) * 0.4):
        return "high"
    return "moderate"


def _solar_outlook(solar_capacity_factor: float) -> str:
    if solar_capacity_factor >= 1.0:
        return "strong"
    if solar_capacity_factor >= 0.75:
        return "balanced"
    return "constrained"


geo_enrichment_service = GeoEnrichmentService()
