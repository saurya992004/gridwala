"""
NEXUS GRID — DQN Offline Training Script
Run this script ONCE to train the agents for N episodes and save weights.

Usage:
    python train_dqn.py
    python train_dqn.py --episodes 200 --preset residential_district

The trained weights are saved to nexusgrid/core/dqn_weights.pt
and automatically loaded by the live server when it starts.
"""

import argparse
import json
import os
import sys
import time

# Add backend root to sys.path so we can import nexusgrid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexusgrid.core.environment import NexusGridEnv
from nexusgrid.core.dqn_agent import DQNAgent, ACTIONS, N_ACTIONS


def get_schema(preset_id: str):
    """Load a preset schema from configs directory."""
    configs_dir = os.path.join(os.path.dirname(__file__), "nexusgrid", "configs")
    path = os.path.join(configs_dir, f"{preset_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def action_to_idx(action_val: float) -> int:
    """Find the closest action index for a given continuous value."""
    return min(range(N_ACTIONS), key=lambda i: abs(ACTIONS[i] - action_val))


def train(episodes: int = 100, preset: str = "residential_district", steps_per_episode: int = 168):
    """
    Main training loop.

    Args:
        episodes: Number of full training runs.
        preset: District schema to train on.
        steps_per_episode: Hours to simulate per episode (168 = 1 week).
    """
    print(f"\n{'='*60}")
    print(f"  NEXUS GRID — DQN Training")
    print(f"  Preset: {preset} | Episodes: {episodes} | Steps/episode: {steps_per_episode}")
    print(f"{'='*60}\n")

    schema = get_schema(preset)
    env = NexusGridEnv(schema=schema)
    n_buildings = env.n_buildings

    agent = DQNAgent(n_buildings=n_buildings)

    # Try to resume from checkpoint
    resumed = agent.load()
    if resumed:
        start_ep = agent._episode
        print(f"[Train] Resuming from episode {start_ep}")
    else:
        start_ep = 0
        print(f"[Train] Starting fresh training with {n_buildings} building agents")

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

            # Agent selects actions (explore=True during training)
            if last_payload:
                actions = agent.decide(
                    buildings=last_payload["buildings"],
                    carbon=last_payload["carbon_intensity"],
                    hour=hour,
                    explore=True,
                )
                action_indices = [action_to_idx(a) for a in actions]
                buildings_before = last_payload["buildings"]
            else:
                actions = [0.0] * n_buildings
                action_indices = [2] * n_buildings
                buildings_before = None

            # Step environment
            payload = env.step(actions)
            carbon = payload["carbon_intensity"]
            buildings_after = payload["buildings"]

            # Collect step reward (sum across all buildings)
            step_reward = sum(
                b.get("nexus_tokens_earned", 0.0) for b in buildings_after
            )
            episode_reward += step_reward

            # Store experience
            if buildings_before is not None:
                agent.store_transition(
                    buildings_before=buildings_before,
                    action_indices=action_indices,
                    buildings_after=buildings_after,
                    carbon=carbon,
                    hour=hour,
                    done=env.is_done,
                )

            # Learn
            loss = agent.learn()
            if loss is not None:
                episode_loss += loss
                loss_steps += 1

            last_payload = payload

        # End of episode
        agent.end_episode(episode_reward)
        avg_loss = episode_loss / loss_steps if loss_steps > 0 else 0.0

        # Log progress
        elapsed = time.time() - start_time
        if (episode - start_ep + 1) % 10 == 0 or episode == start_ep:
            print(
                f"  Ep {episode+1:4d}/{start_ep+episodes}  |  "
                f"Reward: {episode_reward:8.2f}  |  "
                f"Loss: {avg_loss:.4f}  |  "
                f"ε: {agent._epsilon:.3f}  |  "
                f"Time: {elapsed:.1f}s"
            )

        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save()  # Save immediately on new best

    # Final save
    agent.save()

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Best Episode Reward: {best_reward:.2f}")
    print(f"  Total Time: {total_time:.1f}s")
    print(f"  Final Epsilon: {agent._epsilon:.3f}")
    print(f"  Reward History saved alongside weights.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--preset", type=str, default="residential_district")
    parser.add_argument("--steps", type=int, default=168)
    args = parser.parse_args()

    train(episodes=args.episodes, preset=args.preset, steps_per_episode=args.steps)
