# NEXUS GRID Platform Roadmap

## Executive Position

NEXUS GRID already has strong demo energy. It does **not** yet have a defensible simulation core.

Right now, the project wins attention because of packaging:

- the frontend feels like a control room
- the WebSocket loop makes the demo feel alive
- the emergency controls create a memorable presentation moment

Right now, the project loses technical depth because of architecture:

- the environment is a handcrafted single-layer simulator, not a grid model
- the "universal" schema is still a small manual district description
- the RL agent is local and shallow, not topology-aware or globally transferable
- location support is mocked through static presets and carbon profiles

If the goal is to build something judges cannot mentally reduce to "just CityLearn with a nice UI", the answer is **not** cosmetic hiding. The answer is to evolve this into a **location-native grid intelligence platform**.

The product we should build is:

**NEXUS GRID Atlas**

An AI-native operating system for any urban district, campus, industrial park, or feeder that can:

- instantiate a digital twin from coordinates alone
- ingest real-world carbon, weather, tariff, and asset context
- simulate resilience, dispatch, and market behavior
- switch between RL, optimization, and rule-based control
- expose explainable operator actions through a serious mission-control UI

## What The Current Code Actually Is

### Backend strengths

- [main.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\main.py) already exposes a clean FastAPI plus WebSocket interface.
- [schema_loader.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\schema_loader.py) gives you the seed of a portable configuration model.
- [simulation_runner.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\simulation_runner.py) is a decent orchestration shell for live sessions.
- [environment.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\environment.py) contains a compact and understandable simulation loop that is easy to evolve.

### Frontend strengths

- [page.tsx](C:\Users\saury\Desktop\devpost\nexus-grid\frontend\src\app\page.tsx) already frames the system like an operator console rather than a CRUD dashboard.
- [TelemetryCharts.tsx](C:\Users\saury\Desktop\devpost\nexus-grid\frontend\src\components\TelemetryCharts.tsx), [DistrictMap.tsx](C:\Users\saury\Desktop\devpost\nexus-grid\frontend\src\components\DistrictMap.tsx), and [LedgerTable.tsx](C:\Users\saury\Desktop\devpost\nexus-grid\frontend\src\components\LedgerTable.tsx) establish the right product language: control, telemetry, economy, and events.

### Hard truths

1. The environment is not a grid.
   [environment.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\environment.py) models buildings independently and settles surplus/shortage through a scalar P2P pool. There are no buses, lines, transformers, feeder limits, voltage constraints, outage propagation, congestion, or N-1 reliability behavior.

2. The "global" capability is not global.
   The location model is currently just a static `carbon_profile` plus a small building list. That is a flexible preset system, not a world-ready deployment model.

3. The RL agent is real code, but strategically weak.
   [dqn_agent.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\dqn_agent.py) uses only 5 state features per building: `soc`, `solar_norm`, `carbon_norm`, `hour_sin`, `hour_cos`. It does not observe tariff, congestion, neighborhood interactions, building class embeddings, forecasts, topology, price volatility, or district state.

4. The current DQN does not generalize across district shapes.
   The saved checkpoint in [dqn_agent.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\dqn_agent.py) is tied to `n_buildings`. If the checkpoint building count differs from the active schema, load fails and [simulation_runner.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\nexusgrid\core\simulation_runner.py) warns that the agent may act randomly.

5. The training path is currently inconsistent.
   [train_dqn.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\train_dqn.py) looks for presets under `nexusgrid/configs`, while the actual schemas live in `nexusgrid/presets`. That means the advertised preset-conditioned training path is not truly aligned with the current repository layout.

6. The environment is synthetic at the wrong layers.
   The current solar, load, and carbon behavior are mainly handcrafted curves plus noise. That is acceptable for a prototype, but not for a platform pitch built around "any part of the world without changing code."

## Opinionated Product Direction

### What to keep

- Keep the command-center presentation.
- Keep the emergency drill concept.
- Keep explainability as a user-facing differentiator.
- Keep the schema-driven mindset.
- Keep the live streaming experience.

### What to demote

- Demote the current P2P token ledger from "thesis" to "module".
- Demote the current DQN from "hero intelligence" to "baseline controller".
- Demote the current handcrafted environment from "engine" to "sandbox mode".

### What to build instead

Build a three-layer platform:

1. **Geo-to-Twin Ingestion Layer**
   Input a location, not a hand-authored district.

2. **Hybrid Simulation and Optimization Core**
   Combine graph-aware simulation, optimization, and RL rather than betting everything on one DQN.

3. **Operator Intelligence Layer**
   Present resilience, cost, carbon, and dispatch decisions like a serious operations product.

## What To Borrow From Other Platforms

### 1. CityLearn: rich building observations, custom reward design, EV modeling

