# NEXUS GRID Asset Ingestion Architecture

## CTO Stance

The correct architecture is:

- show many assets in the twin
- control only meaningful aggregated entities
- keep provider-specific geo ingestion outside the simulator core

The wrong architecture is:

- making every generator, charger, and line endpoint a separate RL agent
- binding the simulator directly to one geo provider

## Architecture Decision

We are introducing a dedicated asset-ingestion planning layer before implementing full radius-based harvesting.

This means:

- `Electricity Maps` remains the live signal spine
- `GeoTwinBuilder` keeps generating the twin shell
- future radius-based asset discovery will flow through a normalized `asset_ingestion_plan`
- the simulator and controller stack will consume a provider-agnostic asset graph later

## Planned Provider Stack

The current preferred order is:

1. `Overture Maps`
2. country or utility open power datasets when available
3. `OSM / Overpass` as fallback enrichment
4. manual upload for utility shapefiles or CSV overrides

## Normalized Layers

Future radius ingestion should normalize these layers:

- substations
- feeders
- lines
- generation assets
- storage assets
- EV charging assets
- demand clusters
- critical loads

## Agentization Rule

Important assets in the selected radius should appear in the twin, but only control-relevant groups should become agents.

Target agent classes:

- feeder coordinators
- storage fleet dispatch
- EV fleet dispatch
- industrial cluster dispatch
- campus or microgrid dispatch

## Why This Matters

This keeps the project realistic:

- the map can get denser and more truthful
- the RL problem stays tractable
- provider changes do not force simulator rewrites

## Next Practical Use

This architecture should be used as the contract for the later phase that expands city twins into 50 km radius asset graphs.
