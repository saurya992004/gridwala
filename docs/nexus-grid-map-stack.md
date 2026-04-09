# NEXUS GRID Map Stack Decision

## CTO Decision

The chosen map and geo stack for NEXUS GRID is:

- **Open-Meteo Geocoding** for free place search
- **MapLibre** for frontend map rendering
- **PMTiles** for efficient packaged vector tile delivery
- **Overture** for map and place enrichment
- **Electricity Maps** for live grid signals

## Why This Stack

This stack keeps the product:

- more open
- less vendor-locked
- cheaper to operate during prototyping
- closer to our real product need

The core product problem is **not** consumer map UX.  
The real problem is:

- turning a place into a control-ready digital twin
- attaching live grid signals
- generating feeders, asset clusters, and RL control entities

Google Maps is strong for search and polish, but it does not solve the twin-generation problem.  
That is why it is **not** our default architecture.

## Role Of Each Piece

### Open-Meteo Geocoding

Use for:

- city search
- location resolution
- free geographic lookup without paid lock-in

### MapLibre

Use for:

- frontend map canvas
- topology overlays
- asset and feeder layers
- replay and scenario visualization

### PMTiles

Use for:

- portable tile packaging
- efficient local or edge-served basemaps
- controlled map rendering without relying on consumer map APIs

### Overture

Use for:

- richer place and built-environment data
- future map-native enrichment beyond our seeded catalog
- stronger city-twin inference over time

### Electricity Maps

Use for:

- carbon intensity
- electricity mix
- imports and exports
- live external grid context

Important:

- Electricity Maps is the **signal spine**
- it is **not** the full environment

## Product Principle

The right architecture is:

- **Map stack for geography**
- **Electricity Maps for live world-state**
- **NEXUS GRID for digital twin generation and control**

That is what keeps the project both credible and differentiated.

## What We Should Build Next

1. map-first launcher on top of the Phase 2B city twin flow
2. MapLibre scene with city marker, twin footprint, and feeder overlays
3. PMTiles-compatible map layer strategy
4. Overture-backed enrichment pipeline for better urban inference
