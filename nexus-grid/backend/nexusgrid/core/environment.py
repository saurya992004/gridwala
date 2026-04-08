"""
NEXUS GRID - Sandbox Grid Environment Engine v1.0
Custom multi-building energy simulation core used for the current sandbox mode.
"""

import math
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
                actual_charge = 0.0
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
        reward = round(-abs(net) * 0.7 + (0.5 - abs(soc_ratio - 0.5)) * 0.3, 4)

        return {
            "id": self.id,
            "type": self.type,
            "is_ev_away": self._ev_away if self.is_ev else False,
            "net_electricity_consumption": net,
            "solar_generation": round(solar, 4),
            "battery_soc": round(self.battery_soc / self.BATTERY_CAPACITY, 4),
            "reward": reward,
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
        self._district_name = cfg.get("district_name", "NEXUS District")
        self._carbon_profile = get_profile(cfg.get("carbon_profile", "uk_national_grid"))
        self._buildings = [Building(i, building_cfg) for i, building_cfg in enumerate(cfg["buildings"])]
        self._step_count = 0
        self._rng = np.random.default_rng(seed=42)
        self._last_payload: Optional[Dict[str, Any]] = None

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

        hour = self._step_count % HOURS_PER_DAY
        day = (self._step_count // HOURS_PER_DAY) % DAYS_PER_YEAR
        buildings_data = []

        for i, building in enumerate(self._buildings):
            action = float(actions[i]) if i < len(actions) else 0.0
            data = building.step(
                hour,
                day,
                action,
                solar_mult=self._solar_mult,
                load_mult=self._load_mult,
            )
            buildings_data.append(data)

        grid_buy_price = 0.15
        grid_sell_price = 0.05
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
            p2p_price = 0.10
        else:
            supply_ratio = total_surplus / (total_surplus + total_shortage)
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

        noise = float(self._rng.normal(0, 0.01))
        carbon = round((self._carbon_profile[hour] + noise) * self._carbon_mult, 4)
        district_net = round(sum(b["net_electricity_consumption"] for b in buildings_data), 4)

        payload = {
            "step": self._step_count,
            "hour": hour,
            "day": day,
            "done": self._step_count >= TOTAL_STEPS,
            "buildings": buildings_data,
            "carbon_intensity": carbon,
            "district_net_consumption": district_net,
            "p2p_volume_kwh": round(p2p_pool, 4),
            "p2p_clearing_price": p2p_price,
            "forecast_scenario": self._forecast_scenario,
            "forecast_steps_left": self._forecast_steps_left,
        }
        self._last_payload = payload
        return payload

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
