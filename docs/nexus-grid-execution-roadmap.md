# NEXUS GRID Execution Roadmap

## Restart Handoff

If you restart Codex later, the shortest accurate resume prompt is:

`Continue NEXUS GRID from Phase 2B using the roadmap and current repo state. Electricity Maps is the live signal spine, not the full twin. Keep building the city-to-digital-twin RL platform.`

## Current Build Status

Completed:

- **Phase 0:** stabilization, model registry, honest controller fallback, sandbox engine labeling
- **Phase 1A:** geo resolution and location-to-schema generation
- **Phase 1B:** live enrichment providers for weather, carbon, and tariffs
- **Phase 1C:** operating context wired into runtime simulation and dashboard telemetry
- **Phase 2A:** topology foundation with buses, lines, feeders, topology summaries, and a cleaner mission-control dashboard

Current truth:

- the platform is no longer just a manual district simulator
- it can already resolve seeded real locations and enrich them with live context
- Electricity Maps is currently integrated as a **live carbon signal provider**
- the current Electricity Maps token is still **sandbox-mode**, so carbon data is provider-side sandbox until the production key is approved
- the UI has been reframed as an operator control room, but the city-selection and full map-first twin flow are still ahead

## Short Answer

If I drive this with you continuously, the timeline is:

- **Phase 0 to Phase 1:** 4 to 6 days
- **Phase 2:** 7 to 10 days
- **Phase 3:** 10 to 14 days
- **Phase 4:** 5 to 7 days
- **Phase 5:** 7 to 10 days

## Realistic Totals

- **Hackathon-winning upgraded MVP:** 3 to 4 weeks
- **Serious end-to-end platform across all phases:** 6 to 8 weeks
- **Production-polished version:** 10 to 12 weeks

## Recommended Build Order

### Phase 0: Stabilize the current core

Duration:

- 2 to 3 days

Goals:

- fix the DQN training path
- clean up checkpoint handling
- clean up encoding and documentation inconsistencies
- separate sandbox simulation from the future universal engine

Deliverables:

- reliable training flow
- versioned model loading
- cleaner repo structure
- honest sandbox/runtime separation

Status:

- complete

### Phase 1: Universal geo-to-schema engine

Duration:

- 2 to 3 days for a first version
- 5 to 7 days for a stronger version

Goals:

- accept location input instead of manual district-only configs
- generate district schema from coordinates
- attach weather, solar, carbon, and tariff context

Deliverables:

- `LocationResolver`
- `GeoTwinBuilder`
- generated schema pipeline
- live weather, carbon, and tariff enrichment
- operating-context-driven runtime behavior

Status:

- complete for the first serious version
- still needs stronger map ingestion and production-grade provider coverage

### Phase 2: Real grid semantics

Duration:

- 7 to 10 days

Goals:

- move from building pool to graph-aware grid model
- add buses, lines, transformers, feeders, and contingencies

Deliverables:

- extended schema
- topology-aware simulator
- failure and congestion events

Status:

- **Phase 2A complete:** topology foundation exists
- **Phase 2B next:** city-to-grid twin generation, map layers, and agent clustering

### Phase 2B: City-To-Twin Architecture

Duration:

- 3 to 5 days for first strong version

Goals:

- let a user pick a city or coordinates and treat that geography as the active environment
- use Electricity Maps for live external grid signals
- build our own control-ready digital twin instead of pretending Electricity Maps is the twin

Deliverables:

- zone and city resolver
- geo twin builder that outputs controllable assets, feeders, and demand clusters
- map-first city selection flow
- provenance panel showing which parts came from live APIs vs inference

Core product opinion:

- **Electricity Maps should be the live signal spine, not the full simulation engine**
- we should not clone their map product
- we should use their signals, then generate a richer control-ready twin that they do not provide

### Phase 2C: Grid Events And Constraints

Duration:

- 3 to 5 days

Goals:

- make the topology behave like a real feeder instead of a static graph
- add limits, congestion, switching, outages, and resilience drills

Deliverables:

- line loading constraints
- feeder congestion model
- outage and maintenance events
- topology-aware recovery behavior

### Phase 3: Hybrid intelligence

Duration:

- 10 to 14 days

Goals:

- combine rule-based control, optimization, and RL
- make RL graph-aware and transferable

Deliverables:

- baseline controller
- planner
- improved MARL layer
- evaluation harness

Opinionated direction:

- RL agents should represent **control entities** such as feeder controllers, storage fleets, EV fleets, campuses, and industrial clusters
- they should **not** start as one-agent-per-every-generator in a whole city
- optimization should handle planning, heuristics should handle safety fallback, and RL should handle adaptive decisions under uncertainty

### Phase 4: Mission-control experience

Duration:

- 5 to 7 days

Goals:

- make the UI unforgettable
- show resilience, intervention, replay, and counterfactuals

Deliverables:

- geo map
- scenario replay
- operator timeline
- explainability and confidence panels

Current note:

- the dashboard has already been upgraded into a cleaner control-room layout
- the next UI leap is map-first city selection plus topology and feeder overlays

### Phase 5: Real-world integrations

Duration:

- 7 to 10 days

Goals:

- make it look deployable, not just simulated
- add adapter architecture for protocols and external telemetry

Deliverables:

- integration adapters
- telemetry contracts
- edge/backend separation

## Strategic Position

The winning version of NEXUS GRID is **not**:

- "Electricity Maps plus RL"

The winning version is:

- **Electricity Maps + geo ingestion + generated digital twin + hybrid control + operator theater**

That means:

- Electricity Maps provides live carbon, mix, imports, exports, load, and price context where available
- NEXUS GRID generates the actual control-ready environment
- the RL layer acts on inferred feeders, storage fleets, EV fleets, demand clusters, and critical assets
- the operator UI explains what the system would do, why, and what happens under failures

## What To Ask For Next

These are the APIs and data sources we are most likely to need as we continue:

- **Electricity Maps production key** for real carbon and signal coverage
- **OpenStreetMap / Overpass data access** for richer map object extraction
- **A stronger weather or irradiance source** if we outgrow Open-Meteo for serious demos
- **Non-U.S. tariff sources** if we want global price realism beyond heuristics

## Next Resume Point

When work resumes, the next best move is:

1. start **Phase 2B**
2. add city and zone selection as a first-class workflow
3. define which real-world asset clusters become agents
4. build the first map-to-twin pipeline that turns a chosen geography into a controllable RL environment

## What I Recommend We Build First

If the goal is to win fast, we should do this order:

1. Phase 0
2. Phase 1
3. Phase 4
4. Phase 2
5. Phase 3
6. Phase 5

That order gives you the strongest early jump in:

- demo quality
- novelty
- "works anywhere" credibility
- judge memorability

## Best Timeline Strategy

### Option A: Fastest winning version

Target:

- 21 to 28 days

Scope:

- Phase 0
- Phase 1
- Phase 4
- selected parts of Phase 2 and Phase 3

### Option B: Full serious version

Target:

- 6 to 8 weeks

Scope:

- all phases fully implemented

## Immediate Next Step

The next best move is to start with:

1. fixing the current RL and preset pipeline
2. designing the universal geo schema
3. scaffolding the location-to-twin engine
4. redesigning the UI around a map-first mission-control flow
