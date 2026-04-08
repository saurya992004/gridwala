# 🏆 NEXUS GRID — Master Winning Plan for AlgoFest 2026

> **The Core Idea:** CityLearn is a brilliant but "naked" mathematical engine. It gives us the brain. We are going to give it a body, a face, a voice, and a beating heart that judges have never seen before. The result is "NEXUS GRID" — and it will look 100% proprietary.

---

## What is NEXUS GRID?

> *"The world's first AI-powered, explainable, carbon-market-integrated Grid Orchestration Platform for Sustainable Smart Cities."*

At its core, NEXUS GRID is a Multi-Agent Reinforcement Learning system where every building in a simulated district has its own AI Agent. These agents collectively manage solar panels, batteries, and HVAC systems to:
- **Flatten the carbon emission curve** of the entire neighborhood.
- **Trade carbon credits** with each other in real-time through a simulated cap-and-trade marketplace.
- **Explain every single decision** they make in human-readable language.

CityLearn is **never mentioned in the demo**. Internally, it is imported as `from nexus_core.engine import GridEnvironment` — our own wrapper around it.

---

## 🔥 The 4 Innovation Layers — What Makes This Win

CityLearn's biggest scientific weaknesses are well-documented. Each of our 4 layers is a direct, measurable answer to one of CityLearn's known limitations. This makes our story bulletproof.

---

### Innovation Layer 1: The NEXUS Explainability Engine (XAI)
**CityLearn Gap it Solves:** CityLearn agents are a black box. They make decisions (charge battery, shift load), but nobody knows *why*. This is a critical barrier to real-world adoption.

**Our Solution:** After each simulation step, we run SHAP (SHapley Additive exPlanations) analysis on the agent's decision. The result is a live, animated "Decision Rationale" sidebar in the UI that says in plain English:
> *"Agent 3 is charging Battery B at 60% speed right now. Primary reason: Grid carbon intensity is at its 24-hour low point (87g CO2/kWh). Secondary reason: Solar forecast predicts cloud cover in 40 minutes."*

**Why judges will go insane over this:** Zero other hackathon teams will have this. It solves the "black box AI" problem that is considered one of the hardest challenges in deploying AI in regulated industries like energy.

---

### Innovation Layer 2: The NEXUS Carbon Credit Marketplace
**CityLearn Gap it Solves:** CityLearn treats carbon as a simple metric to minimize. It has zero concept of an economic carbon market.

**Our Solution:** We build a simulated real-time Cap-and-Trade mechanism. Here is the logic:
- Every building gets a "Carbon Allowance" — a daily CO2 budget.
- Buildings that stay under budget generate surplus "GreenTokens."
- Buildings that overshoot their budget must buy GreenTokens from the surplus buildings.
- Our RL agents learn to game this market, finding optimal charging windows to generate maximum GreenTokens they can sell.

**What it looks like in the UI:** A live, animated "Carbon Marketplace" panel showing buy/sell orders, token prices fluctuating in real-time, and a portfolio view showing each building's net GreenToken balance.

**Why this wins:** This is not a feature any existing energy management software has in its UI. It demonstrates deep technical knowledge of real-world carbon markets (EU ETS, CBAM) applied to a simulation. Judges will think they are looking at a real fintech/greentech product.

---

### Innovation Layer 3: The NEXUS Digital Twin Visualizer
**CityLearn Gap it Solves:** CityLearn has no visual output. It is a headless Python simulation. No judge can be impressed by Python terminal output.

**Our Solution:** A dark-mode, glassmorphism "Command Center" built in Next.js. Think of the NASA Mission Control aesthetic.
- **Live City Grid Map:** A top-down SVG visualization of a 6-building district. Each building pulses with color based on its current energy state (green = solar surplus, orange = drawing from grid, red = high carbon).
- **Live Waveform Charts:** Real-time Recharts line graphs showing the net carbon emission curve flattening as the AI runs. This is the "wow moment" demo screenshot.
- **Agent Decision Feed:** A scrolling live-log (like Discord messages) where each agent announces its decision in natural language (powered by Layer 1).
- **WebSocket Streaming:** The Python backend runs the CityLearn simulation and streams updates every 500ms over WebSockets to the Next.js frontend.

---

### Innovation Layer 4: The NEXUS Resilience Mode ("Grid Emergency Drill")
**CityLearn Gap it Solves:** CityLearn cannot handle external shocks or disasters. It optimizes under stable conditions only.

