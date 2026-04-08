# NEXUS GRID Geo Foundation

## Phase

Phase 1A

## What This Adds

- world location resolution from:
  - free-form place names
  - raw coordinates like `19.0760,72.8777`
  - an offline-friendly seeded global catalog
- atlas-seed schema generation from a resolved location
- backend endpoints for geo providers, resolution, and schema generation
- validation-compatible schemas that still run on the current sandbox engine

## New Backend Endpoints

- `GET /api/geo/providers`
- `POST /api/geo/resolve`
- `POST /api/geo/schema`

## Current Providers

- `auto`
  - tries coordinates, then the local catalog, then Nominatim
- `coordinates`
  - zero external dependency
- `catalog`
  - seeded global cities for demos and offline testing
- `nominatim`
  - public OpenStreetMap geocoder

## Current Output

The generated schema is still a sandbox-compatible district schema, but it now includes:

- `geo_context`
- `data_sources`
- `generation_summary`
- location-aware district naming
- region-aware carbon-profile mapping
- latitude-aware solar scaling
- deterministic building synthesis

## No Paid APIs Needed Yet

This Phase 1A slice does not require any paid API keys.

You can already generate a district from:

- `London`
- `Mumbai`
- `Chennai`
- `Bengaluru`
- `40.7128,-74.0060`

## APIs Worth Adding Next

These are the highest-value external data sources for the next iteration:

- Electricity Maps
  - live carbon intensity
- Open-Meteo or NASA POWER
  - weather and solar irradiance
- OpenEI or utility-specific tariff feeds
  - dynamic tariff signals
- Overpass / OSM building footprints
  - real built-environment extraction instead of template synthesis

## What This Is Not Yet

This is not yet:

- a topology-aware feeder model
- a live utility integration
- a real tariff engine
- a real weather ingestion pipeline
- a graph-RL world model

It is the bridge that lets us stop hardcoding districts and start generating them from anywhere.
