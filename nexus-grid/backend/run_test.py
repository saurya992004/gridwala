"""
NEXUS GRID - Phase 1 Smoke Test
Run this to verify the simulation engine is working correctly.
Usage: python run_test.py
"""

from nexusgrid.core.environment import NexusGridEnv


def run_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Engine Smoke Test")
    print("=" * 60)

    print("\n[1/4] Initialising NexusGridEnv...")
    env = NexusGridEnv()
    print("      [OK] Environment ready.")
    print(f"      Buildings detected: {env.building_names}")
    print(f"      Max simulation steps: {env.max_steps}")

    print("\n[2/4] Resetting environment...")
    observations = env.reset()
    print(f"      [OK] Reset successful. Got {len(observations)} building observation sets.")

    print("\n[3/4] Running 5 simulation steps (do-nothing policy)...")
    for _ in range(5):
        payload = env.step()
        print(f"\n  --- Step {payload['step']} ---")
        print(f"  Carbon Intensity  : {payload['carbon_intensity']} kgCO2/kWh")
        print(f"  District Net Load : {payload['district_net_consumption']} kWh")
        for building in payload["buildings"]:
            print(
                f"  [{building['id']}] Solar={building['solar_generation']} kWh | "
                f"Battery SoC={building['battery_soc']} | "
                f"Net={building['net_electricity_consumption']} kWh | "
                f"Reward={building['reward']}"
            )

    print("\n[4/4] All checks passed!")
    print("      [OK] NEXUS GRID Engine is operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
