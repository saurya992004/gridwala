"""
NEXUS GRID - Operating Context Smoke Test
Run this to verify that enriched weather, carbon, and tariff context
drives the runtime simulation loop.
Usage: python run_operating_context_test.py
"""

from __future__ import annotations

import asyncio

from nexusgrid.core.simulation_runner import SimulationRunner
from nexusgrid.geo.service import geo_service


async def _collect_first_payload():
    generated = geo_service.generate_schema(
        query="London",
        provider="catalog",
        district_type="auto",
        building_count=6,
        include_enrichment=True,
        weather_provider="heuristic",
        carbon_provider="profile",
        tariff_provider="heuristic",
    )
    runner = SimulationRunner(schema=generated["schema"])
    stream = runner.run(speed=100.0)
    await anext(stream)
    first = await anext(stream)
    await stream.aclose()
    return first


def run_operating_context_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Operating Context Smoke Test")
    print("=" * 60)

    payload = asyncio.run(_collect_first_payload())

    print("\n[1/3] Checking runtime context fields...")
    assert payload["operating_context_mode"] in {"enriched", "live_enriched"}
    assert "grid_tariff_rate" in payload
    assert "ambient_temperature_c" in payload
    assert "weather_outlook" in payload
    print(f"      [OK] Context mode: {payload['operating_context_mode']}")
    print(f"      Tariff: {payload['grid_tariff_rate']} {payload['grid_tariff_currency']}/kWh")

    print("\n[2/3] Checking controller loop output...")
    assert payload["rationales"], "Expected controller rationales in runner payload."
    assert payload["controller_mode"] in {"dqn", "rule-based"}
    print(f"      [OK] Controller mode: {payload['controller_mode']}")
    print(f"      Sample rationale: {payload['rationales'][0]}")

    print("\n[3/3] Checking live runtime metrics...")
    assert payload["carbon_intensity"] > 0
    assert payload["district_net_consumption"] != 0
    print(f"      [OK] Carbon intensity: {payload['carbon_intensity']:.3f}")
    print(f"      Weather outlook: {payload['weather_outlook']}")

    print("\n[OK] Operating context is driving the runtime.")
    print("=" * 60)


if __name__ == "__main__":
    run_operating_context_smoke_test()
