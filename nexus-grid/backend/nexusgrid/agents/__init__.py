"""
NEXUS GRID - Multi-Agent Policy Architectures
==============================================

This package implements the core MARL policy stack:
  - mat_policy:   Multi-Agent Transformer (MAT) — primary policy network
  - qmix_mixer:   QMIX monotonic value decomposition — cooperative credit assignment
  - baselines/:   Legacy single-agent baselines (DQN) for ablation comparison

Architecture reference:
  Wen et al., "Multi-Agent Reinforcement Learning is a Sequence Modeling Problem" (NeurIPS 2022)
  Rashid et al., "Monotonic Value Function Factorisation for Deep Multi-Agent RL" (ICML 2020)
"""

from nexusgrid.agents.mat_policy import MultiAgentTransformer
from nexusgrid.agents.qmix_mixer import QMIXMixingNetwork

__all__ = ["MultiAgentTransformer", "QMIXMixingNetwork"]
