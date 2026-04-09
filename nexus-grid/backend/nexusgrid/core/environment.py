"""
NEXUS GRID - Sandbox Grid Environment Engine v1.0
Custom multi-building energy simulation core used for the current sandbox mode.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional

import numpy as np

from nexusgrid.core.carbon_profiles import get_profile


HOURS_PER_DAY = 24
DAYS_PER_YEAR = 365
TOTAL_STEPS = HOURS_PER_DAY * DAYS_PER_YEAR
ENGINE_NAME = "nexus-sandbox-engine"
ENGINE_VERSION = "1.0.0"
ENGINE_MODE = "sandbox"


def _solar_curve(hour: int, day_of_year: int) -> float:
    """Generate a normalized solar irradiance factor for the current hour and season."""
    seasonal = 0.6 + 0.4 * math.cos(2 * math.pi * (day_of_year - 172) / 365)
    if 6 <= hour <= 18:
        solar = seasonal * math.exp(-0.5 * ((hour - 12) / 3.0) ** 2)
    else:
        solar = 0.0
    return max(0.0, solar)


def _building_base_load(hour: int, building_id: int) -> float:
    """Return the base electricity demand for a building at a given hour."""
    morning = math.exp(-0.5 * ((hour - 8) / 1.5) ** 2)
    evening = math.exp(-0.5 * ((hour - 20) / 2.0) ** 2)
    base = 1.5 + 3.0 * morning + 4.0 * evening
    offset = 0.8 + (building_id % 5) * 0.3
    return round(base * offset, 4)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _time_of_use_window(hour: int) -> str:
    if 0 <= hour < 6:
        return "off_peak"
    if 17 <= hour < 22:
        return "peak"
    return "shoulder"


def _load_factor_from_temperature(temperature_c: float) -> float:
    cooling = max(temperature_c - 24.0, 0.0) * 0.018
    heating = max(18.0 - temperature_c, 0.0) * 0.01
    return round(_clamp(1.0 + cooling + heating, 0.82, 1.45), 3)


def _rate_band(rate: Optional[float], reference_rates: List[float], default: str = "moderate") -> str:
    if rate is None:
        return default

    clean = [float(item) for item in reference_rates if item is not None]
    if not clean:
        return default

    minimum = min(clean)
    maximum = max(clean)
    if abs(maximum - minimum) < 1e-9:
        return "flat"

    if rate <= minimum + ((maximum - minimum) * 0.2):
        return "low"
    if rate >= maximum - ((maximum - minimum) * 0.2):
        return "high"
    return "moderate"


class Building:
    """Represents a single smart building with solar PV and battery storage."""

    def __init__(self, building_id: int, config: Dict[str, Any]):
        self.id = config.get("name", f"Building_{building_id + 1}")
        self._bid = building_id
        self.BATTERY_CAPACITY = float(config.get("battery_kwh", 10.0))
        self.BATTERY_MAX_RATE = float(config.get("battery_max_rate_kw", 3.0))
        self.SOLAR_PEAK_KW = float(config.get("solar_peak_kw", 5.0))
        self._load_mult_base = float(config.get("load_multiplier", 1.0))
        self.type = config.get("type", "residential").lower()
        self.is_ev = self.type == "ev"
        self._ev_away = False

        self.battery_soc: float = self.BATTERY_CAPACITY * 0.5
        self.nexus_tokens: float = 0.0
        self.history: Dict[str, List] = {
            "net_consumption": [],
            "solar": [],
            "battery_soc": [],
            "nexus_tokens": [],
            "reward": [],
        }

    def step(
        self,
        hour: int,
        day: int,
        action: float,
        solar_mult: float = 1.0,
        load_mult: float = 1.0,
        carbon_intensity: float = 0.0,
        tariff_rate: float = 0.15,
    ) -> Dict[str, float]:
        action = max(-1.0, min(1.0, float(action)))
        solar = _solar_curve(hour, day) * self.SOLAR_PEAK_KW * solar_mult
        base_load = _building_base_load(hour, self._bid) * self._load_mult_base * load_mult

        if self.is_ev:
            if 8 <= hour < 18:
                if not self._ev_away:
                    self._ev_away = True
                    drain = self.BATTERY_CAPACITY * 0.3
                    self.battery_soc = max(0.0, self.battery_soc - drain)

                action = 0.0
                solar = 0.0
                base_load = 0.0
            else:
                self._ev_away = False
                base_load = 0.0

        charge_delta = action * self.BATTERY_MAX_RATE
        if charge_delta > 0:
            actual_charge = min(charge_delta, self.BATTERY_CAPACITY - self.battery_soc)
        else:
            actual_charge = max(charge_delta, -self.battery_soc)

        self.battery_soc = round(self.battery_soc + actual_charge, 4)
        net = round(base_load + actual_charge - solar, 4)

        soc_ratio = self.battery_soc / self.BATTERY_CAPACITY
        import_penalty = max(net, 0.0) * ((tariff_rate * 0.08) + (carbon_intensity * 0.45))
        export_credit = max(-net, 0.0) * max(tariff_rate * 0.03, 0.0)
        reward = round(
            (-abs(net) * 0.45) - import_penalty + export_credit + (0.5 - abs(soc_ratio - 0.5)) * 0.35,
            4,
        )

        return {
            "id": self.id,
            "type": self.type,
            "is_ev_away": self._ev_away if self.is_ev else False,
            "net_electricity_consumption": net,
            "solar_generation": round(solar, 4),
            "battery_soc": round(self.battery_soc / self.BATTERY_CAPACITY, 4),
            "reward": reward,
            "estimated_grid_cost": round(max(net, 0.0) * tariff_rate, 4),
            "raw_soc_kwh": self.battery_soc,
        }

    def log_step(self, payload: Dict[str, Any]):
        self.nexus_tokens += payload.get("nexus_tokens_earned", 0.0)
        self.history["net_consumption"].append(payload["net_electricity_consumption"])
        self.history["solar"].append(payload["solar_generation"])
        self.history["battery_soc"].append(payload["raw_soc_kwh"])
        self.history["nexus_tokens"].append(self.nexus_tokens)
        self.history["reward"].append(payload["reward"])
        payload.pop("raw_soc_kwh", None)
        payload["nexus_wallet"] = round(self.nexus_tokens, 2)

    def reset(self):
        self.battery_soc = self.BATTERY_CAPACITY * 0.5
        self.nexus_tokens = 0.0
        self._ev_away = False
        self.history = {key: [] for key in self.history}


_DEFAULT_SCHEMA: Dict[str, Any] = {
    "district_name": "NEXUS Demo District",
    "carbon_profile": "uk_national_grid",
    "buildings": [
        {
            "name": f"Building_{i + 1}",
            "battery_kwh": 10.0,
            "solar_peak_kw": 5.0,
            "battery_max_rate_kw": 3.0,
            "load_multiplier": 1.0,
        }
        for i in range(5)
    ],
}


class NexusGridEnv:
    """
    Sandbox smart-grid environment.

    Accepts any validated Nexus schema dict and simulates a district of
    buildings with solar PV, battery storage, and a shared grid signal.
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        cfg = schema or _DEFAULT_SCHEMA
        self._schema = cfg
        self._district_name = cfg.get("district_name", "NEXUS District")
        self._carbon_profile = get_profile(cfg.get("carbon_profile", "uk_national_grid"))
        self._carbon_profile_average = float(mean(self._carbon_profile))
        self._topology_summary = dict(cfg.get("topology_summary", {}))
        self._geo_context = dict(cfg.get("geo_context", {}))
        self._twin_summary = dict(cfg.get("twin_summary", {}))
        self._atlas_context = dict(cfg.get("atlas_context", {}))
        self._twin_provenance = dict(cfg.get("twin_provenance", {}))
        self._data_sources = dict(cfg.get("data_sources", {}))
        self._enrichment_warnings = list(cfg.get("enrichment_warnings", []))
        self._control_entities = [dict(entity) for entity in cfg.get("control_entities", [])]
        self._buildings = [Building(i, building_cfg) for i, building_cfg in enumerate(cfg["buildings"])]
        self._step_count = 0
        self._rng = np.random.default_rng(seed=42)
        self._last_payload: Optional[Dict[str, Any]] = None

        self._weather_context = dict(cfg.get("operating_context", {}).get("weather", {}))
        self._carbon_context = dict(cfg.get("operating_context", {}).get("carbon", {}))
        self._tariff_context = dict(cfg.get("operating_context", {}).get("tariff", {}))
        self._grid_signal_spine = dict(self._carbon_context.get("signal_spine", {}))
        self._context_enabled = bool(cfg.get("operating_context"))
        self._context_live = any(
            bool(context.get("live"))
            for context in (self._weather_context, self._carbon_context, self._tariff_context)
        )
        if self._context_enabled and self._context_live:
            self._context_mode = "live_enriched"
        elif self._context_enabled:
            self._context_mode = "enriched"
        else:
            self._context_mode = "static"

        self._weather_source = self._weather_context.get("source_detail", "static-profile")
        self._carbon_source = self._carbon_context.get("source_detail", "static-profile")
        self._tariff_source = self._tariff_context.get("source_detail", "flat-default")
        self._weather_outlook = self._weather_context.get("forecast", {}).get("outlook", "balanced")
        self._base_solar_capacity_factor = _safe_float(
            self._weather_context.get("forecast", {}).get("solar_capacity_factor"),
            cfg.get("generation_summary", {}).get("solar_capacity_factor", 1.0),
        )
        current_weather = self._weather_context.get("current", {})
        forecast_weather = self._weather_context.get("forecast", {})
        self._cloud_cover_pct = _safe_float(current_weather.get("cloud_cover_pct"), 15.0)
        self._base_temperature_c = _safe_float(
            current_weather.get("temperature_c"),
            _safe_float(forecast_weather.get("next_24h_avg_temperature_c"), 22.0),
        )
        self._weather_cloud_factor = _clamp(1.0 - ((self._cloud_cover_pct / 100.0) * 0.35), 0.6, 1.05)
        self._weather_load_factor = _load_factor_from_temperature(self._base_temperature_c)
        self._carbon_anchor = _safe_float(
            self._carbon_context.get("current_kg_per_kwh"),
            self._carbon_profile[_safe_int(datetime.now(timezone.utc).hour, 0)],
        )
        self._carbon_anchor_average = _safe_float(
            self._carbon_context.get("daily_average_kg_per_kwh"),
            self._carbon_profile_average,
        )

        now = datetime.now(timezone.utc)
        self._start_hour = now.hour if self._context_enabled else 0
        self._start_day = (now.timetuple().tm_yday - 1) if self._context_enabled else 0
        self._start_weekday = now.weekday()

        self._solar_mult = 1.0
        self._load_mult = 1.0
        self._carbon_mult = 1.0
        self._emergency_steps_left = 0
        self._forecast_scenario: Optional[str] = None
        self._forecast_steps_left = 0

    def reset(self) -> List[Dict]:
        for building in self._buildings:
            building.reset()
        self._step_count = 0
        self._last_payload = None
        self._solar_mult = 1.0
        self._load_mult = 1.0
        self._carbon_mult = 1.0
        self._emergency_steps_left = 0
        self._forecast_scenario = None
        self._forecast_steps_left = 0
        return [{"id": building.id, "battery_soc": 0.5} for building in self._buildings]

    def step(self, actions: Optional[List[float]] = None) -> Dict[str, Any]:
        if actions is None:
            actions = [0.0] * len(self._buildings)

        hour = (self._start_hour + self._step_count) % HOURS_PER_DAY
        day = (self._start_day + (self._step_count // HOURS_PER_DAY)) % DAYS_PER_YEAR
        runtime_context = self._resolve_runtime_context(hour, day)
        solar_multiplier = runtime_context["solar_multiplier"] * self._solar_mult
        load_multiplier = runtime_context["load_multiplier"] * self._load_mult
        carbon_intensity = _clamp(
            runtime_context["carbon_intensity"] * self._carbon_mult,
            0.02,
            2.5,
        )
        tariff_rate = runtime_context["tariff_rate"]
        buildings_data = []

        for i, building in enumerate(self._buildings):
            action = float(actions[i]) if i < len(actions) else 0.0
            data = building.step(
                hour,
                day,
                action,
                solar_mult=solar_multiplier,
                load_mult=load_multiplier,
                carbon_intensity=carbon_intensity,
                tariff_rate=tariff_rate,
            )
            buildings_data.append(data)

        grid_buy_price = tariff_rate
        grid_sell_price = runtime_context["grid_export_rate"]
        total_surplus = 0.0
        total_shortage = 0.0
        shorters = []
        longers = []

        for data in buildings_data:
            net = data["net_electricity_consumption"]
            data["p2p_traded_kwh"] = 0.0
            data["grid_exchanged_kwh"] = 0.0
            data["nexus_tokens_earned"] = 0.0

            if net < 0:
                surplus = abs(net)
                total_surplus += surplus
                longers.append((data, surplus))
            elif net > 0:
                shortage = net
                total_shortage += shortage
                shorters.append((data, shortage))

        p2p_pool = min(total_surplus, total_shortage)

        if total_surplus == 0 and total_shortage == 0:
            p2p_price = round((grid_buy_price + grid_sell_price) / 2.0, 4)
        else:
            supply_ratio = total_surplus / max(total_surplus + total_shortage, 0.0001)
            p2p_price = grid_buy_price - (supply_ratio * (grid_buy_price - grid_sell_price))
            p2p_price = round(p2p_price, 4)

        for data, surplus in longers:
            if total_surplus > 0:
                p2p_ratio = surplus / total_surplus
                sold_p2p = p2p_pool * p2p_ratio
                sold_grid = surplus - sold_p2p
                data["p2p_traded_kwh"] = round(sold_p2p, 4)
                data["grid_exchanged_kwh"] = round(-sold_grid, 4)
                data["nexus_tokens_earned"] = round(
                    (sold_p2p * p2p_price) + (sold_grid * grid_sell_price),
                    4,
                )

        for data, shortage in shorters:
            if total_shortage > 0:
                p2p_ratio = shortage / total_shortage
                bought_p2p = p2p_pool * p2p_ratio
                bought_grid = shortage - bought_p2p
                data["p2p_traded_kwh"] = round(bought_p2p, 4)
                data["grid_exchanged_kwh"] = round(bought_grid, 4)
                data["nexus_tokens_earned"] = round(
                    -((bought_p2p * p2p_price) + (bought_grid * grid_buy_price)),
                    4,
                )

        for data in buildings_data:
            data["reward"] = round(
                data["reward"]
                + (data["nexus_tokens_earned"] * 0.12)
                - (max(data["grid_exchanged_kwh"], 0.0) * carbon_intensity * 0.18),
                4,
            )
            data["grid_tariff_rate"] = round(grid_buy_price, 4)
            data["grid_tariff_window"] = runtime_context["tariff_window"]
            data["grid_tariff_currency"] = runtime_context["tariff_currency"]
            data["grid_tariff_band"] = runtime_context["tariff_band"]

        for building, data in zip(self._buildings, buildings_data):
            building.log_step(data)

        self._step_count += 1

        if self._forecast_steps_left > 0:
            self._forecast_steps_left -= 1
            if self._forecast_steps_left == 0 and self._forecast_scenario:
                self.set_emergency(self._forecast_scenario)
                self._forecast_scenario = None

        if self._emergency_steps_left > 0:
            self._emergency_steps_left -= 1
            if self._emergency_steps_left == 0:
                self.clear_emergency()

        district_net = round(sum(b["net_electricity_consumption"] for b in buildings_data), 4)

        payload = {
            "step": self._step_count,
            "hour": hour,
            "day": day,
            "done": self._step_count >= TOTAL_STEPS,
            "district_name": self._district_name,
            "buildings": buildings_data,
            "carbon_intensity": carbon_intensity,
            "district_net_consumption": district_net,
            "p2p_volume_kwh": round(p2p_pool, 4),
            "p2p_clearing_price": p2p_price,
            "forecast_scenario": self._forecast_scenario,
            "forecast_steps_left": self._forecast_steps_left,
            "grid_tariff_rate": round(grid_buy_price, 4),
            "grid_export_rate": round(grid_sell_price, 4),
            "grid_tariff_currency": runtime_context["tariff_currency"],
            "grid_tariff_window": runtime_context["tariff_window"],
            "grid_tariff_band": runtime_context["tariff_band"],
            "ambient_temperature_c": runtime_context["temperature_c"],
            "solar_capacity_factor": runtime_context["solar_capacity_factor"],
            "weather_outlook": runtime_context["weather_outlook"],
            "weather_source": self._weather_source,
            "carbon_source": self._carbon_source,
            "tariff_source": self._tariff_source,
            "operating_context_mode": self._context_mode,
            "operating_context_live": self._context_live,
            "electricity_maps_zone": self._grid_signal_spine.get("zone"),
            "electricity_maps_provider_mode": self._grid_signal_spine.get("provider_mode"),
            "grid_signal_estimated": self._grid_signal_spine.get("is_estimated"),
            "grid_renewable_share_pct": self._grid_signal_spine.get("renewable_share_pct"),
            "grid_total_load_mw": self._grid_signal_spine.get("total_load_mw"),
            "grid_import_mw": self._grid_signal_spine.get("total_import_mw"),
            "grid_export_mw": self._grid_signal_spine.get("total_export_mw"),
            "grid_net_interchange_mw": self._grid_signal_spine.get("net_interchange_mw"),
            "grid_interchange_state": self._grid_signal_spine.get("interchange_state"),
            "grid_wholesale_price": self._grid_signal_spine.get("day_ahead_price"),
            "grid_wholesale_price_unit": self._grid_signal_spine.get("day_ahead_price_unit"),
            "topology_summary": self._topology_summary,
            "geo_context": self._geo_context,
            "twin_summary": self._twin_summary,
            "atlas_context": self._atlas_context,
            "control_entities": self._control_entities,
            "twin_provenance": self._twin_provenance,
            "data_sources": self._data_sources,
            "enrichment_warnings": self._enrichment_warnings,
        }
        self._last_payload = payload
        return payload

    def _resolve_runtime_context(self, hour: int, day: int) -> Dict[str, Any]:
        temperature_c = self._resolve_temperature(hour)
        solar_capacity_factor = self._resolve_solar_capacity_factor(hour)
        load_factor = _load_factor_from_temperature(temperature_c)
        carbon_intensity = self._resolve_carbon_intensity(hour)
        tariff_rate, tariff_window, tariff_band = self._resolve_tariff(hour, day)
        grid_export_rate = max(0.03, round(tariff_rate * 0.42, 4))

        return {
            "temperature_c": temperature_c,
            "solar_capacity_factor": solar_capacity_factor,
            "solar_multiplier": solar_capacity_factor,
            "load_multiplier": load_factor,
            "carbon_intensity": carbon_intensity,
            "tariff_rate": tariff_rate,
            "tariff_window": tariff_window,
            "tariff_band": tariff_band,
            "tariff_currency": self._tariff_context.get("currency", "USD"),
            "weather_outlook": self._weather_outlook,
            "grid_export_rate": grid_export_rate,
        }

    def _resolve_temperature(self, hour: int) -> float:
        if not self._context_enabled:
            return 22.0

        daily_wave = math.cos(2 * math.pi * (hour - 15) / 24)
        temperature = self._base_temperature_c + (4.0 * daily_wave)
        return round(temperature, 1)

    def _resolve_solar_capacity_factor(self, hour: int) -> float:
        if not self._context_enabled:
            return 1.0

        morning_haze = 0.94 + (0.05 * math.sin(2 * math.pi * (hour - 7) / 24))
        modifier = self._base_solar_capacity_factor * self._weather_cloud_factor * morning_haze
        return round(_clamp(modifier, 0.45, 1.35), 3)

    def _resolve_carbon_intensity(self, hour: int) -> float:
        profile_hour = float(self._carbon_profile[hour])
        if self._context_enabled:
            deviation = profile_hour - self._carbon_anchor_average
            anchored = self._carbon_anchor + (0.55 * deviation)
        else:
            anchored = profile_hour

        noise = float(self._rng.normal(0, 0.006 if self._context_enabled else 0.01))
        return round(_clamp(anchored + noise, 0.02, 2.5), 4)

    def _resolve_tariff(self, hour: int, day: int) -> tuple[float, str, str]:
        if not self._context_enabled:
            return 0.15, "flat", "moderate"

        weekday_schedule = self._tariff_context.get("weekday_schedule")
        period_rates = self._tariff_context.get("period_rates")
        if isinstance(period_rates, dict):
            schedule = self._resolve_period_schedule()
            if schedule and hour < len(schedule):
                period = int(schedule[hour])
                rate = self._lookup_period_rate(period_rates, period)
                if rate is not None:
                    band = _rate_band(rate, [self._lookup_period_rate(period_rates, key) for key in period_rates], self._tariff_context.get("rate_band", "moderate"))
                    return round(rate, 4), f"period_{period}", band

        if isinstance(weekday_schedule, dict):
            window = _time_of_use_window(hour)
            rates = [value for value in weekday_schedule.values() if value is not None]
            rate = _safe_float(weekday_schedule.get(window), self._tariff_context.get("current_rate", 0.15))
            band = _rate_band(rate, rates, self._tariff_context.get("rate_band", "moderate"))
            return round(rate, 4), window, band

        rate = _safe_float(self._tariff_context.get("current_rate"), 0.15)
        window = str(self._tariff_context.get("current_window", "flat"))
        band = str(self._tariff_context.get("rate_band", "moderate"))
        return round(rate, 4), window, band

    def _resolve_period_schedule(self) -> List[int]:
        weekday = (self._start_weekday + (self._step_count // HOURS_PER_DAY)) % 7
        is_weekend = weekday >= 5
        key = "weekend_period_schedule" if is_weekend else "weekday_period_schedule"
        schedule = self._tariff_context.get(key, [])
        if isinstance(schedule, list):
            return [int(item) for item in schedule[:24]]
        return []

    def _lookup_period_rate(self, period_rates: Dict[Any, Any], period: Any) -> Optional[float]:
        if period in period_rates:
            return _safe_float(period_rates[period], 0.0)
        period_key = str(period)
        if period_key in period_rates:
            return _safe_float(period_rates[period_key], 0.0)
        return None

    def set_emergency(self, scenario: str):
        if scenario == "solar_offline":
            self._solar_mult = 0.0
            self._emergency_steps_left = 12
        elif scenario == "carbon_spike":
            self._carbon_mult = 2.0
            self._emergency_steps_left = 6
        elif scenario == "heatwave":
            self._load_mult = 2.0
            self._emergency_steps_left = 8

    def clear_emergency(self):
        self._solar_mult = 1.0
        self._load_mult = 1.0
        self._carbon_mult = 1.0
        self._emergency_steps_left = 0

    def set_forecast(self, scenario: str, steps_ahead: int = 4):
        self._forecast_scenario = scenario
        self._forecast_steps_left = steps_ahead

    @property
    def last_payload(self) -> Optional[Dict[str, Any]]:
        return self._last_payload

    @property
    def building_names(self) -> List[str]:
        return [building.id for building in self._buildings]

    @property
    def seed_buildings(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": building.id,
                "type": building.type,
                "is_ev_away": False,
                "net_electricity_consumption": 0.0,
                "solar_generation": 0.0,
                "battery_soc": 0.5,
                "reward": 0.0,
                "p2p_traded_kwh": 0.0,
                "grid_exchanged_kwh": 0.0,
                "nexus_tokens_earned": 0.0,
                "nexus_wallet": 0.0,
            }
            for building in self._buildings
        ]

    @property
    def n_buildings(self) -> int:
        return len(self._buildings)

    @property
    def max_steps(self) -> int:
        return TOTAL_STEPS

    @property
    def engine_mode(self) -> str:
        return ENGINE_MODE

    @property
    def engine_name(self) -> str:
        return ENGINE_NAME

    @property
    def engine_version(self) -> str:
        return ENGINE_VERSION

    @property
    def is_done(self) -> bool:
        return self._step_count >= TOTAL_STEPS

    @property
    def operating_context_mode(self) -> str:
        return self._context_mode

    @property
    def operating_context_live(self) -> bool:
        return self._context_live

    @property
    def topology_summary(self) -> Dict[str, Any]:
        return self._topology_summary

    @property
    def geo_context(self) -> Dict[str, Any]:
        return self._geo_context

    @property
    def twin_summary(self) -> Dict[str, Any]:
        return self._twin_summary

    @property
    def atlas_context(self) -> Dict[str, Any]:
        return self._atlas_context

    @property
    def control_entities(self) -> List[Dict[str, Any]]:
        return self._control_entities

    @property
    def twin_provenance(self) -> Dict[str, Any]:
        return self._twin_provenance

    @property
    def data_sources(self) -> Dict[str, Any]:
        return self._data_sources

    @property
    def enrichment_warnings(self) -> List[str]:
        return self._enrichment_warnings

    @property
    def grid_signal_spine(self) -> Dict[str, Any]:
        return self._grid_signal_spine


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)
