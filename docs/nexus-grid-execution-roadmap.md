# NEXUS GRID Execution Roadmap

## Restart Handoff

If you restart Codex later, use this exact prompt:

`Continue NEXUS GRID from docs/nexus-grid-execution-roadmap.md. First inspect git status and preserve the validated uncommitted frontend stability fixes, asset-ingestion architecture work, and topology-aware control-loop changes. Then continue from the next recommended phase without redoing completed work.`

## Product Position

NEXUS GRID is being built as a three-layer system:

1. **Layer 1: Twin Foundation and World Ingestion**
2. **Layer 2: Grid Runtime and Intelligence**
3. **Layer 3: Operator Control Room and Deployability**

Core stance:

- **Electricity Maps is the live signal spine**
- **NEXUS GRID is the digital-twin generator and control layer**
- **RL should act on feeder- and cluster-level control entities, not every raw asset marker**

## Current Executive Summary

What is already true now:

- the sandbox engine is stabilized and honest about fallback behavior
- the platform can resolve places or coordinates into generated city twins
- weather, tariff, and carbon enrichment are wired into the runtime
- Electricity Maps is integrated as the live `v4` regional signal spine
- the schema now supports buses, lines, feeders, control entities, and provenance
- the frontend is now a sparse map-first control room instead of a card dump
- topology stress, congestion, outages, and feeder-fault drills exist in the runtime
- controller behavior now starts responding to topology stress instead of only visualizing it
- a future-ready asset-ingestion architecture exists for later `50 km` expansion

## Layer 1: Twin Foundation and World Ingestion

### Phase 0: Core Stabilization

Goal:

- stabilize the sandbox engine
- make controller fallback honest
- clean up training and model loading

Status:

- **complete**

Delivered:

- model registry
- preset-aware checkpoint loading
- rule-based fallback
- clearer engine labeling

### Phase 1A: Geo Resolution

Goal:

- resolve city names and coordinates into valid location candidates

Status:

- **complete**

Delivered:

- `LocationResolver`
- catalog-backed and coordinate-backed resolution
- backend geo provider endpoints

### Phase 1B: Live Enrichment

Goal:

- enrich generated twins with weather, carbon, and tariff context

Status:

- **complete**

Delivered:

- Open-Meteo weather integration
- OpenEI tariff integration
- Electricity Maps enrichment integration
- provider fallback logic

### Phase 1C: Runtime Operating Context

Goal:

- make enrichment actually affect the live simulation

Status:

- **complete**

Delivered:

- live weather and tariff context in runtime behavior
- enriched carbon/tariff/weather signals exposed in payloads
- dashboard telemetry support

### Phase 1D: Open Geo Stack and City Launcher Foundation

Goal:

- move from manual district presets toward map-native city selection

Status:

- **complete for foundation**

Delivered:

- Open-Meteo geocoding direction
- MapLibre / PMTiles / Overture stack decision
- city-to-twin launcher shell
- generated provenance and control-entity metadata

Still missing:

- real asset harvesting inside a configurable radius
- dense map-derived twin population

### Phase 1E: Asset-Ingestion Architecture Contract

Goal:

- define how future `50 km` asset ingestion plugs in without rewriting the simulator

Status:

- **architecture complete, implementation pending**

Delivered:

- provider-agnostic ingestion planner
- normalized future asset-layer contract
- `asset_ingestion_plan` metadata in schema output
- asset-plan API surface

Still missing:

- actual Overture or utility-data ingestion
- actual radius-based asset graph construction

### Phase 1F: Real Radius-Based Asset Ingestion

Goal:

- populate the twin with important assets around a city or coordinate automatically

Status:

- **not started**

Will deliver:

- substations, feeders, lines, generation assets, storage assets, EV chargers, critical loads, and demand clusters inside a real radius

## Layer 2: Grid Runtime and Intelligence

### Phase 2A: Grid Topology Foundation

Goal:

- graduate from independent buildings to a feeder-aware graph

Status:

- **complete**

Delivered:

- buses
- lines
- feeders
- topology summaries
- topology validation and rendering support

### Phase 2B: City-To-Twin Runtime

Goal:

- connect generated city twins to the active simulation environment

Status:

- **complete for foundation**

Delivered:

- city twin generation
- control entities
- twin provenance
- map-first runtime shell

Still missing:

- dense real asset population
- stronger clustering logic from real map data

### Phase 2C: Topology Stress and Grid Events

Goal:

- make the topology behave like a real constrained feeder network

Status:

- **complete for first strong version**

Delivered:

- feeder constraints
- line-loading stress
- `congestion_wave`
- `line_derating`
- `feeder_fault`
- topology runtime overlays and summaries

### Phase 2D: Topology-Aware Control Loop

Goal:

- make controllers respond to stress instead of ignoring it

Status:

- **foundation complete locally**

Delivered:

- building payloads now carry feeder and line stress context
- topology-sensitive reward shaping
- rule-based controller feeder-relief and resilience behavior
- DQN runtime post-processing aware of feeder stress
- `topology_control_signal` in websocket payloads

Still missing:

- retraining DQN or MARL policies on these richer observations
- benchmarking controller quality under repeated contingencies

