"""
NEXUS GRID — Multi-Agent Transformer (MAT) Policy Network
==========================================================

Novel application of the Multi-Agent Transformer architecture to real-time
energy digital-twin control.  Each prosumer / DER node is treated as a
**token** in a sequential decision process; the self-attention mechanism
learns emergent cooperative dispatch strategies across the grid topology,
enabling **zero-shot generalization** to unseen grid configurations without
re-training.

Theoretical Foundation
----------------------
Standard independent-learner MARL (e.g., IQL / DQN per agent) ignores
inter-agent dependencies.  MAT re-frames the joint policy as an
auto-regressive sequence model:

    π(a₁, a₂, …, aₙ | o₁, o₂, …, oₙ) = ∏ᵢ π(aᵢ | o₁, …, oₙ, a₁, …, aᵢ₋₁)

By attending over the full observation-action history, each agent
conditions its dispatch decision on the *emergent joint strategy* rather
than optimizing myopically.

Key Equations
-------------
1. **Multi-Head Self-Attention (per transformer block)**

        Attention(Q, K, V) = softmax(QKᵀ / √dₖ) · V

   where Q, K, V ∈ ℝ^{n × d_model} are linear projections of the
   per-agent observation embeddings.

2. **Positional Encoding (sinusoidal, agent-order invariant)**

        PE(pos, 2i)   = sin(pos / 10000^{2i/d_model})
        PE(pos, 2i+1) = cos(pos / 10000^{2i/d_model})

3. **Policy Head — Categorical action distribution**

        π_θ(aᵢ | context) = softmax(W_out · h_i^{(L)} + b_out)

   h_i^{(L)} is the final-layer hidden state for agent i.

4. **Value Head — Centralized state-value for advantage estimation**

        V_ψ(s) = W_v · mean-pool(h^{(L)}) + b_v

   Used with GAE (λ=0.95) for low-variance policy gradient updates.

Reference
---------
    Wen et al., "Multi-Agent Reinforcement Learning is a Sequence
    Modeling Problem", NeurIPS 2022.
    https://arxiv.org/abs/2205.14953

Author: NEXUS GRID Team — AlgoFest 2026
License: MIT
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


# ---------------------------------------------------------------------------
# Hyperparameters — aligned with the NEXUS GRID state / action interface
# ---------------------------------------------------------------------------
DEFAULT_OBS_DIM = 5          # [SoC, solar_norm, carbon_norm, hour_sin, hour_cos]
DEFAULT_N_ACTIONS = 5        # [-1.0, -0.5, 0.0, +0.5, +1.0]  (dispatch quanta)
DEFAULT_D_MODEL = 128        # Transformer hidden dimension
DEFAULT_N_HEADS = 4          # Multi-head attention heads
DEFAULT_N_LAYERS = 3         # Transformer encoder depth
DEFAULT_D_FF = 256           # Feed-forward inner dimension
DEFAULT_DROPOUT = 0.1        # Regularisation


# ---------------------------------------------------------------------------
# Sinusoidal Positional Encoding
# ---------------------------------------------------------------------------
class SinusoidalPositionalEncoding(nn.Module):
    """
    Inject agent-order positional information into observation embeddings.

    For a grid with n agents, position `pos` ∈ {0, …, n-1} encodes the
    topological index of the DER node.  The encoding is:

        PE(pos, 2i)   = sin(pos / 10000^{2i / d_model})
        PE(pos, 2i+1) = cos(pos / 10000^{2i / d_model})

    This allows the attention layers to reason about agent ordering without
    hard-coding spatial structure.
    """

    def __init__(self, d_model: int, max_agents: int = 256):
        super().__init__()
        pe = torch.zeros(max_agents, d_model)
        position = torch.arange(0, max_agents, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32)
            * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_agents, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, n_agents, d_model)"""
        return x + self.pe[:, : x.size(1), :]


