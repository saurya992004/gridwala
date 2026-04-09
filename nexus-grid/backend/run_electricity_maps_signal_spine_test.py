"""
NEXUS GRID - Electricity Maps Signal Spine Smoke Test
Run this to verify the v4 Electricity Maps signal spine parsing logic.
Usage: python run_electricity_maps_signal_spine_test.py
"""

from __future__ import annotations

import os

import nexusgrid.geo.enrichment as enrichment_module
from nexusgrid.geo.enrichment import ElectricityMapsCarbonProvider


def run_electricity_maps_signal_spine_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Electricity Maps Signal Spine Smoke Test")
    print("=" * 60)

    original_fetch = enrichment_module._electricity_maps_latest
    original_key = os.environ.get("NEXUS_ELECTRICITYMAPS_API_KEY")

    sample_payloads = {
        "carbon-intensity/latest": {
            "zone": "GB",
            "carbonIntensity": 118,
            "datetime": "2026-04-09T15:00:00.000Z",
            "updatedAt": "2026-04-09T14:24:20.488Z",
            "isEstimated": True,
            "estimationMethod": "TIME_SLICER_AVERAGE",
        },
        "renewable-energy/latest": {
            "zone": "GB",
            "value": 62,
            "unit": "%",
        },
        "total-load/latest": {
            "zone": "GB",
            "value": 32603.15,
            "unit": "MW",
        },
        "electricity-flows/latest": {
            "zone": "GB",
            "unit": "MW",
            "data": [
                {
                    "import": {
                        "IE": 428,
                        "NL": 117,
                        "GB-NIR": 103,
                        "NO-NO2": 1549,
                    },
                    "export": {
                        "BE": 609,
                        "FR": 2510,
                        "IM": 31,
                        "DK-DK1": 563,
                    },
                }
            ],
        },
        "price-day-ahead/latest": {
            "zone": "GB",
            "value": 69.8,
            "unit": "GBP/MWh",
            "source": "nordpool.com",
        },
    }

    def fake_latest(path: str, location: dict, api_key: str):
        return sample_payloads[path]

    try:
        os.environ["NEXUS_ELECTRICITYMAPS_API_KEY"] = "test-token"
        enrichment_module._electricity_maps_latest = fake_latest

        provider = ElectricityMapsCarbonProvider()
        enrichment = provider.enrich(
            location={"latitude": 51.5072, "longitude": -0.1276},
            schema={"carbon_profile": "uk_national_grid"},
        )
        signal_spine = enrichment["signal_spine"]

        assert enrichment["provider"] == "electricity_maps"
        assert enrichment["provider_mode"] == "live"
        assert signal_spine["zone"] == "GB"
        assert signal_spine["renewable_share_pct"] == 62.0
        assert signal_spine["total_load_mw"] == 32603.15
        assert signal_spine["net_interchange_mw"] == -1516.0
        assert signal_spine["interchange_state"] == "net_exporting"
        assert signal_spine["day_ahead_price"] == 69.8

        print("      [OK] Parsed carbon, renewable, load, flows, and price signals.")
        print(
            f"      Zone: {signal_spine['zone']} | Renewable share: "
            f"{signal_spine['renewable_share_pct']}% | System load: {signal_spine['total_load_mw']} MW"
        )
        print(f"      Net interchange: {signal_spine['net_interchange_mw']} MW")
        print(f"      Day-ahead price: {signal_spine['day_ahead_price']} {signal_spine['day_ahead_price_unit']}")
        print("\n[OK] Electricity Maps v4 signal spine parsing is operational.")
        print("=" * 60)
    finally:
        enrichment_module._electricity_maps_latest = original_fetch
        if original_key is None:
            os.environ.pop("NEXUS_ELECTRICITYMAPS_API_KEY", None)
        else:
            os.environ["NEXUS_ELECTRICITYMAPS_API_KEY"] = original_key


if __name__ == "__main__":
    run_electricity_maps_signal_spine_smoke_test()