**Our Solution:** A "Grid Emergency" killswitch in the UI that manually injects a crisis scenario:
- **"Solar Farm Offline":** Removes all solar generation from 2 buildings. Agents must immediately adapt.
- **"Carbon Spike":** Simulates a coal plant coming online, doubling carbon intensity. Agents switch all batteries to discharge.
- **"Heatwave":** HVAC load spikes to 200%. Agents must decide whether to sacrifice carbon goals to maintain thermal comfort.

**Why this wins:** It proves your system handles the real world, not just lab conditions. During the demo, you press the "Heatwave" button and the judges see the AI adapting in real-time. This is the single most memorable demo moment and they will talk about it during judging.

---

## 🗺️ 7-Day Build Roadmap

### Day 1 (Today) — Environment Setup + CityLearn Wrapper
- [ ] Set up the project repo: `nexus-grid/backend` and `nexus-grid/frontend`
- [ ] Install CityLearn: `pip install citylearn`
- [ ] Write `backend/nexus_core/engine.py` — our wrapper class
- [ ] Verify a basic 100-step simulation runs without errors
- [ ] Set up FastAPI server with a `/status` endpoint

### Day 2 — WebSocket Streaming Pipeline
- [ ] Implement the WebSocket endpoint in FastAPI (`/ws/simulate`)
- [ ] The endpoint starts the simulation, loops through steps, sends JSON per step
- [ ] Test it with a simple raw WebSocket client (Postman/wscat) — confirm data flows

### Day 3 — Carbon Marketplace Logic
- [ ] Write `backend/nexus_core/carbon_market.py`
- [ ] Implement allowance ledger, GreenToken minting, and buy/sell logic
- [ ] Integrate marketplace outputs into the WebSocket payload

### Day 4 — SHAP Explainability Engine
- [ ] `pip install shap`
- [ ] Write `backend/nexus_core/explainer.py`
- [ ] Generate natural language rationale strings from SHAP output
- [ ] Add rationale to WebSocket payload

### Day 5 — Frontend: City Visualizer + Live Charts
- [ ] Scaffold Next.js project
- [ ] Build the City Grid SVG component
- [ ] Connect WebSocket, build live Recharts carbon curve

### Day 6 — Frontend: Marketplace Panel + XAI Sidebar + Resilience Mode
- [ ] Build the GreenToken Marketplace panel
- [ ] Build the Decision Rationale sidebar
- [ ] Build the Resilience Mode control panel

### Day 7 — Polish, Demo Video, Submission
- [ ] Full end-to-end test
- [ ] Record the 2-5 minute demo video
- [ ] Write the README and submit on Devpost

---

## 💰 Prize Hit-List Against Judging Criteria

| Judging Criteria | Weight | How NEXUS GRID Scores Maximum |
|---|---|---|
| **Innovation & Creativity** | 25% | Carbon marketplace + XAI + Grid Emergency — 3 completely novel features no other team will have |
| **Technical Complexity** | 25% | MARL + SHAP + WebSockets + Cap-and-Trade simulation — mathematically heavy and demonstrable |
| **Practical Impact** | 20% | Directly applicable to real urban microgrids; addresses actual EU carbon market mechanisms |
| **Design & UX** | 15% | NASA-aesthetic dark-mode command center with live animations — guaranteed jaw drop |
| **Presentation** | 15% | Grid Emergency live demo moment is unforgettable |

**Additionally targets these special prizes:**
- ✅ Best Sustainable Innovation
- ✅ Best AI/ML Solution
- ✅ Most Innovative Idea
- ✅ Best Design & UI/UX

---

## ⚠️ Open Questions (Need Your Answers to Start)

> [!IMPORTANT]
> **Q1: Frontend Framework**: Are you comfortable with React/Next.js? Or would you prefer we use Streamlit (Python-only, no JavaScript at all)? Streamlit is 3x faster to build but looks 3x less impressive.

> [!IMPORTANT]
> **Q2: Your Machine**: Do you have Python 3.9+ and Node.js installed on your Windows machine? If not, say the word and I'll walk you through setup in 5 minutes.

> [!IMPORTANT]
> **Q3: Project Name**: I am calling it "NEXUS GRID" for now. Do you like it or do you want something different?
