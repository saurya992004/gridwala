# NEXUS GRID Phase 2B: City-To-Twin Slice

## What This Slice Adds

This phase turns NEXUS GRID from a preset-only simulator into the first version of a **city launcher**.

The current product direction is:

- **Electricity Maps = live signal spine**
- **NEXUS GRID = generated control-ready digital twin**

That means the project does **not** treat Electricity Maps as the full environment. Instead, it uses external live signals such as carbon intensity while generating its own:

- feeder-aware topology seed
- asset mix
- control entities
- provenance trail

## Implemented In This Slice

### Backend

- featured city discovery for the atlas launcher
- generated `control_entities` attached to city twins
- generated `twin_summary`, `atlas_context`, and `twin_provenance`
- connected and step payloads now carry city-twin metadata
- smoke test: [nexus-grid/backend/run_city_twin_test.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\run_city_twin_test.py)

### Frontend

- city launcher panel to build and load a city twin live
- control-entity theater in the main twin view
- provenance panel in the right rail
- websocket hook can fetch a generated city twin and inject it into the live simulator
- loaded city twins persist across reconnects

## Current Limitations

- the launcher is **city-first**, not yet full map-first
- topology is still seeded radial topology, not map-extracted distribution geometry
- control entities are inferred from feeder and asset clustering, not learned from real utility asset registries
- Electricity Maps is still running on a sandbox key until production approval lands

## Next Best Move

Phase 2C should now focus on:

1. feeder limits and congestion
2. outage and maintenance events
3. city map overlays and topology visualization
4. agent decisions tied to feeder stress, not just district-wide signals
