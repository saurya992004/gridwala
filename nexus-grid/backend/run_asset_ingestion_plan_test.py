"""
NEXUS GRID - Asset Ingestion Architecture Smoke Test
Run this to verify the future radius-ingestion planning contract.
Usage: python run_asset_ingestion_plan_test.py
"""

from nexusgrid.geo.service import geo_service


def main() -> None:
    print("NEXUS GRID - Asset Ingestion Architecture Smoke Test")

    print("\n[1/2] Generating a city twin with architecture metadata...")
    generated = geo_service.generate_schema(
        query="London",
        provider="catalog",
        district_type="mixed_use",
        building_count=8,
        include_enrichment=False,
    )
    plan = generated["schema"].get("asset_ingestion_plan", {})
    assert plan.get("radius_km") == 50, "Expected the default asset-ingestion radius to be 50 km."
    assert "generation_assets" in plan.get("normalized_layers", []), "Expected generation assets in normalized layers."
    print("      [OK] Schema carries future radius-ingestion plan metadata.")

    print("\n[2/2] Listing the future provider stack...")
    providers = geo_service.list_asset_ingestion_providers()
    provider_ids = {provider["id"] for provider in providers}
    assert "overture" in provider_ids and "osm_overpass" in provider_ids
    print("      [OK] Asset-ingestion provider architecture is exposed.")

    print("\nAll asset-ingestion architecture checks passed.")


if __name__ == "__main__":
    main()
