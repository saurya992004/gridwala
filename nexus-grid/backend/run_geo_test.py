"""
NEXUS GRID - Geo Foundation Smoke Test
Run this to verify Phase 1A geo resolution and atlas-seed schema generation.
Usage: python run_geo_test.py
"""

from nexusgrid.geo.service import geo_service


def run_geo_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Geo Foundation Smoke Test")
    print("=" * 60)

    print("\n[1/3] Resolving catalog-backed city...")
    resolved_city = geo_service.resolve("Mumbai", provider="catalog", limit=3)
    assert resolved_city["candidates"], "Expected at least one catalog candidate for Mumbai."
    top_city = resolved_city["candidates"][0]
    print(f"      [OK] Top candidate: {top_city['display_name']}")
    print(f"      Provider used: {resolved_city['provider']}")

    print("\n[2/3] Resolving raw coordinates...")
    resolved_coordinates = geo_service.resolve("19.0760,72.8777", provider="auto", limit=1)
    assert resolved_coordinates["candidates"], "Expected coordinate input to resolve."
    top_coordinate = resolved_coordinates["candidates"][0]
    print(f"      [OK] Coordinate candidate: {top_coordinate['display_name']}")
    print(f"      Provider used: {resolved_coordinates['provider']}")

    print("\n[3/3] Generating atlas-seed schema...")
    generated = geo_service.generate_schema(
        query="Chennai",
        provider="catalog",
        district_type="auto",
        building_count=7,
        include_enrichment=True,
        weather_provider="heuristic",
        carbon_provider="profile",
        tariff_provider="heuristic",
    )
    schema = generated["schema"]
    print(f"      [OK] District name: {schema['district_name']}")
    print(f"      Carbon profile: {schema['carbon_profile']}")
    print(f"      Buildings generated: {len(schema['buildings'])}")

    print("\n[OK] Geo foundation is operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_geo_smoke_test()
