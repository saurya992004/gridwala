"""
NEXUS GRID — Simulation Runner
Manages the lifecycle of a running simulation session.

Each WebSocket connection gets its own SimulationRunner instance.
The runner owns the environment + agent and drives the step loop.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

from nexusgrid.core.environment import NexusGridEnv
from nexusgrid.core.dqn_agent import DQNAgent


class SimulationRunner:
    """
    Drives one full simulation session.

    Usage:
        runner = SimulationRunner(schema=validated_schema_dict)
        async for payload in runner.run(speed=2.0):
            await websocket.send_json(payload)
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.env = NexusGridEnv(schema=schema)
        
        # Initialise and load actual neural network weights for inference
        self.agent = DQNAgent(n_buildings=self.env.n_buildings)
        success = self.agent.load()
        if not success:
            print("[WARNING] Could not load DQN weights. Agent will act randomly during presentation.")

        self._paused = False
        self._speed = 2.0             # steps per second (adjustable via control msg)
        self._override_actions = None
        self._emergency = None

    # ------------------------------------------------------------------
    # Control methods (called from WebSocket message handler)
    # ------------------------------------------------------------------

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def inject_emergency(self, scenario: str):
        """
        Inject a Grid Emergency scenario.
        Scenarios:
          - "solar_offline"  : zero out solar for 12 steps
          - "carbon_spike"   : double carbon intensity for 6 steps
          - "heatwave"       : 2x building load for 8 steps
        """
        self._emergency = scenario
        self.env.set_emergency(scenario)

    def clear_emergency(self):
        self._emergency = None
        self.env.clear_emergency()

    def inject_forecast(self, scenario: str, steps_ahead: int = 4):
        """Inject a prediction of an incoming emergency"""
        self.env.set_forecast(scenario, steps_ahead)

    # ------------------------------------------------------------------
    # Main async generator
    # ------------------------------------------------------------------

    async def run(self, speed: float = 1.0) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields one payload dict per simulation step.

        Args:
            speed: Steps per second (1.0 = real-time, 5.0 = 5x speed)
        """
        self.env.reset()
        delay = 1.0 / max(0.1, speed)

        while not self.env.is_done:
            # Honour pause
            while self._paused:
                await asyncio.sleep(0.2)

            # Get current building states (from last step, or initial)
            last_payload = self.env.last_payload

            # Agent decides actions
            if last_payload:
                f_scenario = last_payload.get("forecast_scenario")
                actions = self.agent.decide(
                    buildings=last_payload["buildings"],
                    carbon=last_payload["carbon_intensity"],
                    hour=last_payload.get("hour", 0),
                    forecast_scenario=f_scenario,
                )
                rationales = self.agent.explain(
                    buildings=last_payload["buildings"],
                    carbon=last_payload["carbon_intensity"],
                    actions=actions,
                    forecast_scenario=f_scenario,
                )
            else:
                actions = None
                rationales = ["Initialising..." for _ in range(self.env.n_buildings)]

            # Step environment
            payload = self.env.step(actions)
            payload["rationales"] = rationales
            payload["emergency"] = self._emergency

            yield payload
            await asyncio.sleep(delay)
