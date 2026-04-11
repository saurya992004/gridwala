# NEXUS GRID — Development Execution Roadmap

> How we systematically engineered a city-scale energy digital twin with Multi-Agent Transformer control from the ground up.

---

## Architecture Overview

NEXUS GRID was built as a three-layer system, each layer depending on the one below it:

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Operator Command Center (Next.js)                  │
│  Real-time WebSocket UI · Glassmorphism · AI Rationale Feed  │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Grid Runtime & Multi-Agent Intelligence (PyTorch)  │
│  MAT Policy · QMIX Mixer · Topology Stress · P2P Market     │
├──────────────────────────────────────────────────────────────┤
│  Layer 1: Digital Twin Foundation (FastAPI + NetworkX)        │
│  Geo Resolution · Schema Engine · Signal Ingestion           │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Digital Twin Foundation

### Phase 0 — Core Stabilization ✅

**Objective:** Establish a reliable simulation engine with clean model lifecycle management.

**What we built:**
- Model registry with preset-aware checkpoint loading and versioned metadata
- Schema-driven environment engine that ingests portable JSON district definitions
- Rule-based fallback controller for deterministic baseline behavior
- Standardized simulation loop with clean state transitions

**Engineering decision:** We chose to decouple the model registry from the environment early. This meant any policy architecture (baseline DQN, MAT, QMIX) could be swapped in without touching the simulation core — a decision that paid off when we upgraded the policy stack later.

---

### Phase 1A — Geo Resolution ✅

**Objective:** Resolve arbitrary city names and GPS coordinates into valid location candidates.

**What we built:**
- `LocationResolver` service with catalog-backed and coordinate-backed resolution
- Backend geo provider endpoints exposed via FastAPI
- Automatic fallback between geocoding providers for reliability

---

### Phase 1B — Live External Signal Ingestion ✅

**Objective:** Make the digital twin context-aware by ingesting real-world environmental data.

**What we built:**
- **Electricity Maps v4** integration — real-time regional carbon intensity (gCO₂eq/kWh)
- **Open-Meteo** weather integration — solar irradiance, temperature, cloud cover
- **OpenEI** tariff integration — time-of-use pricing structures
- Provider fallback logic — graceful degradation to internal stochastic mock engine when API keys are absent

**Engineering decision:** We designed the signal spine as provider-agnostic from day one. Each data source implements a common interface, making it trivial to swap Electricity Maps for a utility-specific SCADA feed in a production deployment.

---

### Phase 1C — Runtime Operating Context ✅

**Objective:** Make ingested signals actually influence simulation behavior, not just display.

**What we built:**
- Live weather context driving solar generation curves and HVAC load profiles
- Carbon intensity signals feeding directly into the reward function
- Tariff windows influencing agent charge/discharge economics
- Enriched payloads streamed to the frontend via WebSocket

---

### Phase 1D — City Launcher & Twin Generation ✅

**Objective:** Move from static district presets toward dynamic, map-native city selection.

**What we built:**
- City-to-twin launcher pipeline — enter coordinates, get a running simulation
- Generated control-entity metadata with provenance tracking
- MapLibre / PMTiles / Overture-ready geo stack foundation
- Asset-ingestion architecture contract for future 50km radius expansion

---

## Layer 2: Grid Runtime & Multi-Agent Intelligence

### Phase 2A — Grid Topology Foundation ✅

**Objective:** Graduate from independent buildings to a physically-constrained feeder network.

**What we built:**
- Full graph topology engine using NetworkX: buses, lines, feeders, substations
- Topology validation, rendering support, and structural summaries
- Each building is now a node in a physical graph with real edge constraints (ampacity, impedance)

**Engineering decision:** We modeled the grid as a dynamic graph $G_t(V, E)$ from the start, anticipating the need for graph-aware policies. This structural choice is what makes the MAT architecture a natural fit — each node becomes a token.

---

### Phase 2B — City-to-Twin Runtime ✅

**Objective:** Connect generated city twins to the live simulation environment.

**What we built:**
- City twin generation pipeline with control entity assignment
- Twin provenance tracking (which geo source, which enrichment providers, confidence scores)
- Map-first runtime shell connecting topology to the simulation loop

---

### Phase 2C — Topology Stress & Grid Events ✅

**Objective:** Make the topology behave like a real constrained feeder network with failure modes.

**What we built:**
- **Feeder constraints** — ampacity limits, voltage regulation boundaries
- **Line-loading stress** — real-time utilization tracking per edge
- **Congestion wave** — cascading overload propagation across feeders
- **Line derating** — thermal and weather-dependent capacity reduction
- **Feeder fault** — complete branch isolation with islanding behavior
- Topology runtime overlays and stress summaries for the frontend