Borrow:

- richer observation spaces across calendar, weather, district, and building signals
- configurable reward functions
- electric vehicle charger abstractions
- central-agent and per-building control modes

Do not borrow:

- the identity
- the bare benchmark framing
- the "small predefined district" feel

Use it like this:

- CityLearn-compatible mode becomes one backend adapter, not the product itself
- your product language stays "Atlas digital twin" and "grid operations intelligence"

### 2. Grid2Op: topology, contingencies, maintenance, redispatch, graph actions

Borrow:

- explicit line and bus modeling
- maintenance and hazard simulation
- redispatch and storage actions
- topology-aware control framing

This is the single biggest missing layer if you want to sound like infrastructure instead of a building battery demo.

### 3. PyPSA: optimization and planning

Borrow:

- optimal power flow
- security-constrained optimization
- capacity expansion planning
- rolling-horizon dispatch
- sector coupling mindset

This is how you escape the trap of "RL everywhere." Fast-timescale control can be RL. Slow-timescale planning should be optimization.

### 4. OpenEMS / OpenFMB / OpenADR: interoperability and reality

Borrow:

- adapter-based device integration
- Edge/Backend architecture separation
- Modbus, MQTT, REST, and semantic device communication concepts
- demand response signaling patterns

This is how you make the project feel deployable instead of decorative.

### 5. Global data sources: location-native twin generation

Borrow:

- geocoding and search
- map object extraction
- weather and irradiance time series
- global carbon intensity and power signals
- tariff lookup and demand-response structures

This is the unlock for "anywhere in the world without changing code."

## The New System We Should Build

## Layer A: Universal Geo-to-Twin Engine

Input:

- place name
- coordinates
- polygon
- uploaded feeder or campus file

Pipeline:

1. geocode the target
2. query surrounding map objects and land-use types
3. infer candidate building archetypes
4. assign region-specific weather, solar, and carbon profiles
5. infer tariff, demand-response, and utility context
6. generate a normalized `district twin schema`

Output:

- a fully generated district/facility schema
- confidence scores for inferred attributes
- editable assumptions panel in the UI

This is where you win the hackathon.

The killer demo is not "here is a five-building demo." The killer demo is:

> "Give me a lat/lon in Nairobi, Pune, Austin, or Berlin, and I will generate a working district twin in under a minute."

## Layer B: Hybrid Grid Intelligence Core

This layer should support **three control regimes**:

### 1. Heuristic mode

Use for:

- fallback
- interpretability
- debugging
- deterministic demo stability

### 2. Optimization mode

Use for:

- day-ahead scheduling
- tariff-aware dispatch
- contingency planning
- capital allocation

### 3. RL mode

Use for:

- real-time adaptive control
- non-linear policies
- human-in-the-loop strategy learning
- disturbance response under uncertainty

The correct architecture is **hybrid control**, not ideological RL.

## Layer C: Operator Mission Control

The UI should evolve from "cool dashboard" into a real operational theater:

- geo map with layers
- feeder health
- line congestion and contingency states
- carbon nowcast and forecast
- tariff windows
- asset fleet view
- agent actions with confidence and counterfactuals
- intervention timeline
- scenario branching and replay

## Feature Debate

## Feature to build immediately: Auto-generated district twin

Why:

- highest wow factor
- strongest differentiation
- directly supports "works anywhere"
- impossible to dismiss as a simple benchmark wrapper

## Feature to build immediately: Hybrid control engine

Why:

- makes the product technically believable
- lets you compare heuristic vs optimization vs RL in the same scene
- creates a credible research story

## Feature to build immediately: Contingency and resilience simulator

Why:

- judges remember failures and recoveries
- resilience is easier to sell than raw algorithm metrics
- it aligns with real utility pain

## Feature to postpone: tokenized marketplace theatrics

Why:

- the current ledger is a nice visual, but it is not the strongest moat
- if you over-index on token economics, the project starts to smell like hackathon theater
- keep market logic, but anchor it to tariffs, flexibility bids, ancillary services, and carbon-aware dispatch

## Feature to postpone: "true AGI" language

Why:

- smart judges punish vague intelligence claims
- grounded control stacks win more trust than inflated AI branding

## Feature to kill entirely: manually authored districts as the main workflow

Why:

- that caps the project at a demo
- universal ingestion is the entire strategic unlock

## RL Analysis and Recommendation

## What the current RL does well

- It is easy to understand.
- It trains quickly on CPU.
- It gives you a working policy artifact for a demo.
- It already establishes the interface between controller and simulation.

## Why the current RL is not enough

1. It is not graph-aware.
   The agent reasons building-by-building with no feeder or neighborhood context.

2. It is not policy-shared.
   One network per building is a poor scaling strategy for heterogeneous districts.