### Phase 2E: Optimization Planner

Goal:

- add a planner for day-ahead and constrained dispatch decisions

Status:

- **not started**

Will deliver:

- optimization baseline
- tariff-aware and congestion-aware planning
- hybrid planner-versus-policy comparisons

### Phase 2F: Graph-Aware RL and Hybrid Arbitration

Goal:

- move beyond per-building shallow DQN into transferable, topology-aware control

Status:

- **not started**

Will deliver:

- graph-aware RL or MARL environment
- shared or clustered policy design
- rule-based, optimizer, and RL arbitration
- evaluation harness for cost, carbon, resilience, and stability

## Layer 3: Operator Control Room and Deployability

### Phase 3A: Sparse Map-First Control Room

Goal:

- make the product feel like an operator theater instead of a dashboard

Status:

- **complete for foundation**

Delivered:

- sparse command-center layout
- map-centered UI
- left launch rail
- right intelligence rail
- bottom live signal dock

### Phase 3B: City Launch Reliability and Map Stability

Goal:

- make the map-first UI behave like a real product under live updates

Status:

- **complete locally**

Delivered:

- city chips now actually launch twins
- right rail and launcher scrolling fixes
- larger map footprint
- map flicker fix on resume by preventing map re-creation on each live tick

### Phase 3C: Topology-Aware Operator Guidance

Goal:

- surface the new topology-aware control posture clearly in the UI

Status:

- **partially complete**

Delivered:

- topology stress rail
- map stress overlays
- operator guidance reacting to topology events

Still missing:

- dedicated UI for `topology_control_signal`
- clearer controller posture and feeder relief storytelling
- richer event playback and intervention narrative

### Phase 3D: Replay, Counterfactuals, and Mission-Control Storytelling

Goal:

- make the operator experience unforgettable

Status:

- **not started**

Will deliver:

- replay mode
- intervention timeline
- counterfactual panel
- “why this action / why not another action” story

### Phase 3E: Real-World Integration Adapters

Goal:

- make the system look deployable, not just simulated

Status:

- **not started**

Will deliver:

- telemetry contracts
- adapter architecture
- MQTT / REST / protocol bridge direction
- edge/backend separation plan

### Phase 3F: Final Hackathon Polish

Goal:

- tighten the product story, deployability, and submission quality

Status:

- **not started**

Will deliver:

- final README / Devpost alignment
- demo script
- deployment-ready config
- visual and narrative polish

## Completed vs Remaining

### Completed

- Phase 0
- Phase 1A
- Phase 1B
- Phase 1C
- Phase 1D foundation
- Phase 1E architecture
- Phase 2A
- Phase 2B foundation
- Phase 2C first strong version
- Phase 2D foundation
- Phase 3A foundation
- Phase 3B local foundation
- Phase 3C partial

### Remaining Major Work

- Phase 1F real radius-based asset ingestion
- Phase 2E optimization planner
- Phase 2F graph-aware RL and hybrid arbitration
- Phase 3C full topology-control UI
- Phase 3D replay and counterfactuals
- Phase 3E integration adapters
- Phase 3F final polish

## What Is Committed vs Local

Committed baseline includes:

- Phase 2C topology stress runtime in commit `257c279`
- Electricity Maps `v4` signal spine in commit `fe68c8f`

Validated but currently uncommitted local work includes:

- frontend stability fixes
- asset-ingestion architecture files
- topology-aware control-loop backend changes

## Tests Run and Passing

Backend:

- `python run_test.py`
- `python run_city_twin_test.py`
- `python run_geo_test.py`
- `python run_geo_enrichment_test.py`
- `python run_operating_context_test.py`
- `python run_topology_constraints_test.py`
- `python run_asset_ingestion_plan_test.py`
- `python run_electricity_maps_signal_spine_test.py`

Frontend:

- `npm run lint`
- `npm run build`

Important precision:

- the latest frontend stability fixes were revalidated with `npm run lint`
- the earlier production build already passed, but a fresh full browser automation pass has not been done in this exact local slice

## CTO Build Order

If the goal is to win fast, the best order now is:

1. finish the current local slice and commit it
2. complete **Phase 3C** by surfacing topology control posture in the frontend
3. start **Phase 2E** with an optimization planner baseline
4. start **Phase 2F** by upgrading RL observations and training to topology-aware control
5. only then implement **Phase 1F** real `50 km` asset ingestion
6. finish **Phases 3D, 3E, and 3F**

Reason:

- the product already has enough shell to demo
- the next biggest leverage is better decisions, not denser raw maps
- the `50 km` ingestion phase should land when the control stack is ready to consume it cleanly

## Immediate Next Recommended Phase

**Next recommended phase: Phase 3C full implementation**

Build next:

- surface `topology_control_signal` in the frontend
- show controller posture changes clearly
- show feeder-targeted resilience guidance
- make the operator understand why the controller changed behavior during faults and congestion

After that:

- move directly into **Phase 2E / 2F**

## Timeline Reality

- **Strong hackathon-winning version:** 3 to 4 weeks total
- **Serious end-to-end platform:** 6 to 8 weeks
- **Production-polished version:** 10 to 12 weeks
