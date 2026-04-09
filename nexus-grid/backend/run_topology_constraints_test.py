"""
NEXUS GRID - Phase 2C Topology Constraints Smoke Test
Run this to verify feeder stress, line derating, and outage events.
Usage: python run_topology_constraints_test.py
"""

from pathlib import Path

from nexusgrid.core.environment import NexusGridEnv
from nexusgrid.core.schema_loader import load_from_file


PRESET_PATH = Path(__file__).parent / "nexusgrid" / "presets" / "residential_district.json"


def run_topology_constraints_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Phase 2C Topology Constraints Smoke Test")
    print("=" * 60)

    schema = load_from_file(PRESET_PATH)

    print("\n[1/4] Checking baseline topology runtime...")
    env = NexusGridEnv(schema=schema)
    env.reset()
    baseline = env.step([0.0] * env.n_buildings)
    baseline_runtime = baseline["topology_runtime"]
    assert baseline_runtime["feeder_states"], "Expected feeder states in topology runtime."
    print(
        f"      [OK] Baseline stress index: {baseline_runtime['system_stress_index']} "
        f"across {len(baseline_runtime['feeder_states'])} feeders."
    )

    print("\n[2/4] Triggering line derating...")
    env = NexusGridEnv(schema=schema)
    env.reset()
    env.set_emergency("line_derating")
    derated = env.step([0.0] * env.n_buildings)
    derated_runtime = derated["topology_runtime"]
    assert derated_runtime["active_events"], "Expected an active line derating event."
    assert derated_runtime["overloaded_lines"] >= 1, "Expected overloaded or constrained lines after derating."
    print(
        f"      [OK] Event: {derated_runtime['active_events'][0]['label']} "
        f"| Overloaded lines: {derated_runtime['overloaded_lines']}"
    )

    print("\n[3/4] Triggering feeder fault...")
    env = NexusGridEnv(schema=schema)
    env.reset()
    env.set_emergency("feeder_fault")
    faulted = env.step([0.0] * env.n_buildings)
    faulted_runtime = faulted["topology_runtime"]
    assert faulted_runtime["constrained_feeders"] >= 1, "Expected at least one constrained feeder during a feeder fault."
    assert any(line["status"] == "outage" for line in faulted_runtime["line_states"]), "Expected an outage line state."
    print(
        f"      [OK] Constrained feeders: {faulted_runtime['constrained_feeders']} "
        f"| Active event: {faulted_runtime['active_events'][0]['target']}"
    )

    print("\n[4/4] Triggering congestion wave...")
    env = NexusGridEnv(schema=schema)
    env.reset()
    env.set_emergency("congestion_wave")
    congested = env.step([0.0] * env.n_buildings)
    congested_runtime = congested["topology_runtime"]
    assert congested_runtime["system_stress_index"] > baseline_runtime["system_stress_index"]
    assert congested_runtime["constrained_feeders"] >= 1, "Expected constrained feeders during congestion wave."
    print(
        f"      [OK] Stress index rose to {congested_runtime['system_stress_index']} "
        f"with {congested_runtime['constrained_feeders']} constrained feeders."
    )

    print("\n[OK] Phase 2C topology constraints are operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_topology_constraints_smoke_test()