---

### Phase 2D — Multi-Agent Transformer Control Loop ✅

**Objective:** Deploy the MAT + QMIX policy architecture with topology-aware reward shaping.

**What we built:**
- **Multi-Agent Transformer (MAT)** policy network [(Wen et al., NeurIPS 2022)](https://arxiv.org/abs/2205.14953) — each DER node is a token, self-attention learns inter-agent cooperative strategies
- **QMIX monotonic value decomposition** [(Rashid et al., ICML 2020)](https://arxiv.org/abs/2003.08839) — cooperative credit assignment with IGM guarantees
- Topology-sensitive reward shaping with quadratic ampacity penalties
- Building payloads carrying feeder and line stress context into the observation space
- `topology_control_signal` exposed in WebSocket payloads for frontend observability
- Baseline DQN retained for ablation comparison

**Engineering decision:** We chose MAT over MADDPG because our agents operate in discrete action spaces (dispatch quanta). MAT's auto-regressive factorization naturally handles the combinatorial explosion of joint actions across n agents, while MADDPG's continuous actor-critic would require unnecessary discretization. QMIX was chosen over VDN for its state-conditioned mixing, which lets the coordination strategy adapt to grid conditions.

---

## Layer 3: Operator Command Center

### Phase 3A — Map-First Control Room ✅

**Objective:** Build a production-grade operator interface, not a dashboard.

**What we built:**
- Sparse, map-centered command layout (inspired by utility SCADA/EMS control rooms)
- **Left rail:** District launcher, simulation controls, emergency scenarios
- **Right rail:** AI rationale feed, topology intelligence, agent decision explanations
- **Bottom dock:** Live signal indicators (carbon, weather, tariff, grid status)
- Dark-mode glassmorphism aesthetic with Framer Motion transitions

---

### Phase 3B — City Launch Reliability ✅

**Objective:** Make the UI behave like a real product under continuous live updates.

**What we built:**
- City chip launcher with reliable twin instantiation
- Map flicker elimination — prevented map re-creation on each WebSocket tick
- Scroll stability fixes for rail components under streaming data
- Full-viewport map footprint with overlay panels

---

### Phase 3C — Topology-Aware Operator Guidance ✅

**Objective:** Surface the grid intelligence layer clearly in the operator experience.

**What we built:**
- **Topology stress rail** — real-time feeder health visualization
- **Map stress overlays** — color-coded line/feeder utilization on the spatial view
- **Operator guidance** — contextual recommendations reacting to topology events
- **Controller posture badge** — shows current policy mode (normal / feeder-relief / resilience / islanded)
- **Control posture summary** in the bottom signal dock
- **Network view** with per-feeder status, utilization, and agent assignment

---

### Phase 3D — Chaos Engineering & Resilience Drills ✅

**Objective:** Let operators inject grid emergencies and watch the AI adapt in real-time.

**What we built:**
- **Emergency scenario dropdown** — one-click injection of grid shocks
- **Scenarios implemented:**
  - 🔥 Heatwave — HVAC load spike to 200%, solar derating
  - ⚡ EV surge — sudden fleet charging demand
  - 🔌 Feeder fault — branch isolation with cascading effects
  - 📈 Congestion wave — propagating overload across topology
  - 🌑 Solar blackout — complete PV generation dropout
- **Emergency alert banner** — visual feedback for active emergency state
- **Auto-switch to Network view** on emergency trigger for full topology visibility
- MAT policy adapts dispatch in real-time via attention-based coordination

---

## Validation & Testing

### Backend
| Test Suite | Coverage |
|---|---|
| `run_test.py` | Core simulation loop |
| `run_city_twin_test.py` | Twin generation pipeline |
| `run_geo_test.py` | Geo resolution |
| `run_geo_enrichment_test.py` | Signal enrichment |
| `run_operating_context_test.py` | Runtime context fusion |
| `run_topology_constraints_test.py` | Topology stress engine |
| `run_asset_ingestion_plan_test.py` | Ingestion architecture |
| `run_electricity_maps_signal_spine_test.py` | Electricity Maps v4 |

### Frontend
- `npm run lint` — zero warnings
- `npm run build` — production build passing

---

## Summary

| Metric | Value |
|---|---|
| **Total phases executed** | 13 |
| **Backend modules** | 11 core modules |
| **Policy architectures** | MAT + QMIX (primary) · DQN (baseline) |
| **External integrations** | 3 (Electricity Maps, Open-Meteo, OpenEI) |
| **Emergency scenarios** | 5 |
| **Test suites** | 8 backend + 2 frontend |
| **Real-time middleware** | WebSocket bi-directional JSON streaming |
