"""
NEXUS GRID - Geo Enrichment Smoke Test
Run this to verify Phase 1B enrichment for weather, carbon, and tariffs.
Usage: python run_geo_enrichment_test.py
"""

from nexusgrid.geo.service import geo_service


def run_geo_enrichment_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Geo Enrichment Smoke Test")
    print("=" * 60)

    print("\n[1/3] Resolving and enriching a U.K. location with deterministic providers...")
    enriched_location = geo_service.enrich_location(
        query="London",
        provider="catalog",
        weather_provider="heuristic",
        carbon_provider="profile",
        tariff_provider="heuristic",
    )
    assert enriched_location["enrichment"]["weather"]["provider"] == "heuristic"
    assert enriched_location["enrichment"]["carbon"]["provider"] == "profile"
    assert enriched_location["enrichment"]["tariff"]["provider"] == "heuristic"
    print("      [OK] Enrichment providers resolved correctly.")
    print(
        f"      Weather outlook: "
        f"{enriched_location['enrichment']['weather']['forecast']['outlook']}"
    )
    print(
        f"      Carbon intensity: "
        f"{enriched_location['enrichment']['carbon']['current_kg_per_kwh']} kgCO2/kWh"
    )

    print("\n[2/3] Generating an enriched schema...")
    generated = geo_service.generate_schema(
        query="New York City",
        provider="catalog",
        district_type="mixed_use",
        building_count=6,
        include_enrichment=True,
        weather_provider="heuristic",
        carbon_provider="profile",
        tariff_provider="heuristic",
    )
    schema = generated["schema"]
    assert "operating_context" in schema, "Expected operating_context in enriched schema."
    assert schema["generation_summary"]["enriched"] is True
    print(f"      [OK] District name: {schema['district_name']}")
    print(
        f"      Tariff window: "
        f"{schema['operating_context']['tariff']['current_window']}"
    )

    print("\n[3/3] Confirming provider metadata is available...")
    providers = geo_service.list_enrichment_providers()
    assert "weather" in providers and "carbon" in providers and "tariff" in providers
    print("      [OK] Enrichment provider catalog is available.")

    print("\n[OK] Geo enrichment foundation is operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_geo_enrichment_smoke_test()
