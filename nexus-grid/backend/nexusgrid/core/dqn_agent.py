"""
NEXUS GRID - Deep Q-Network (DQN) Agent
A lightweight neural policy for battery dispatch that can be trained offline
and loaded at runtime through the model registry.
"""

from __future__ import annotations

import json
import math
import random
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.optim as optim

from nexusgrid.core.model_registry import (
    LEGACY_WEIGHTS_PATH,
    build_metadata,
    checkpoint_path,
    ensure_model_dir,
    metadata_path,
)


ACTIONS = [-1.0, -0.5, 0.0, 0.5, 1.0]
N_ACTIONS = len(ACTIONS)
STATE_FEATURES_PER_BUILDING = 5


class QNetwork(nn.Module):
    """Tiny MLP that maps a per-building state to action Q-values."""

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


class DQNAgent:
    """Independent per-building DQN controller."""

    GAMMA = 0.97
    LR = 3e-4
    BATCH_SIZE = 64
    EPSILON_START = 1.0
    EPSILON_END = 0.05
    EPSILON_DECAY = 0.995
    TARGET_UPDATE = 10
    MIN_BUFFER = 256

    def __init__(self, n_buildings: int):
        self.n_buildings = n_buildings
        self._state_dim = STATE_FEATURES_PER_BUILDING
        self._q_nets = [QNetwork(self._state_dim, N_ACTIONS) for _ in range(n_buildings)]
        self._target_nets = [QNetwork(self._state_dim, N_ACTIONS) for _ in range(n_buildings)]
        self._optimizers = [optim.Adam(q.parameters(), lr=self.LR) for q in self._q_nets]
        self._buffers = [ReplayBuffer() for _ in range(n_buildings)]

        for i in range(n_buildings):
            self._target_nets[i].load_state_dict(self._q_nets[i].state_dict())
            self._target_nets[i].eval()

        self._epsilon = self.EPSILON_START
        self._episode = 0
        self._trained = False
        self.reward_history: List[float] = []

    def _build_state(self, building: dict, carbon: float, hour: int) -> List[float]:
        soc = float(building.get("battery_soc", 0.5))
        solar_norm = min(float(building.get("solar_generation", 0.0)) / 10.0, 1.0)
        carbon_norm = min(carbon / 0.8, 1.0)
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        return [soc, solar_norm, carbon_norm, hour_sin, hour_cos]

    def _compute_reward(self, building: dict, carbon: float) -> float:
        p2p_earned = float(building.get("nexus_tokens_earned", 0.0))
        grid_exchange = float(building.get("grid_exchanged_kwh", 0.0))
        soc = float(building.get("battery_soc", 0.5))

        grid_carbon_cost = max(0.0, grid_exchange) * carbon * 0.5
        soc_health = -abs(soc - 0.5) * 0.5
        return float(p2p_earned - grid_carbon_cost + soc_health)

    def _restore_checkpoint(self, checkpoint: Dict) -> bool:
        if checkpoint.get("n_buildings") != self.n_buildings:
            return False

        for i, state_dict in enumerate(checkpoint["state_dicts"]):
            self._q_nets[i].load_state_dict(state_dict)
            self._target_nets[i].load_state_dict(state_dict)

        self.reward_history = checkpoint.get("reward_history", [])
        self._epsilon = checkpoint.get("epsilon", self.EPSILON_END)
        self._episode = checkpoint.get("episode", 0)
        self._trained = True
        return True

    def _load_checkpoint_file(self, path: Path) -> Optional[Dict]:
        if not path.exists():
            return None

        try:
            return torch.load(path, map_location="cpu", weights_only=True)
        except TypeError:
            return torch.load(path, map_location="cpu")
        except Exception as exc:
            print(f"[DQN] Failed to load checkpoint from {path}: {exc}")
            return None

    def decide(
        self,
        buildings: List[dict],
        carbon: float,
        hour: int,
        forecast_scenario: Optional[str] = None,
        explore: bool = False,
    ) -> List[float]:
        actions = []
        for i, building in enumerate(buildings):
            if building.get("is_ev_away", False):
                actions.append(0.0)
                continue

            if forecast_scenario:
                soc = float(building.get("battery_soc", 0.5))
                actions.append(1.0 if soc < 0.95 else 0.0)
                continue

            state = self._build_state(building, carbon, hour)
            if explore and random.random() < self._epsilon:
                action_idx = random.randint(0, N_ACTIONS - 1)
            else:
                with torch.no_grad():
                    state_tensor = torch.tensor([state], dtype=torch.float32)
                    action_idx = self._q_nets[i](state_tensor).argmax(dim=1).item()

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
        for i in range(self.n_buildings):
            if i >= len(buildings_before) or i >= len(buildings_after):
                continue

            state = self._build_state(buildings_before[i], carbon, hour)
            next_state = self._build_state(buildings_after[i], carbon, (hour + 1) % 24)
            reward = self._compute_reward(buildings_after[i], carbon)
            self._buffers[i].push(state, action_indices[i], reward, next_state, float(done))

    def learn(self) -> Optional[float]:
        total_loss = 0.0
        n_updated = 0

        for i in range(self.n_buildings):
            buffer = self._buffers[i]
            if len(buffer) < self.MIN_BUFFER:
                continue

            states, actions, rewards, next_states, dones = buffer.sample(self.BATCH_SIZE)
            q_values = self._q_nets[i](states).gather(1, actions.unsqueeze(1)).squeeze(1)

            with torch.no_grad():
                next_q = self._target_nets[i](next_states).max(1)[0]
                targets = rewards + self.GAMMA * next_q * (1 - dones)

            loss = nn.functional.smooth_l1_loss(q_values, targets)
            self._optimizers[i].zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(self._q_nets[i].parameters(), 1.0)
            self._optimizers[i].step()

            total_loss += loss.item()
            n_updated += 1

        return total_loss / n_updated if n_updated > 0 else None

    def end_episode(self, episode_reward: float):
        self.reward_history.append(episode_reward)
        self._epsilon = max(self.EPSILON_END, self._epsilon * self.EPSILON_DECAY)
        self._episode += 1

        if self._episode % self.TARGET_UPDATE == 0:
            for i in range(self.n_buildings):
                self._target_nets[i].load_state_dict(self._q_nets[i].state_dict())

    def save(self, model_id: str = "default-demo", extra_metadata: Optional[Dict] = None):
        ensure_model_dir(model_id)
        checkpoint = {
            "n_buildings": self.n_buildings,
            "state_dicts": [net.state_dict() for net in self._q_nets],
            "reward_history": self.reward_history,
            "epsilon": self._epsilon,
            "episode": self._episode,
        }

        checkpoint_file = checkpoint_path(model_id)
        metadata_file = metadata_path(model_id)
        metadata = build_metadata(model_id, self.n_buildings, extra=extra_metadata)

        torch.save(checkpoint, checkpoint_file)
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"[DQN] Saved checkpoint to {checkpoint_file}")

    def load(self, model_id: str = "default-demo", allow_legacy: bool = True) -> bool:
        registry_checkpoint = self._load_checkpoint_file(checkpoint_path(model_id))
        if registry_checkpoint and self._restore_checkpoint(registry_checkpoint):
            print(f"[DQN] Loaded checkpoint '{model_id}' (episode {self._episode})")
            return True

        if allow_legacy:
            legacy_checkpoint = self._load_checkpoint_file(LEGACY_WEIGHTS_PATH)
            if legacy_checkpoint and self._restore_checkpoint(legacy_checkpoint):
                print(f"[DQN] Loaded legacy checkpoint from {LEGACY_WEIGHTS_PATH}")
                return True

        return False

    def explain(
        self,
        buildings: List[dict],
        carbon: float,
        actions: List[float],
        forecast_scenario: Optional[str] = None,
    ) -> List[str]:
        rationales = []
        for i, building in enumerate(buildings):
            if building.get("is_ev_away", False):
                rationales.append("Mobile asset (EV) is away driving and disconnected from the grid.")
                continue

            soc = float(building.get("battery_soc", 0.5))
            solar = float(building.get("solar_generation", 0.0))
            action = actions[i] if i < len(actions) else 0.0
            p2p = abs(building.get("p2p_traded_kwh", 0.0))
            p2p_str = f" | P2P: {p2p:.2f} kWh traded" if p2p > 0 else ""

            state = self._build_state(building, carbon, 0)
            with torch.no_grad():
                q_values = self._q_nets[i](torch.tensor([state], dtype=torch.float32))[0]
                q_str = f" [Q: {q_values.max().item():.3f}]"

            if forecast_scenario and action > 0:
                rationales.append(
                    f"PRE-COGNITION OVERRIDE - Stockpiling for {forecast_scenario}. "
                    f"SoC: {int(soc * 100)}%."
                )
            elif action >= 0.8:
                rationales.append(
                    f"DQN -> CHARGE MAX - Solar: {solar:.1f} kWh. "
                    f"Battery: {int(soc * 100)}%.{p2p_str}{q_str}"
                )
            elif action >= 0.3:
                rationales.append(
                    f"DQN -> Charge - Moderate solar or low SoC hedge. "
                    f"Battery: {int(soc * 100)}%.{q_str}"
                )
            elif action <= -0.8:
                building_type = building.get("type", "residential")
                source = "V2G EV" if building_type == "ev" else "Battery"
                rationales.append(
                    f"DQN -> DISCHARGE MAX ({source}) - Grid carbon {carbon:.3f} kgCO2/kWh."
                    f"{p2p_str}{q_str}"
                )
            elif action <= -0.3:
                rationales.append(
                    f"DQN -> Discharge - Carbon arbitrage. Selling stored energy."
                    f"{p2p_str}{q_str}"
                )
            else:
                rationales.append(
                    f"DQN -> Idle - No clear arbitrage opportunity. SoC: {int(soc * 100)}%. "
                    f"Carbon: {carbon:.3f}.{q_str}"
                )

        return rationales
