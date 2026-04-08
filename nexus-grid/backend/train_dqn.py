"""
NEXUS GRID - DQN offline training entrypoint.

Usage:
    python train_dqn.py
    python train_dqn.py --episodes 200 --preset residential_district
    python train_dqn.py --preset industrial_microgrid --model-id pilot-industrial-v1
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexusgrid.core.dqn_agent import ACTIONS, DQNAgent, N_ACTIONS
from nexusgrid.core.environment import NexusGridEnv
from nexusgrid.core.model_registry import resolve_model_id
from nexusgrid.core.schema_loader import load_from_file


PRESETS_DIR = Path(__file__).resolve().parent / "nexusgrid" / "presets"


def get_schema(preset_id: str):
    path = PRESETS_DIR / f"{preset_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {path}")
    return load_from_file(path)


def action_to_idx(action_val: float) -> int:
    return min(range(N_ACTIONS), key=lambda i: abs(ACTIONS[i] - action_val))


def train(
    episodes: int = 100,
    preset: str = "residential_district",
    steps_per_episode: int = 168,
    model_id: str | None = None,
):
    print(f"\n{'=' * 60}")
    print("  NEXUS GRID - DQN Training")
    print(f"  Preset: {preset} | Episodes: {episodes} | Steps/episode: {steps_per_episode}")
    print(f"{'=' * 60}\n")

    schema = get_schema(preset)
    model_id = model_id or resolve_model_id(schema=schema, preset_id=preset)

    env = NexusGridEnv(schema=schema)
    agent = DQNAgent(n_buildings=env.n_buildings)

    resumed = agent.load(model_id=model_id)
    if resumed:
        start_ep = agent._episode
        print(f"[Train] Resuming model '{model_id}' from episode {start_ep}")
    else:
        start_ep = 0
        print(f"[Train] Starting fresh training for model '{model_id}'")

    best_reward = float("-inf")
    start_time = time.time()

    for episode in range(start_ep, start_ep + episodes):
        env.reset()
        episode_reward = 0.0
        episode_loss = 0.0
        last_payload = env.last_payload
        loss_steps = 0

        for step in range(steps_per_episode):
            if env.is_done:
                break

            hour = step % 24
            if last_payload:
                actions = agent.decide(
                    buildings=last_payload["buildings"],
                    carbon=last_payload["carbon_intensity"],
                    hour=hour,
                    explore=True,
                )
                action_indices = [action_to_idx(action) for action in actions]
                buildings_before = last_payload["buildings"]
            else:
                actions = [0.0] * env.n_buildings
                action_indices = [2] * env.n_buildings
                buildings_before = None

            payload = env.step(actions)
            carbon = payload["carbon_intensity"]
            buildings_after = payload["buildings"]

            episode_reward += sum(
                building.get("nexus_tokens_earned", 0.0) for building in buildings_after
            )

            if buildings_before is not None:
                agent.store_transition(
                    buildings_before=buildings_before,
                    action_indices=action_indices,
                    buildings_after=buildings_after,
                    carbon=carbon,
                    hour=hour,
                    done=env.is_done,
                )

            loss = agent.learn()
            if loss is not None:
                episode_loss += loss
                loss_steps += 1

            last_payload = payload

        agent.end_episode(episode_reward)
        avg_loss = episode_loss / loss_steps if loss_steps > 0 else 0.0
        elapsed = time.time() - start_time

        if (episode - start_ep + 1) % 10 == 0 or episode == start_ep:
            print(
                f"  Ep {episode + 1:4d}/{start_ep + episodes}  |  "
                f"Reward: {episode_reward:8.2f}  |  "
                f"Loss: {avg_loss:.4f}  |  "
                f"Epsilon: {agent._epsilon:.3f}  |  "
                f"Time: {elapsed:.1f}s"
            )

        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save(
                model_id=model_id,
                extra_metadata={
                    "preset_id": preset,
                    "district_name": schema.get("district_name"),
                    "steps_per_episode": steps_per_episode,
                    "best_episode_reward": best_reward,
                },
            )

    agent.save(
        model_id=model_id,
        extra_metadata={
            "preset_id": preset,
            "district_name": schema.get("district_name"),
            "steps_per_episode": steps_per_episode,
            "best_episode_reward": best_reward,
        },
    )

    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print("  Training Complete!")
    print(f"  Model ID: {model_id}")
    print(f"  Best Episode Reward: {best_reward:.2f}")
    print(f"  Total Time: {total_time:.1f}s")
    print(f"  Final Epsilon: {agent._epsilon:.3f}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--preset", type=str, default="residential_district")
    parser.add_argument("--steps", type=int, default=168)
    parser.add_argument("--model-id", type=str, default=None)
    args = parser.parse_args()

    train(
        episodes=args.episodes,
        preset=args.preset,
        steps_per_episode=args.steps,
        model_id=args.model_id,
    )
