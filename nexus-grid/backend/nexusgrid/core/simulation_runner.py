"""
NEXUS GRID - Simulation Runner
Owns the environment and controller lifecycle for a live session.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

from nexusgrid.core.agent import RuleBasedAgent
from nexusgrid.core.dqn_agent import DQNAgent
from nexusgrid.core.environment import NexusGridEnv
from nexusgrid.core.model_registry import resolve_model_id


class SimulationRunner:
    def __init__(self, schema: Optional[Dict[str, Any]] = None, preset_id: Optional[str] = None):
        self._paused = False
        self._speed = 2.0
        self._override_actions = None
        self._emergency = None
        self.rule_agent = RuleBasedAgent()
        self.model_id = "default-demo"
        self.controller_mode = "rule-based"
        self.engine_mode = "sandbox"
        self.engine_name = "nexus-sandbox-engine"
        self.engine_version = "1.0.0"
        self.env = NexusGridEnv(schema=schema)
        self.engine_mode = self.env.engine_mode
        self.engine_name = self.env.engine_name
        self.engine_version = self.env.engine_version
        self._configure_controller(schema=schema, preset_id=preset_id)

    def _configure_controller(self, schema: Optional[Dict[str, Any]], preset_id: Optional[str]):
        self.model_id = resolve_model_id(schema=schema, preset_id=preset_id)
        self.agent = DQNAgent(n_buildings=self.env.n_buildings)
        success = self.agent.load(model_id=self.model_id)
        self.controller_mode = "dqn" if success else "rule-based"

        if not success:
            print(
                f"[INFO] No trained DQN checkpoint for '{self.model_id}'. "
                "Falling back to rule-based control."
            )

    def update_schema(self, schema: Dict[str, Any], preset_id: Optional[str] = None):
        self.env = NexusGridEnv(schema=schema)
        self.engine_mode = self.env.engine_mode
        self.engine_name = self.env.engine_name
        self.engine_version = self.env.engine_version
        self._emergency = None
        self._configure_controller(schema=schema, preset_id=preset_id)
        self.env.reset()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def inject_emergency(self, scenario: str):
        self._emergency = scenario
        self.env.set_emergency(scenario)

    def clear_emergency(self):
        self._emergency = None
        self.env.clear_emergency()

    def inject_forecast(self, scenario: str, steps_ahead: int = 4):
        self.env.set_forecast(scenario, steps_ahead)

    async def run(self, speed: float = 1.0) -> AsyncGenerator[Dict[str, Any], None]:
        self.env.reset()
        delay = 1.0 / max(0.1, speed)

        while not self.env.is_done:
            while self._paused:
                await asyncio.sleep(0.2)

            last_payload = self.env.last_payload

            if last_payload:
                forecast_scenario = last_payload.get("forecast_scenario")
                if self.controller_mode == "dqn":
                    actions = self.agent.decide(
                        buildings=last_payload["buildings"],
                        carbon=last_payload["carbon_intensity"],
                        hour=last_payload.get("hour", 0),
                        forecast_scenario=forecast_scenario,
                    )
                    rationales = self.agent.explain(
                        buildings=last_payload["buildings"],
                        carbon=last_payload["carbon_intensity"],
                        actions=actions,
                        forecast_scenario=forecast_scenario,
                    )
                else:
                    actions = self.rule_agent.decide(
                        buildings=last_payload["buildings"],
                        carbon_intensity=last_payload["carbon_intensity"],
                        forecast_scenario=forecast_scenario,
                    )
                    rationales = self.rule_agent.explain(
                        buildings=last_payload["buildings"],
                        carbon_intensity=last_payload["carbon_intensity"],
                        actions=actions,
                        forecast_scenario=forecast_scenario,
                    )
            else:
                actions = None
                rationales = [
                    f"Initialising {self.controller_mode} controller..."
                    for _ in range(self.env.n_buildings)
                ]

            payload = self.env.step(actions)
            payload["rationales"] = rationales
            payload["emergency"] = self._emergency
            payload["controller_mode"] = self.controller_mode
            payload["model_id"] = self.model_id
            payload["engine_mode"] = self.engine_mode
            payload["engine_name"] = self.engine_name
            payload["engine_version"] = self.engine_version

            yield payload
            await asyncio.sleep(delay)
