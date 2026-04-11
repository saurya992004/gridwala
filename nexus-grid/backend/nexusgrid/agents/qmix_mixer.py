"""
NEXUS GRID — QMIX Monotonic Value Decomposition Network
=========================================================

Implements the QMIX mixing network for cooperative multi-agent credit
assignment in the NEXUS GRID energy digital twin.

Problem Statement
-----------------
In a multi-agent grid with n DER nodes, each agent i selects action aᵢ
based on its local observation oᵢ.  The joint action-value function
Q_tot(τ, a) must be factored into per-agent utilities Qᵢ(τᵢ, aᵢ) such
that:

    argmax_a Q_tot(τ, a) = (argmax_{a₁} Q₁, …, argmax_{aₙ} Qₙ)

This **Individual-Global-Max (IGM)** property ensures decentralized
execution: each agent can greedily maximize its own Qᵢ while jointly
maximizing Q_tot.

QMIX Monotonicity Constraint
-----------------------------
QMIX enforces IGM by ensuring the mixing function is **monotonic** in
each Qᵢ:

    ∂Q_tot / ∂Qᵢ ≥ 0    ∀ i

This is achieved by constraining the weights of the mixing network to be
**non-negative** (via absolute-value of hypernetwork outputs).

Architecture
------------
1. **Agent Networks** compute local utilities:
        Qᵢ(oᵢ, aᵢ; θᵢ) = MLP(oᵢ)[aᵢ]

2. **Hypernetworks** generate state-dependent mixing weights:
        W₁ = |HyperNet₁(s)|     ∈ ℝ^{n × d_mix}
        b₁ = HyperNet_b₁(s)     ∈ ℝ^{d_mix}
        W₂ = |HyperNet₂(s)|     ∈ ℝ^{d_mix × 1}
        b₂ = HyperNet_b₂(s)     ∈ ℝ^{1}

   The absolute value |·| ensures non-negative weights → monotonicity.

3. **Mixing Network** computes Q_tot:
        Q_tot = W₂ᵀ · ELU(W₁ᵀ · [Q₁, …, Qₙ] + b₁) + b₂

Loss Function
-------------
    L(θ) = 𝔼[(y_tot - Q_tot(τ, a; θ))²]

    where y_tot = r + γ · max_a' Q_tot(τ', a'; θ⁻)   (target network)

Reference
---------
    Rashid et al., "Monotonic Value Function Factorisation for Deep
    Multi-Agent Reinforcement Learning", ICML 2020.
    https://arxiv.org/abs/2003.08839

    (Original QMIX: Rashid et al., ICML 2018)

Author: NEXUS GRID Team — AlgoFest 2026
License: MIT
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Hypernetwork — generates state-conditioned mixing weights
# ---------------------------------------------------------------------------
class HyperNetwork(nn.Module):
    """
    Generates mixing-network weights conditioned on the global state.

    Maps the global state vector s ∈ ℝ^{state_dim} to a weight matrix
    W ∈ ℝ^{input_dim × output_dim}.

    The output is passed through |·| (absolute value) to enforce the
    monotonicity constraint:  ∂Q_tot / ∂Qᵢ ≥ 0.
    """

    def __init__(self, state_dim: int, output_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state)


# ---------------------------------------------------------------------------
# Per-Agent Q-Network (local utility function)
# ---------------------------------------------------------------------------
class AgentQNetwork(nn.Module):
    """
    Local utility network for agent i.

    Computes Qᵢ(oᵢ, ·) ∈ ℝ^{n_actions} from the agent's local
    observation.  Architecture:

        oᵢ → Linear(obs_dim, 128) → ReLU → GRU(128)
            → Linear(128, n_actions)

    The GRU provides temporal context over the agent's observation
    history, critical for partially observable grid environments.
    """

    def __init__(self, obs_dim: int, n_actions: int, hidden_dim: int = 128):
        super().__init__()
        self.hidden_dim = hidden_dim

        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        self.q_head = nn.Linear(hidden_dim, n_actions)

    def forward(
        self,
        obs: torch.Tensor,
        hidden: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Parameters
        ----------
        obs : (batch, obs_dim)
        hidden : (batch, hidden_dim) or None

        Returns
        -------
        q_values : (batch, n_actions)
        new_hidden : (batch, hidden_dim)
        """
        x = F.relu(self.fc1(obs))

        if hidden is None:
            hidden = torch.zeros(obs.size(0), self.hidden_dim, device=obs.device)

        h = self.gru(x, hidden)
        q_values = self.q_head(h)
        return q_values, h