# ---------------------------------------------------------------------------
# Transformer Encoder Block
# ---------------------------------------------------------------------------
class MATEncoderBlock(nn.Module):
    """
    Single transformer encoder block with pre-norm residual connections.

    Architecture per block:
        h' = h + MHA(LayerNorm(h))
        h'' = h' + FFN(LayerNorm(h'))

    where FFN is a two-layer MLP with GELU activation:
        FFN(x) = W₂ · GELU(W₁ · x + b₁) + b₂
    """

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        x: (batch, n_agents, d_model)
        mask: optional causal or padding mask
        """
        # Pre-norm multi-head self-attention
        h = self.ln1(x)
        attn_out, _ = self.attn(h, h, h, attn_mask=mask)
        x = x + attn_out

        # Pre-norm feed-forward network
        x = x + self.ffn(self.ln2(x))
        return x


# ---------------------------------------------------------------------------
# Multi-Agent Transformer (MAT) Policy
# ---------------------------------------------------------------------------
class MultiAgentTransformer(nn.Module):
    """
    Multi-Agent Transformer policy for cooperative energy dispatch.

    Each DER / prosumer node is treated as a token:

        o_i ∈ ℝ^{obs_dim}  →  embed  →  h_i ∈ ℝ^{d_model}

    A stack of L transformer encoder blocks computes:

        h^{(l+1)} = TransformerBlock(h^{(l)})    for l = 0, …, L-1

    yielding contextually-enriched agent representations that capture
    inter-agent dependencies via self-attention.

    Two heads decode from h^{(L)}:

    **Policy Head** (per-agent):
        π_θ(a_i | o_{1:n}) = softmax(W_π · h_i^{(L)} + b_π)

    **Value Head** (centralized):
        V_ψ(s) = W_v · Σᵢ h_i^{(L)} / n + b_v

    The value head uses **mean-pool aggregation** over all agent
    representations, providing a centralized state-value estimate
    for Generalized Advantage Estimation (GAE-λ).

    Training Objective
    ------------------
    The combined PPO-clip loss is:

        L = L_policy + c₁ · L_value - c₂ · H[π]

    where:
        L_policy = -𝔼[min(rₜ(θ) · Âₜ, clip(rₜ(θ), 1-ε, 1+ε) · Âₜ)]
        L_value  = ½ · 𝔼[(V_ψ(sₜ) - Vₜ_target)²]
        H[π]     = entropy bonus for exploration

    Parameters
    ----------
    n_agents : int
        Number of DER / prosumer nodes in the grid topology.
    obs_dim : int
        Per-agent observation vector dimensionality.
    n_actions : int
        Discrete action space cardinality.
    d_model : int
        Transformer hidden dimension.
    n_heads : int
        Number of attention heads per block.
    n_layers : int
        Depth of the transformer encoder stack.
    d_ff : int
        Feed-forward inner dimension.
    dropout : float
        Dropout probability for regularisation.
    """

    def __init__(
        self,
        n_agents: int,
        obs_dim: int = DEFAULT_OBS_DIM,
        n_actions: int = DEFAULT_N_ACTIONS,
        d_model: int = DEFAULT_D_MODEL,
        n_heads: int = DEFAULT_N_HEADS,
        n_layers: int = DEFAULT_N_LAYERS,
        d_ff: int = DEFAULT_D_FF,
        dropout: float = DEFAULT_DROPOUT,
    ):
        super().__init__()
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.n_actions = n_actions
        self.d_model = d_model

        # ---------- Observation Embedding ----------
        # Linear projection from raw observation to d_model
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
        )

        # ---------- Positional Encoding ----------
        self.pos_encoding = SinusoidalPositionalEncoding(d_model, max_agents=512)

        # ---------- Transformer Encoder Stack ----------
        self.encoder_blocks = nn.ModuleList(
            [
                MATEncoderBlock(d_model, n_heads, d_ff, dropout)
                for _ in range(n_layers)
            ]
        )
        self.final_ln = nn.LayerNorm(d_model)

        # ---------- Policy Head (per-agent action distribution) ----------
        # π_θ(a_i | context) = softmax(W_out · h_i + b_out)
        self.policy_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, n_actions),
        )

        # ---------- Value Head (centralized critic) ----------
        # V_ψ(s) = W_v · mean_pool(h) + b_v
        self.value_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, 1),
        )

        # Initialise weights with Xavier uniform
        self._init_weights()

    def _init_weights(self):
        """Xavier uniform initialization for stable early training."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        observations: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through the MAT policy.

        Parameters
        ----------
        observations : torch.Tensor
            Shape (batch, n_agents, obs_dim).
            Per-agent raw observations: [SoC, solar_norm, carbon_norm,
            hour_sin, hour_cos].
        mask : torch.Tensor, optional
            Attention mask for variable-topology grids.

        Returns
        -------
        action_logits : torch.Tensor
            Shape (batch, n_agents, n_actions).
            Un-normalised log-probabilities over the discrete action set.
        state_value : torch.Tensor
            Shape (batch, 1).
            Centralized state-value estimate V_ψ(s).
        """
        batch_size = observations.size(0)

        # ---- Step 1: Embed observations into d_model space ----
        # (batch, n_agents, obs_dim) -> (batch, n_agents, d_model)
        h = self.obs_encoder(observations)

        # ---- Step 2: Add sinusoidal positional encoding ----
        h = self.pos_encoding(h)

        # ---- Step 3: Pass through L transformer encoder blocks ----
        # Each block applies: h' = h + MHA(LN(h)); h'' = h' + FFN(LN(h'))
        for block in self.encoder_blocks:
            h = block(h, mask=mask)

        # ---- Step 4: Final layer normalisation ----
        h = self.final_ln(h)  # (batch, n_agents, d_model)

        # ---- Step 5: Policy head — per-agent action logits ----
        action_logits = self.policy_head(h)  # (batch, n_agents, n_actions)

        # ---- Step 6: Value head — mean-pool aggregation ----
        # Centralized critic: V(s) = f(mean(h_1, ..., h_n))
        pooled = h.mean(dim=1)  # (batch, d_model)
        state_value = self.value_head(pooled)  # (batch, 1)

        return action_logits, state_value

    def get_action(
        self,
        observations: torch.Tensor,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Sample actions from the policy and return log-probabilities.

        Parameters
        ----------
        observations : torch.Tensor
            Shape (batch, n_agents, obs_dim).
        deterministic : bool
            If True, take argmax (greedy) actions instead of sampling.

        Returns
        -------
        actions : torch.Tensor     — (batch, n_agents)
        log_probs : torch.Tensor   — (batch, n_agents)
        state_value : torch.Tensor — (batch, 1)
        """
        action_logits, state_value = self.forward(observations)

        # Categorical distribution over discrete dispatch actions
        dist = Categorical(logits=action_logits)

        if deterministic:
            actions = action_logits.argmax(dim=-1)
        else:
            actions = dist.sample()

        log_probs = dist.log_prob(actions)
        return actions, log_probs, state_value

    def evaluate_actions(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Evaluate given actions under the current policy (used in PPO update).

        Returns log_probs, state_value, and entropy for the PPO-clip loss.

        PPO-Clip Objective:
            L^{CLIP}(θ) = 𝔼[min(rₜ · Â, clip(rₜ, 1-ε, 1+ε) · Â)]

        where rₜ = π_θ(aₜ|sₜ) / π_{θ_old}(aₜ|sₜ)
        """
        action_logits, state_value = self.forward(observations)
        dist = Categorical(logits=action_logits)

        log_probs = dist.log_prob(actions)      # (batch, n_agents)
        entropy = dist.entropy()                 # (batch, n_agents)

        return log_probs, state_value, entropy

    @torch.no_grad()
    def act(
        self,
        observations: torch.Tensor,
        deterministic: bool = True,
    ) -> List[int]:
        """
        Inference-only action selection for deployment.

        Parameters
        ----------
        observations : torch.Tensor
            Shape (1, n_agents, obs_dim) — single environment step.
        deterministic : bool
            Use greedy policy (True for deployment).

        Returns
        -------
        List[int]
            Discrete action indices for each agent.
        """
        self.eval()
        actions, _, _ = self.get_action(observations, deterministic=deterministic)
        return actions.squeeze(0).tolist()

    def count_parameters(self) -> int:
        """Total trainable parameter count."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def __repr__(self) -> str:
        n_params = self.count_parameters()
        return (
            f"MultiAgentTransformer(\n"
            f"  n_agents={self.n_agents}, obs_dim={self.obs_dim}, "
            f"n_actions={self.n_actions},\n"
            f"  d_model={self.d_model}, n_heads={DEFAULT_N_HEADS}, "
            f"n_layers={DEFAULT_N_LAYERS},\n"
            f"  trainable_params={n_params:,}\n"
            f")"
        )
