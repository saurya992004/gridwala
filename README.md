<div align="center">
  <h1>⚡ NEXUS GRID</h1>
  <h3>Autonomous City-Scale Energy Digital Twin & Multi-Agent Transformer Orchestrator</h3>
  <p><em>The first application of Multi-Agent Transformer (MAT) architecture to real-time energy digital twins — enabling zero-shot cooperative dispatch across arbitrary grid topologies.</em></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
  [![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
  [![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)
  [![Status](https://img.shields.io/badge/Status-Production_Ready-success.svg)]()
</div>

<br/>

### 📊 Pitch Deck
[**View the AlgoFest 2026 Presentation (Google Drive)**](https://drive.google.com/file/d/1vxaxv1BPe_PtsL3CYBJQc_K334l_ec4Q/view?usp=sharing)

### 🌐 Live Deployment
- **Frontend Control Room:** [https://gridwala-nexusgrid-frontend.onrender.com](https://gridwala-nexusgrid-frontend.onrender.com)
- **Backend Health/API:** [https://gridwala-nexusgrid-backend.onrender.com/status](https://gridwala-nexusgrid-backend.onrender.com/status)

> Share the **frontend link** with judges as the main experience. The backend link is included only for technical verification. On free Render, the first load after inactivity may take a short cold-start delay.

---

### 🚨 The Problem
Modern energy grids are decaying under the weight of their own complexity. As we transition to distributed energy resources (DERs), energy supply has become volatile, decentralized, and entirely unpredictable. 

**Current industry tools fail catastrophically because:**
- They rely on **human-authored static heuristics** that cannot scale.
- They depend on **pre-trained machine learning models** that instantly degrade during physical grid anomalies (data drift).
- They are **blind to the underlying physical constraints** of the grid.

**The exact problem:** The grid is no longer a predictable top-down utility; it is an infinitely complex mathematical graph, and we lack the dynamic intelligence to orchestrate it.

### 💡 The Solution
**NEXUS GRID** is a groundbreaking, mathematically advanced digital twin and autonomous control operating system. 

We instantly generate a live topological twin of any city, inject real-world telemetry, and unleash a swarm of **Non-Pretrained Reinforcement Learning Agents** (specifically, **Multi-Agent Transformers** with **QMIX** value decomposition) to autonomously balance the grid—enabling emergent cooperative energy dispatch with zero-shot generalization to unseen grid configurations.

---

## 🧠 Core Innovation: Adaptive Multi-Agent Control

Our core innovation is **Adaptive Multi-Agent Control**, a topology-aware control framework that can shift coordination strategy as grid conditions change instead of binding the system to one static controller family. NexusGrid models the district as a **Decentralized Partially Observable MDP (Dec-POMDP)** over a dynamic graph $G_t(V, E)$ and lets the runtime route between cooperative RL behavior, safety-constrained fallback logic, and event-specific coordination according to feeder stress, tariff pressure, carbon intensity, and resilience requirements.

At the architectural level, this is compatible with **Multi-Agent Transformer-style sequence coordination** and **QMIX-style monotonic value decomposition** [[1]](#references) [[2]](#references), where local agent utilities can be composed into a globally aligned dispatch objective while preserving decentralized actionability. In practical terms, the system is designed to fall back or switch policy posture when the grid demands a different control regime, rather than forcing one brittle policy to operate across every market, weather, and topology state.

Mathematically, the control objective can be written as a constrained cooperative optimization:

$$ \pi(\mathbf{a} | \mathbf{o}, G_t) = \arg\max_{\pi} \; \mathbb{E}\left[\sum_t R_t\right] \quad \text{s.t. feeder, line, and energy balance constraints} $$

with a reward shaped around cleaner dispatch, lower stress, and continuity of service:

$$ R_t = \alpha \cdot \Delta E_{green} - \beta \cdot \mathcal{L}(C_{grid}^{(t)}) - \lambda \cdot \sum_{e \in E} \max\left(0, \frac{|I_e|}{I_{max}} - 1\right)^2 $$

---

## ✨ Features

### 📍 Phase 1: Dynamic Topological Graph Generation (The Twin)
Instantly maps any geographic coordinate into a structured, executable mathematical graph (nodes = buildings/DERs, edges = physical feeders) via `NetworkX`.

### 📡 Phase 2: Live External Signal Ingestion
The twin is completely live — it independently ingests real-time carbon intensity, wholesale electricity pricing, and stochastic weather forecasts via robust API websockets.

### 🤖 Phase 3: MAT + QMIX Multi-Agent Control (Zero-Shot)
The core autonomous engine. Each DER node is a token. Self-attention learns inter-agent dependencies. QMIX ensures decentralized execution with global optimality guarantees. **No pre-training required.**

### ⚡ Phase 4: Chaos Engineering (Resilience Drills)
Operators inject arbitrary shocks — EV load spikes, cascading feeder failures, heatwaves — and watch the MAT policy adapt and self-heal via emergent attention-based coordination.

### 🎛 Phase 5: Premium Command Center
An elite Next.js spatial interface with real-time WebSocket telemetry, glassmorphism, Framer Motion transitions, and an AI Rationale feed for deep observability into the policy's reasoning.

---

## 🏗 Architecture

```
nexusgrid/
├── agents/
│   ├── mat_policy.py          ← Multi-Agent Transformer (primary policy)
│   ├── qmix_mixer.py          ← QMIX monotonic value decomposition
│   └── baselines/
│       └── dqn_agent.py       ← Independent DQN (ablation baseline)
├── core/
│   ├── environment.py         ← NexusGridEnv (Dec-POMDP physics engine)
│   ├── topology.py            ← Dynamic graph generation (NetworkX)
│   ├── simulation_runner.py   ← Async simulation orchestrator
│   └── schema_loader.py       ← Grid topology schema parser
```

---

## 🛠 Tech Stack

| Layer | Stack |
|---|---|
| **Policy Architecture** | Multi-Agent Transformer (MAT) + QMIX, PyTorch |
| **Physics Simulation** | FastAPI (Python 3.11+), Uvicorn, NetworkX, AsyncIO |
| **Command & Control** | Next.js 14, React 18, TypeScript, TailwindCSS |
| **Real-Time Middleware** | WebSockets (bi-directional JSON streams) |
| **Visualization** | Framer Motion, Recharts |

---

## 🚀 Setup & Execution

> **API Keys:** The system hooks into Electricity Maps and EPEX SPOT for live telemetry, but you can leave `.env` keys blank — the backend falls back to its internal stochastic mock-data engine automatically.

### Quickest Way For Judges

If you only want to review the project, open:

```text
https://gridwala-nexusgrid-frontend.onrender.com
```

### One-Click Boot (Recommended)

**Prerequisites:** `Python 3.11+` and `Node.js 20+`

**Windows:**
```cmd
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh && ./start.sh
```

The boot scripts automatically:
- create the backend virtual environment if needed
- install backend dependencies including `torch`
- install frontend dependencies
- start the backend on `http://localhost:8000`
- start the frontend on `http://localhost:3000`

### Manual Setup

**Backend:**
```bash
cd nexus-grid/backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd nexus-grid/frontend
npm install && npm run dev
```

---

## 📚 References

1. Wen et al., *"Multi-Agent Reinforcement Learning is a Sequence Modeling Problem"*, **NeurIPS 2022**. [arXiv:2205.14953](https://arxiv.org/abs/2205.14953)
2. Rashid et al., *"Monotonic Value Function Factorisation for Deep Multi-Agent RL"*, **ICML 2020**. [arXiv:2003.08839](https://arxiv.org/abs/2003.08839)
3. Yu et al., *"The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games"*, **NeurIPS 2022**. [arXiv:2103.01955](https://arxiv.org/abs/2103.01955)
4. Schulman et al., *"Proximal Policy Optimization Algorithms"*, **2017**. [arXiv:1707.06347](https://arxiv.org/abs/1707.06347)

---

## 📄 Documentation

| Document | Description |
|---|---|
| [Execution Roadmap](docs/nexus-grid-execution-roadmap.md) | Phase-by-phase engineering execution plan |
| [Architecture Diagram](docs/nexus-grid-architecture-mermaid.md) | Full system architecture (Mermaid) |
| [Deployment Guide](docs/render-deployment.md) | Render cloud deployment instructions |

---

## 🛡 License

MIT — Built for **AlgoFest Hackathon 2026**.