# ---------------------------------------------------------------------------
# QMIX Mixing Network
# ---------------------------------------------------------------------------
class QMIXMixingNetwork(nn.Module):
    """
    QMIX Mixing Network for cooperative value decomposition.

    Given per-agent utilities Q₁, …, Qₙ and global state s, computes:

        Q_tot = f_mix(Q₁, …, Qₙ; s)

    subject to the monotonicity constraint ∂Q_tot/∂Qᵢ ≥ 0 ∀i.

    The mixing function is parameterised by hypernetworks that take the
    global state as input and produce non-negative weights:

        hidden = ELU(|W₁(s)| · [Q₁, …, Qₙ]ᵀ + b₁(s))
        Q_tot  = |W₂(s)| · hidden + b₂(s)

    Parameters
    ----------
    n_agents : int
        Number of grid agents (DER nodes).
    state_dim : int
        Global state vector dimensionality.
    mixing_dim : int
        Hidden dimension of the mixing network.
    obs_dim : int
        Per-agent observation dimensionality.
    n_actions : int
        Discrete action space size.
    """

    def __init__(
        self,
        n_agents: int,
        state_dim: int = 32,
        mixing_dim: int = 32,
        obs_dim: int = 5,
        n_actions: int = 5,
    ):
        super().__init__()
        self.n_agents = n_agents
        self.state_dim = state_dim
        self.mixing_dim = mixing_dim
        self.obs_dim = obs_dim
        self.n_actions = n_actions

        # ---------- Per-Agent Q-Networks ----------
        # Each agent has an independent utility network with GRU memory
        self.agent_networks = nn.ModuleList(
            [AgentQNetwork(obs_dim, n_actions) for _ in range(n_agents)]
        )

        # ---------- Global State Encoder ----------
        # Compresses joint observation into a global state representation
        # s = f(o₁, o₂, …, oₙ) ∈ ℝ^{state_dim}
        self.state_encoder = nn.Sequential(
            nn.Linear(n_agents * obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, state_dim),
        )

        # ---------- Hypernetworks for Mixing Weights ----------
        # W₁(s) ∈ ℝ^{n_agents × mixing_dim}
        self.hyper_w1 = HyperNetwork(state_dim, n_agents * mixing_dim)
        # b₁(s) ∈ ℝ^{mixing_dim}
        self.hyper_b1 = nn.Linear(state_dim, mixing_dim)
        # W₂(s) ∈ ℝ^{mixing_dim × 1}
        self.hyper_w2 = HyperNetwork(state_dim, mixing_dim)
        # b₂(s) ∈ ℝ^{1}  — final bias (two-layer hypernetwork for expressivity)
        self.hyper_b2 = nn.Sequential(
            nn.Linear(state_dim, mixing_dim),
            nn.ReLU(),
            nn.Linear(mixing_dim, 1),
        )

    def forward(
        self,
        agent_qs: torch.Tensor,
        global_state: torch.Tensor,
    ) -> torch.Tensor:
        """
        Mix per-agent Q-values into Q_tot using state-conditioned weights.

        Parameters
        ----------
        agent_qs : torch.Tensor
            Shape (batch, n_agents). The chosen-action Q-values from each
            agent's local utility network.
        global_state : torch.Tensor
            Shape (batch, state_dim). Encoded global state.

        Returns
        -------
        q_tot : torch.Tensor
            Shape (batch, 1). Joint action-value estimate.
        """
        batch_size = agent_qs.size(0)

        # ---- Generate mixing weights via hypernetworks ----
        # Absolute value enforces monotonicity: ∂Q_tot / ∂Qᵢ ≥ 0
        w1 = torch.abs(self.hyper_w1(global_state))         # (batch, n_agents * mixing_dim)
        w1 = w1.view(batch_size, self.n_agents, self.mixing_dim)
        b1 = self.hyper_b1(global_state)                    # (batch, mixing_dim)

        w2 = torch.abs(self.hyper_w2(global_state))         # (batch, mixing_dim)
        w2 = w2.view(batch_size, self.mixing_dim, 1)
        b2 = self.hyper_b2(global_state)                    # (batch, 1)

        # ---- Mixing forward pass ----
        # agent_qs: (batch, 1, n_agents) @ w1: (batch, n_agents, mix) → (batch, 1, mix)
        agent_qs_reshaped = agent_qs.unsqueeze(1)           # (batch, 1, n_agents)
        hidden = torch.bmm(agent_qs_reshaped, w1)           # (batch, 1, mixing_dim)
        hidden = hidden.squeeze(1) + b1                     # (batch, mixing_dim)
        hidden = F.elu(hidden)

        # (batch, 1, mixing_dim) @ (batch, mixing_dim, 1) → (batch, 1, 1)
        q_tot = torch.bmm(hidden.unsqueeze(1), w2)          # (batch, 1, 1)
        q_tot = q_tot.squeeze(-1) + b2                      # (batch, 1)

        return q_tot

    def get_agent_qs(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        hidden_states: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute per-agent Q-values for chosen actions.

        Parameters
        ----------
        observations : (batch, n_agents, obs_dim)
        actions : (batch, n_agents) — long tensor of action indices
        hidden_states : (batch, n_agents, hidden_dim) or None

        Returns
        -------
        chosen_qs : (batch, n_agents)
        new_hiddens : (batch, n_agents, hidden_dim)
        """
        batch_size = observations.size(0)
        chosen_qs = []
        new_hiddens = []

        for i, agent_net in enumerate(self.agent_networks):
            obs_i = observations[:, i, :]                    # (batch, obs_dim)
            h_i = hidden_states[:, i, :] if hidden_states is not None else None
            q_vals, h_new = agent_net(obs_i, h_i)            # (batch, n_actions), (batch, hidden)

            # Index the Q-value for the taken action
            action_i = actions[:, i].unsqueeze(1)            # (batch, 1)
            q_chosen = q_vals.gather(1, action_i).squeeze(1) # (batch,)

            chosen_qs.append(q_chosen)
            new_hiddens.append(h_new)

        chosen_qs = torch.stack(chosen_qs, dim=1)            # (batch, n_agents)
        new_hiddens = torch.stack(new_hiddens, dim=1)        # (batch, n_agents, hidden)

        return chosen_qs, new_hiddens

    def compute_q_tot(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        hidden_states: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        End-to-end: observations + actions → Q_tot.

        This is the primary interface for training:
            1. Compute per-agent Qᵢ via agent networks
            2. Encode global state from joint observations
            3. Mix via QMIX to get Q_tot

        Returns
        -------
        q_tot : (batch, 1)
        new_hiddens : (batch, n_agents, hidden_dim)
        """
        # Step 1: Per-agent Q-values
        agent_qs, new_hiddens = self.get_agent_qs(
            observations, actions, hidden_states
        )

        # Step 2: Encode global state
        batch_size = observations.size(0)
        flat_obs = observations.view(batch_size, -1)         # (batch, n_agents * obs_dim)
        global_state = self.state_encoder(flat_obs)          # (batch, state_dim)

        # Step 3: QMIX mixing
        q_tot = self.forward(agent_qs, global_state)         # (batch, 1)

        return q_tot, new_hiddens

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def __repr__(self) -> str:
        n_params = self.count_parameters()
        return (
            f"QMIXMixingNetwork(\n"
            f"  n_agents={self.n_agents}, state_dim={self.state_dim}, "
            f"mixing_dim={self.mixing_dim},\n"
            f"  obs_dim={self.obs_dim}, n_actions={self.n_actions},\n"
            f"  trainable_params={n_params:,}\n"
            f")"
        )
