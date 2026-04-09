"""
NEXUS GRID - Phase 2B City Twin Smoke Test
Run this to verify featured locations, generated control entities, and twin provenance.
Usage: python run_city_twin_test.py
"""

from nexusgrid.geo.service import geo_service


def run_city_twin_smoke_test():
    print("=" * 60)
    print("  NEXUS GRID - Phase 2B City Twin Smoke Test")
    print("=" * 60)

    print("\n[1/3] Loading featured atlas cities...")
    featured = geo_service.list_featured_locations(limit=5)
    assert featured, "Expected featured locations for the city launcher."
    print(f"      [OK] Featured city: {featured[0]['location']['display_name']}")

    print("\n[2/3] Generating a city twin with deterministic enrichment...")
    generated = geo_service.generate_schema(
        query="Singapore",
        provider="catalog",
        district_type="auto",
        building_count=8,
        include_enrichment=True,
        weather_provider="heuristic",
        carbon_provider="profile",
        tariff_provider="heuristic",
    )
    schema = generated["schema"]
    control_entities = schema.get("control_entities", [])
    twin_summary = schema.get("twin_summary", {})
    twin_provenance = schema.get("twin_provenance", {})

    assert control_entities, "Expected generated control entities."
    assert twin_summary.get("n_control_entities", 0) == len(control_entities)
    assert twin_provenance.get("live_signal_spine", {}).get("carbon") == "profile"
    print(f"      [OK] District twin: {schema['district_name']}")
    print(f"      Control entities: {len(control_entities)}")
    print(f"      Dominant asset type: {twin_summary.get('dominant_asset_type')}")

    print("\n[3/3] Confirming control entities are agent-ready...")
    first_entity = control_entities[0]
    assert first_entity.get("agent_class"), "Expected agent_class on control entities."
    assert first_entity.get("member_buildings"), "Expected clustered members on control entities."
    print(f"      [OK] First control entity: {first_entity['label']}")
    print(f"      Agent class: {first_entity['agent_class']}")

    print("\n[OK] Phase 2B city-to-twin foundation is operational.")
    print("=" * 60)


if __name__ == "__main__":
    run_city_twin_smoke_test()
