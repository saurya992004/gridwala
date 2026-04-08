"""
NEXUS GRID - Rule-Based Energy Agent
A deterministic controller used as the stable fallback when no trained
checkpoint exists for the active district.
"""

from typing import List, Optional


class RuleBasedAgent:
    """
    Deterministic energy management agent.

    Makes per-building charge and discharge decisions from current conditions.
    """

    SOLAR_HIGH_THRESHOLD = 1.5
    CARBON_HIGH_THRESHOLD = 0.44
    SOC_FULL_THRESHOLD = 0.90
    SOC_EMPTY_THRESHOLD = 0.15

    def decide(
        self,
        buildings: List[dict],
        carbon_intensity: float,
        forecast_scenario: Optional[str] = None,
        tariff_rate: Optional[float] = None,
        tariff_band: Optional[str] = None,
        weather_outlook: Optional[str] = None,
    ) -> List[float]:
        actions = []
        grid_is_dirty = carbon_intensity > self.CARBON_HIGH_THRESHOLD
        tariff_is_expensive = tariff_band == "high"
        tariff_is_cheap = tariff_band in {"low", "flat"}

        for building in buildings:
            solar = building["solar_generation"]
            soc = building["battery_soc"]
            is_ev_away = building.get("is_ev_away", False)

            if is_ev_away:
                action = 0.0
            elif forecast_scenario:
                if forecast_scenario in {"solar_offline", "heatwave", "carbon_spike"}:
                    action = 1.0 if soc < 1.0 else 0.0
                else:
                    action = 0.0
            elif tariff_is_expensive and soc > self.SOC_EMPTY_THRESHOLD:
                action = -0.9
            elif tariff_is_cheap and soc < self.SOC_FULL_THRESHOLD:
                action = 0.6
            elif solar > self.SOLAR_HIGH_THRESHOLD and soc < self.SOC_FULL_THRESHOLD:
                action = 0.8
            elif grid_is_dirty and soc > self.SOC_EMPTY_THRESHOLD:
                action = -0.7
            elif weather_outlook == "constrained" and soc < 0.75:
                action = 0.4
            else:
                action = 0.0

            actions.append(round(action, 4))

        return actions

    def explain(
        self,
        buildings: List[dict],
        carbon_intensity: float,
        actions: List[float],
        forecast_scenario: Optional[str] = None,
        tariff_rate: Optional[float] = None,
        tariff_band: Optional[str] = None,
        tariff_window: Optional[str] = None,
        weather_outlook: Optional[str] = None,
    ) -> List[str]:
        rationales = []

        for i, building in enumerate(buildings):
            solar = building["solar_generation"]
            soc = building["battery_soc"]
            is_ev_away = building.get("is_ev_away", False)
            building_type = building.get("type", "residential")
            action = actions[i]
            p2p_traded = abs(building.get("p2p_traded_kwh", 0.0))
            p2p_str = f" | P2P traded: {p2p_traded:.2f} kWh" if p2p_traded > 0 else ""

            if is_ev_away:
                reason = "Mobile asset (EV) is away driving and disconnected from the grid."
            elif forecast_scenario and action > 0.3:
                reason = (
                    f"PRE-COGNITION OVERRIDE: stockpiling energy ahead of {forecast_scenario}."
                )
            elif tariff_band == "high" and action < -0.3:
                reason = (
                    f"Tariff-led discharge. Utility price window is {tariff_window or 'high'}"
                    f" at {tariff_rate if tariff_rate is not None else 0.0:.3f}."
                    f" Releasing stored energy while prices are elevated{p2p_str}."
                )
            elif tariff_band in {"low", "flat"} and action > 0.3:
                reason = (
                    f"Tariff-led charging. Utility price window is {tariff_window or 'low'}"
                    f" at {tariff_rate if tariff_rate is not None else 0.0:.3f}."
                    f" Taking cheap energy now and preserving flexibility later."
                )
            elif action > 0.3:
                reason = (
                    f"Charging at {int(action * 100)}% rate. Solar output is {solar:.2f} kWh"
                    f"{p2p_str}. Battery at {int(soc * 100)}% capacity."
                )
            elif action < -0.3:
                source = "V2G EV" if building_type == "ev" else "Battery"
                reason = (
                    f"Discharging {source} at {int(abs(action) * 100)}% rate. "
                    f"Grid carbon is elevated at {carbon_intensity:.3f} kgCO2/kWh{p2p_str}."
                )
            else:
                reason = (
                    f"Idling. Solar: {solar:.2f} kWh. Grid carbon: {carbon_intensity:.3f} kgCO2/kWh. "
                    f"Battery SoC: {int(soc * 100)}%. Weather: {weather_outlook or 'steady'}{p2p_str}."
                )

            rationales.append(reason)

        return rationales
