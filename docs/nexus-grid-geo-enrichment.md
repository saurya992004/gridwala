# NEXUS GRID Geo Enrichment

## Phase

Phase 1B

## What This Adds

- weather enrichment
- carbon-intensity enrichment
- tariff-context enrichment
- enriched geo schema generation with operational context

## New Endpoints

- `POST /api/geo/enrich`
- `POST /api/geo/schema`
  - now supports enrichment controls

## Request Controls

`/api/geo/schema` now accepts:

- `include_enrichment`
- `weather_provider`
- `carbon_provider`
- `tariff_provider`

## Provider Strategy

### Weather

- `auto`
  - tries Open-Meteo, then falls back to heuristics
- `open_meteo`
  - live weather and solar context
- `heuristic`
  - offline fallback

### Carbon

- `auto`
  - tries Electricity Maps, then falls back to mapped sandbox profiles
- `electricity_maps`
  - live carbon by geolocation
- `profile`
  - static sandbox-compatible profile mapping

### Tariffs

- `auto`
  - tries OpenEI for U.S. locations, then falls back to regional heuristics
- `openei`
  - live utility-rate lookup
- `heuristic`
  - country-aware tariff fallback

## Environment Variables

Optional live-provider keys:

- `NEXUS_ELECTRICITYMAPS_API_KEY`
- `NEXUS_OPENEI_API_KEY`

Optional networking controls:

- `NEXUS_GEO_TIMEOUT_SECONDS`
- `NEXUS_OPEN_METEO_BASE_URL`
- `NEXUS_ELECTRICITY_MAPS_BASE_URL`
- `NEXUS_OPENEI_BASE_URL`

## What Lands In The Schema

Enriched schemas now include:

- `operating_context.weather`
- `operating_context.carbon`
- `operating_context.tariff`
- `generation_summary.enriched`
- `data_sources.weather_live`
- `data_sources.carbon_live`
- `data_sources.tariffs_live`

## Honest Limitation

The sandbox simulator still uses the static `carbon_profile` for runtime simulation.

Phase 1B adds real operational context to the generated twin, but it does not yet make the simulator fully weather-driven, tariff-driven, or live-carbon-driven.

That comes next when we wire this context into the simulation engine and controller stack.
