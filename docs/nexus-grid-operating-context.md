# NEXUS GRID Operating Context

## Phase

Phase 1C

## What This Changes

Phase 1A generated a location-aware twin.

Phase 1B attached weather, carbon, and tariff enrichment to that twin.

Phase 1C makes the simulator actually use that operating context during runtime.

## Runtime Effects

The sandbox engine now uses enriched context to influence:

- solar output
- district load
- carbon intensity
- utility tariff signals
- grid import and export pricing
- controller decisions

## What The Runtime Emits

WebSocket step payloads now include:

- `grid_tariff_rate`
- `grid_tariff_currency`
- `grid_tariff_window`
- `grid_tariff_band`
- `ambient_temperature_c`
- `solar_capacity_factor`
- `weather_outlook`
- `operating_context_mode`
- `operating_context_live`

## Controller Behavior

### Rule-based controller

The fallback controller now reacts to:

- expensive tariff windows
- cheap tariff windows
- constrained weather outlook
- dirty carbon periods

### DQN controller

The DQN remains checkpoint-compatible, but it now applies a lightweight
runtime arbitration layer on top of the raw network action.

That means:

- old checkpoints still load
- tariff and weather context can still shape runtime actions
- the project behaves more like a hybrid controller, not a blind static DQN

## Preset Behavior

The built-in presets now auto-attach runtime geo enrichment:

- `Residential District` -> London
- `University Campus` -> Boston
- `Industrial Microgrid` -> Mumbai

So the default app experience benefits from live or enriched context automatically.

## Honest Limitation

This is still a sandbox engine.

Phase 1C makes the runtime materially context-aware, but it is not yet:

- a topology-aware feeder simulator
- a full weather-forecast time series engine
- a real utility dispatch stack
- a graph-native RL environment

It is the point where NEXUS GRID stops being just a pretty geo twin and starts behaving like a live operating twin.