3. It is not transfer-ready.
   The checkpoint is tightly coupled to building count and shallow feature assumptions.

4. It is not forecast-native.
   Forecasting appears only as a manual override, not as part of the state.

5. It is not market-complete.
   It does not see tariffs, constraints, bids, congestion, curtailment penalties, or demand-response events.

## What the new RL stack should be

### Stage 1

Move to a standardized multi-agent environment interface.

Recommendation:

- expose the district as a PettingZoo Parallel environment or RLlib `MultiAgentEnv`
- share policy weights across asset classes where possible
- keep building embeddings or typed encoders for heterogeneity

### Stage 2

Add graph structure.

Recommendation:

- represent buildings, DERs, feeders, and substations as a graph
- use a graph encoder or graph-conditioned policy
- add edge features like line capacity, distance, congestion, and switch state

### Stage 3

Train under domain randomization.

Recommendation:

- randomize geography
- randomize weather
- randomize tariffs
- randomize asset mixes
- randomize contingencies

This is how the phrase "works anywhere" becomes technically honest.

### Stage 4

Use hybrid control.

Recommendation:

- optimizer for planning
- RL for adaptation
- heuristics for safe fallback
- policy arbitration layer for reliability

## Architecture Roadmap

## Phase 0: Stop the bleeding

Goal: make the current code honest and stable.

Tasks:

- fix preset loading in [train_dqn.py](C:\Users\saury\Desktop\devpost\nexus-grid\backend\train_dqn.py)
- separate sandbox simulator from future world-scale engine
- clean up encoding artifacts in backend copy and frontend labels
- add a model registry instead of assuming one checkpoint fits all districts
- add proper experiment metadata for each trained policy

## Phase 1: Universal schema and adapters

Goal: make the twin generation portable.

Deliverables:

- `LocationResolver`
- `GeoTwinBuilder`
- `WeatherProvider`
- `CarbonProvider`
- `TariffProvider`
- `ArchetypeLibrary`

Output:

- generated district schema from coordinates
- editable assumptions with provenance for each inferred field

## Phase 2: Real grid semantics

Goal: graduate from building pool to grid graph.

Deliverables:

- buses, lines, transformers, feeders, substations in schema
- topology-aware simulation core
- congestion, outage, and switching mechanics
- contingency event engine

Output:

- district twin becomes feeder twin

## Phase 3: Hybrid intelligence

Goal: create a real decision stack.

Deliverables:

- rule baseline controller
- optimization planner
- graph-aware MARL controller
- arbitration layer
- evaluation harness for stability, cost, carbon, comfort, and resilience

Output:

- one platform, multiple control strategies, measurable tradeoffs

## Phase 4: Mission control UI

Goal: turn the experience from impressive to unforgettable.

Deliverables:

- map-first interface
- scenario branching and replay
- operator timeline
- intervention diff view
- confidence plus rationale pane
- "why not this action?" counterfactual explorer

Output:

- a demo that feels like a product, not a notebook

## Phase 5: Edge and ecosystem connectivity

Goal: make it feel deployable.

Deliverables:

- OpenEMS-style adapter layer
- MQTT and REST channels
- Modbus or SunSpec pilot integration
- demand-response event bridge
- telemetry ingestion contracts

Output:

- clear path from simulation to operational pilot

## My Most Opinionated Recommendation

Do **not** spend the next sprint polishing the existing small-grid simulator.

That path improves aesthetics, not category position.

Spend the next sprint building:

1. location-to-schema generation
2. graph-aware schema extensions
3. a hybrid planner/controller architecture
4. a stronger mission-control story around resilience and portability

If you do those four things, the project stops being:

> "a smart grid simulation dashboard"

and becomes:

> "a universal AI operating system for regional grid-edge intelligence"

That is the level where judges stop comparing you to other student demos and start comparing you to emerging infrastructure products.

## Source Inspirations

- CityLearn docs: https://www.citylearn.net/
- Grid2Op docs: https://grid2op.readthedocs.io/en/latest/index.html
- PyPSA docs: https://docs.pypsa.org/
- OpenEMS docs: https://openems.github.io/openems.io/openems/latest/
- OpenFMB docs: https://openfmb.openenergysolutions.com/docs/openfmb/intro/
- OpenADR info: https://www.openadr.org/faq
- Nominatim search docs: https://nominatim.org/release-docs/latest/api/Search/
- Overpass API docs: https://wiki.openstreetmap.org/wiki/Overpass_API
- NASA POWER hourly API: https://power.larc.nasa.gov/docs/services/api/temporal/hourly/
- Electricity Maps API: https://portal.electricitymaps.com/developer-hub/api/getting-started
- OpenEI utility rates: https://openei.org/services/doc/rest/util_rates/
