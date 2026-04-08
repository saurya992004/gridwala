# NEXUS GRID Topology Foundation

## Phase

Phase 2A

## What This Adds

- optional `grid_topology` support in the schema
- automatic radial topology generation when a schema only provides buildings
- validation for:
  - buses
  - lines
  - feeders
  - slack bus connectivity
  - building to bus attachment
- lightweight topology summaries for API and runtime use

## New Schema Concepts

### `grid_topology`

Supports:

- `slack_bus`
- `buses`
- `lines`
- `feeders`

### `topology_summary`

Generated automatically and includes:

- topology type
- slack bus
- bus count
- line count
- feeder count
- asset attachment count
- max line capacity

## Current Behavior

If the user does not provide a topology:

- NEXUS GRID auto-generates a radial distribution layout
- each building is attached to an asset bus
- feeder heads are created automatically
- a substation slack bus is created automatically

If the user does provide a topology:

- it is validated
- disconnected buses are rejected
- duplicate ids are rejected
- invalid line references are rejected

## Runtime Status

Phase 2A currently gives the runtime:

- topology awareness
- topology summaries in websocket payloads
- a foundation for future feeder and line constraint simulation

It does not yet enforce:

- thermal line constraints
- voltage drops
- feeder congestion
- switching actions
- contingency propagation

Those are the next layers on top of this foundation.
