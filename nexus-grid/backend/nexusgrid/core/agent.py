"""
NEXUS GRID — Rule-Based Energy Agent
A deterministic smart agent that optimises battery charge/discharge
based on solar availability and grid carbon intensity.

Logic:
  - If solar is high AND battery not full  → charge battery
  - If carbon is high AND battery has charge → discharge battery
  - Otherwise → idle (0.0)

This gives us a working "AI agent" without needing to train an RL model.
In Phase 4 we will add the SHAP explainability layer on top of this.
"""

from typing import List, Optional


class RuleBasedAgent:
    """
    Deterministic energy management agent.

    Makes per-building charge/discharge decisions each step
    based on current conditions.
    """

    # Thresholds
    SOLAR_HIGH_THRESHOLD = 1.5      # kWh — above this: good solar window
    CARBON_HIGH_THRESHOLD = 0.44    # kgCO2/kWh — above this: grid is dirty
    SOC_FULL_THRESHOLD = 0.90       # 90% — treat as "full"
    SOC_EMPTY_THRESHOLD = 0.15      # 15% — treat as "empty"

    def decide(
        self,
        buildings: List[dict],
        carbon_intensity: float,
        forecast_scenario: Optional[str] = None,
    ) -> List[float]:
        """
        Compute one action per building.

        Args:
            buildings: List of building state dicts from env.step()
            carbon_intensity: Current grid carbon intensity (kgCO2/kWh)
            forecast_scenario: Optional string of an incoming emergency.

        Returns:
            List of actions in [-1.0, 1.0] — one per building.
            Positive = charge, Negative = discharge.
        """
        actions = []
        grid_is_dirty = carbon_intensity > self.CARBON_HIGH_THRESHOLD

        for b in buildings:
            solar = b["solar_generation"]
            soc = b["battery_soc"]  # Already normalised 0-1
            is_ev_away = b.get("is_ev_away", False)

            if is_ev_away:
                action = 0.0
                reason = "EV away driving — disconnected"

            elif forecast_scenario:
                # PRE-COGNITION OVERRIDE: 
                # If there's an emergency coming, we must lock the batteries into a state of readiness.
                if forecast_scenario == "solar_offline" or forecast_scenario == "heatwave":
                    # We need maximum power later! Charge immediately at 100% capacity from the grid!
                    action = 1.0 if soc < 1.0 else 0.0
                    reason = f"PRE-COGNITION: Stockpiling energy for {forecast_scenario}"
                elif forecast_scenario == "carbon_spike":
                    # Carbon spike means energy will be dirty and expensive. Stockpile now while it's normal.
                    action = 1.0 if soc < 1.0 else 0.0
                    reason = f"PRE-COGNITION: Hedging against {forecast_scenario}"
                else:
                    action = 0.0
                    reason = "Pre-Cognition idle"
                
            elif solar > self.SOLAR_HIGH_THRESHOLD and soc < self.SOC_FULL_THRESHOLD:
                # Sun is shining and battery has room → charge hard
                action = 0.8
                reason = "Solar surplus — charging battery"

            elif grid_is_dirty and soc > self.SOC_EMPTY_THRESHOLD:
                # Grid carbon is high → use stored clean energy (or V2G)
                action = -0.7
                reason = "Grid carbon spike — discharging battery/EV"

            elif soc > self.SOC_FULL_THRESHOLD:
                # Battery is almost full regardless of solar → slow charge or idle
                action = 0.0
                reason = "Battery full — idling"

            else:
                # No clear signal → idle
                action = 0.0
                reason = "No clear signal — idling"

            actions.append(round(action, 4))

        return actions

    def explain(
        self,
        buildings: List[dict],
        carbon_intensity: float,
        actions: List[float],
        forecast_scenario: Optional[str] = None,
    ) -> List[str]:
        """
        Generate plain-English rationale for each building's action.
        Used by the XAI sidebar in the frontend.
        """
        grid_is_dirty = carbon_intensity > self.CARBON_HIGH_THRESHOLD
        rationales = []

        for i, b in enumerate(buildings):
            solar = b["solar_generation"]
            soc = b["battery_soc"]
            is_ev_away = b.get("is_ev_away", False)
            b_type = b.get("type", "residential")
            
            action = actions[i]
            
            # Additional P2P stats if available from the previous step simulation
            p2p_traded = abs(b.get("p2p_traded_kwh", 0))
            p2p_str = f" | P2P Traded: {p2p_traded} kWh" if p2p_traded > 0 else ""

            if is_ev_away:
                reason = "Mobile asset (EV) is currently away driving. Disconnected from grid."
            elif forecast_scenario and action > 0.3:
                reason = f"🚨 PRE-COGNITION OVERRIDE: Stockpiling energy from grid array for impending {forecast_scenario}."
            elif action > 0.3:
                reason = (
                    f"Charging at {int(action*100)}% rate. "
                    f"Solar output is {solar:.2f} kWh{p2p_str}. "
                    f"Battery at {int(soc*100)}% capacity."
                )
            elif action < -0.3:
                src = "V2G EV" if b_type == "ev" else "Battery"
                reason = (
                    f"Discharging {src} at {int(abs(action)*100)}% rate. "
                    f"Grid carbon spiking ({carbon_intensity:.3f} kgCO₂/kWh){p2p_str}."
                )
            else:
                reason = (
                    f"Idling. Solar: {solar:.2f} kWh. "
                    f"Grid carbon: {carbon_intensity:.3f} kgCO₂/kWh. "
                    f"Battery SoC: {int(soc*100)}%{p2p_str}."
                )

            rationales.append(reason)

        return rationales
