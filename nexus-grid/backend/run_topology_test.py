"""
NEXUS GRID - Topology Foundation Smoke Test
Run this to verify Phase 2A topology generation and validation.
Usage: python run_topology_test.py
"""

from pathlib import Path

from nexusgrid.core.schema_loader import load_from_dict, load_from_file


def run_topology_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Topology Foundation Smoke Test")
    print("=" * 60)

    print("\n[1/3] Loading preset topology...")
    preset = load_from_file(Path("nexusgrid/presets/residential_district.json"))
    preset_summary = preset["topology_summary"]
    assert preset_summary["n_buses"] >= len(preset["buildings"]) + 1
    assert preset_summary["n_feeders"] >= 1
    print(f"      [OK] Auto-generated topology type: {preset_summary['topology_type']}")
    print(
        f"      Buses: {preset_summary['n_buses']} | "
        f"Lines: {preset_summary['n_lines']} | Feeders: {preset_summary['n_feeders']}"
    )

    print("\n[2/3] Validating a custom user-supplied topology...")
    custom = load_from_dict(
        {
            "district_name": "Topology Validation Yard",
            "buildings": [
                {"name": "Node A", "type": "commercial", "battery_kwh": 20, "solar_peak_kw": 9, "bus_id": "load_a"},
                {"name": "Node B", "type": "residential", "battery_kwh": 12, "solar_peak_kw": 5, "bus_id": "load_b"},
            ],
            "grid_topology": {
                "slack_bus": "substation",
                "buses": [
                    {"id": "substation", "role": "slack", "voltage_kv": 11.0},
                    {"id": "feeder_1_bus", "role": "feeder_head", "voltage_kv": 0.415},
                    {"id": "load_a", "role": "load_bus", "voltage_kv": 0.415},
                    {"id": "load_b", "role": "load_bus", "voltage_kv": 0.415},
                ],
                "lines": [
                    {"id": "line_root", "from_bus": "substation", "to_bus": "feeder_1_bus", "capacity_kw": 240},
                    {"id": "line_a", "from_bus": "feeder_1_bus", "to_bus": "load_a", "capacity_kw": 80},
                    {"id": "line_b", "from_bus": "feeder_1_bus", "to_bus": "load_b", "capacity_kw": 60},
                ],
            },
        }
    )
    custom_summary = custom["topology_summary"]
    assert custom_summary["n_assets_attached"] == 2
    print(f"      [OK] Custom topology buses: {custom_summary['n_buses']}")

    print("\n[3/3] Confirming asset-to-bus attachments...")
    attachments = [building["bus_id"] for building in preset["buildings"]]
    assert all(attachments), "Each building should be attached to a bus."
    print(f"      [OK] Sample bus attachment: {attachments[0]}")

    print("\n[OK] Topology foundation is operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_topology_smoke_test()
