"""
NEXUS GRID — Baseline Policy Architectures
============================================

Legacy single-agent baselines retained for ablation studies and
comparative benchmarking against the primary MAT + QMIX policy stack.

Baselines:
  - DQN (Deep Q-Network): Independent per-node value-based controller.
    Vanilla DQN has no inter-agent communication and treats each prosumer
    as an isolated MDP — useful as a lower-bound performance reference.

See ``nexusgrid.agents`` for the primary multi-agent architectures.
"""
