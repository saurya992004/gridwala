"""
NEXUS GRID — Deep Q-Network (DQN) Agent
A real neural network that LEARNS to optimise battery dispatch.

Architecture:
  - State vector: [soc, solar_norm, carbon_norm, hour_sin, hour_cos] per building
  - Action space: 5 discrete actions per building
      0: Discharge full  (-1.0)
      1: Discharge half  (-0.5)
      2: Idle            ( 0.0)
      3: Charge half     (+0.5)
      4: Charge full     (+1.0)
  - Reward: based on P2P savings, carbon avoidance, and battery health

The DQN is TRAINED offline (100 episodes) and then its weights are used
for live inference during the WebSocket simulation stream.
"""

import random
import math
import json
import os
from collections import deque
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np


# ---------------------------------------------------------------------------
# Action mapping
# ---------------------------------------------------------------------------
ACTIONS = [-1.0, -0.5, 0.0, 0.5, 1.0]  # Continuous action values
N_ACTIONS = len(ACTIONS)

# State features per building
STATE_FEATURES_PER_BUILDING = 5  # [soc, solar_norm, carbon_norm, hour_sin, hour_cos]

# Where to save trained weights
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "dqn_weights.pt")


# ---------------------------------------------------------------------------
# Neural Network
# ---------------------------------------------------------------------------
class QNetwork(nn.Module):
    """
    A simple 3-layer MLP that maps per-building state → Q-values for each action.
    Tiny network — trains in seconds on CPU.
    """
    def __init__(self, state_dim: int, n_actions: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------------
# Replay Buffer
# ---------------------------------------------------------------------------
class ReplayBuffer:
    def __init__(self, capacity: int = 10_000):
        self._buf = deque(maxlen=capacity)

    def push(self, state, action_idx, reward, next_state, done):
        self._buf.append((state, action_idx, reward, next_state, done))

    def sample(self, batch_size: int):
        batch = random.sample(self._buf, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.tensor(states, dtype=torch.float32),
            torch.tensor(actions, dtype=torch.long),
            torch.tensor(rewards, dtype=torch.float32),
            torch.tensor(next_states, dtype=torch.float32),
            torch.tensor(dones, dtype=torch.float32),
        )

    def __len__(self):
        return len(self._buf)


# ---------------------------------------------------------------------------
# DQN Agent
# ---------------------------------------------------------------------------
class DQNAgent:
    """
    Per-building Deep Q-Network agent.

    Each building has its own Q-network.
    Agents share the same hyperparameters but learn independently.
    """

    # Hyperparameters (tuned for fast CPU training)
    GAMMA = 0.97          # Discount factor
    LR = 3e-4             # Learning rate
    BATCH_SIZE = 64
    EPSILON_START = 1.0   # Start fully random
    EPSILON_END = 0.05    # End at 5% random
    EPSILON_DECAY = 0.995 # Per-episode decay
    TARGET_UPDATE = 10    # Sync target net every N episodes
    MIN_BUFFER = 256      # Minimum samples before training starts

    def __init__(self, n_buildings: int):
        self.n_buildings = n_buildings
        self._state_dim = STATE_FEATURES_PER_BUILDING  # Per-building state

        # One Q-network per building (independent agents)
        self._q_nets = [QNetwork(self._state_dim, N_ACTIONS) for _ in range(n_buildings)]
        self._target_nets = [QNetwork(self._state_dim, N_ACTIONS) for _ in range(n_buildings)]
        self._optimizers = [optim.Adam(q.parameters(), lr=self.LR) for q in self._q_nets]
        self._buffers = [ReplayBuffer() for _ in range(n_buildings)]
        
        # Sync target networks
        for i in range(n_buildings):
            self._target_nets[i].load_state_dict(self._q_nets[i].state_dict())
            self._target_nets[i].eval()

        self._epsilon = self.EPSILON_START
        self._episode = 0
        self._trained = False

        # Track per-episode reward for plotting
        self.reward_history: List[float] = []

    def _build_state(self, b: dict, carbon: float, hour: int) -> List[float]:
        """Convert a building payload dict into a flat normalised state vector."""
        soc = float(b.get("battery_soc", 0.5))
        solar_norm = min(float(b.get("solar_generation", 0.0)) / 10.0, 1.0)
        carbon_norm = min(carbon / 0.8, 1.0)
        # Encode hour cyclically so model understands 23:00 → 00:00 continuity
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        return [soc, solar_norm, carbon_norm, hour_sin, hour_cos]

    def _compute_reward(self, b: dict, carbon: float) -> float:
        """
        Shape the reward signal to teach the agent:
        1. Maximize P2P revenue (selling surplus is good)
        2. Penalize buying dirty grid power
        3. Reward balanced battery SoC
        4. Penalize battery being empty or completely full (degradation)
        """
        net = float(b.get("net_electricity_consumption", 0.0))
        soc = float(b.get("battery_soc", 0.5))
        p2p_earned = float(b.get("nexus_tokens_earned", 0.0))

        # Carbon-weighted grid cost penalty
        grid_exchange = float(b.get("grid_exchanged_kwh", 0.0))
        grid_carbon_cost = max(0.0, grid_exchange) * carbon * 0.5

        # SoC health reward (prefer 20-80% range)
        soc_health = -abs(soc - 0.5) * 0.5  

        # Net reward
        reward = p2p_earned - grid_carbon_cost + soc_health
        return float(reward)

    def decide(
        self,
        buildings: List[dict],
        carbon: float,
        hour: int,
        forecast_scenario: Optional[str] = None,
        explore: bool = False,
    ) -> List[float]:
        """
        Select one action per building using epsilon-greedy DQN policy.
        Falls back to Pre-Cognition override for forecast emergencies.
        """
        actions = []
        for i, b in enumerate(buildings):
            # EV away: always idle
            if b.get("is_ev_away", False):
                actions.append(0.0)
                continue

            # Pre-Cognition override (deterministic, overrides RL)
            if forecast_scenario:
                soc = float(b.get("battery_soc", 0.5))
                actions.append(1.0 if soc < 0.95 else 0.0)
                continue

            state = self._build_state(b, carbon, hour)

            # Epsilon-greedy during training, greedy during inference
            if explore and random.random() < self._epsilon:
                action_idx = random.randint(0, N_ACTIONS - 1)
            else:
                with torch.no_grad():
                    state_t = torch.tensor([state], dtype=torch.float32)
                    q_values = self._q_nets[i](state_t)
                    action_idx = q_values.argmax(dim=1).item()

            actions.append(ACTIONS[action_idx])
        return actions

    def store_transition(
        self,
        buildings_before: List[dict],
        action_indices: List[int],
        buildings_after: List[dict],
        carbon: float,
        hour: int,
        done: bool,
    ):
        """Push one step of experience into each building's replay buffer."""
        for i in range(self.n_buildings):
            if i >= len(buildings_before) or i >= len(buildings_after):
                continue
            state = self._build_state(buildings_before[i], carbon, hour)
            next_state = self._build_state(buildings_after[i], carbon, (hour + 1) % 24)
            reward = self._compute_reward(buildings_after[i], carbon)
            self._buffers[i].push(state, action_indices[i], reward, next_state, float(done))

    def learn(self) -> Optional[float]:
        """Run one gradient update step per building. Returns mean loss."""
        total_loss = 0.0
        n_updated = 0

        for i in range(self.n_buildings):
            buf = self._buffers[i]
            if len(buf) < self.MIN_BUFFER:
                continue

            states, actions, rewards, next_states, dones = buf.sample(self.BATCH_SIZE)

            # Current Q-values
            q_values = self._q_nets[i](states).gather(1, actions.unsqueeze(1)).squeeze(1)

            # Target Q-values (double DQN style)
            with torch.no_grad():
                next_q = self._target_nets[i](next_states).max(1)[0]
                targets = rewards + self.GAMMA * next_q * (1 - dones)

            loss = nn.functional.smooth_l1_loss(q_values, targets)
            self._optimizers[i].zero_grad()
            loss.backward()
            # Gradient clipping for stability
            nn.utils.clip_grad_norm_(self._q_nets[i].parameters(), 1.0)
            self._optimizers[i].step()

            total_loss += loss.item()
            n_updated += 1

        return total_loss / n_updated if n_updated > 0 else None

    def end_episode(self, episode_reward: float):
        """Called at end of each training episode."""
        self.reward_history.append(episode_reward)
        self._epsilon = max(self.EPSILON_END, self._epsilon * self.EPSILON_DECAY)
        self._episode += 1

        if self._episode % self.TARGET_UPDATE == 0:
            for i in range(self.n_buildings):
                self._target_nets[i].load_state_dict(self._q_nets[i].state_dict())

    def save(self, path: str = WEIGHTS_PATH):
        """Save all Q-network weights to disk."""
        state_dicts = [net.state_dict() for net in self._q_nets]
        torch.save({
            "n_buildings": self.n_buildings,
            "state_dicts": state_dicts,
            "reward_history": self.reward_history,
            "epsilon": self._epsilon,
            "episode": self._episode,
        }, path)
        print(f"[DQN] Saved weights → {path}")

    def load(self, path: str = WEIGHTS_PATH) -> bool:
        """Load weights from disk. Returns True if successful."""
        if not os.path.exists(path):
            return False
        try:
            ckpt = torch.load(path, map_location="cpu", weights_only=True)
            if ckpt["n_buildings"] != self.n_buildings:
                return False
            for i, sd in enumerate(ckpt["state_dicts"]):
                self._q_nets[i].load_state_dict(sd)
                self._target_nets[i].load_state_dict(sd)
            self.reward_history = ckpt.get("reward_history", [])
            self._epsilon = ckpt.get("epsilon", self.EPSILON_END)
            self._episode = ckpt.get("episode", 0)
            self._trained = True
            print(f"[DQN] Loaded weights from {path} (episode {self._episode})")
            return True
        except Exception as e:
            print(f"[DQN] Load failed: {e}")
            return False

    def explain(
        self,
        buildings: List[dict],
        carbon: float,
        actions: List[float],
        forecast_scenario: Optional[str] = None,
    ) -> List[str]:
        """Generate XAI rationales for the frontend log stream."""
        rationales = []
        for i, b in enumerate(buildings):
            if b.get("is_ev_away", False):
                rationales.append("Mobile asset (EV) away driving. Disconnected from grid.")
                continue

            soc = float(b.get("battery_soc", 0.5))
            solar = float(b.get("solar_generation", 0.0))
            action = actions[i] if i < len(actions) else 0.0
            p2p = abs(b.get("p2p_traded_kwh", 0.0))
            p2p_str = f" | P2P: {p2p:.2f} kWh traded" if p2p > 0 else ""
            
            # Get Q-values for XAI transparency
            state = self._build_state(b, carbon, 0)
            with torch.no_grad():
                q_vals = self._q_nets[i](torch.tensor([state], dtype=torch.float32))[0]
                q_str = f" [Q: {q_vals.max().item():.3f}]"

            if forecast_scenario and action > 0:
                rationales.append(f"🚨 PRE-COGNITION OVERRIDE — Stockpiling for {forecast_scenario}. SoC: {int(soc*100)}%.")
            elif action >= 0.8:
                rationales.append(f"⚡ DQN→CHARGE MAX — Solar: {solar:.1f} kWh. Battery: {int(soc*100)}%.{p2p_str}{q_str}")
            elif action >= 0.3:
                rationales.append(f"DQN→Charge — Moderate solar or low SoC hedge. Battery: {int(soc*100)}%.{q_str}")
            elif action <= -0.8:
                b_type = b.get("type", "residential")
                src = "V2G EV" if b_type == "ev" else "Battery"
                rationales.append(f"⚡ DQN→DISCHARGE MAX ({src}) — Grid carbon {carbon:.3f} kgCO₂/kWh.{p2p_str}{q_str}")
            elif action <= -0.3:
                rationales.append(f"DQN→Discharge — Carbon arbitrage. Selling stored energy.{p2p_str}{q_str}")
            else:
                rationales.append(f"DQN→Idle — No clear arbitrage opportunity. SoC: {int(soc*100)}%. Carbon: {carbon:.3f}.{q_str}")

        return rationales
