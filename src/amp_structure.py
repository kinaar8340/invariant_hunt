"""
Amplitude-structure mappings for the positional echo ladder.

Core locks (W_g, κ, braiding attractor) stay fixed. Only the relative
visibility/weight of ladder steps changes:

  geometric       — fixed decay amp0^n  (mapping v2 baseline)
  braiding        — geometric × (1 + β cos ψ_n)
  braiding_lock   — geometric × exp(−γ · ang(ψ_n, φ_b^*))
  flux_kappa      — geometric with base → κ-dependent flux-shedding rate
  hopf_winding    — geometric × (1 + α cos(2π n / W_g))

All weights are non-negative and L2-normalized across the train so overall
scale remains free in the coherent fit (a_c, a_s).
"""

from __future__ import annotations

import math
from typing import Any, Literal

from .invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG, InvariantSet

AmpStructure = Literal[
    "geometric",
    "braiding",
    "braiding_lock",
    "flux_kappa",
    "hopf_winding",
]

AMP_STRUCTURES: tuple[AmpStructure, ...] = (
    "geometric",
    "braiding",
    "braiding_lock",
    "flux_kappa",
    "hopf_winding",
)


def _angle_diff(a: float, b: float) -> float:
    """Smallest absolute difference on the circle [0, 2π)."""
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return abs(d)


def step_weight(
    n: int,
    *,
    braiding_angle: float,
    inv: InvariantSet | None = None,
    amp0: float = 0.35,
    structure: AmpStructure = "geometric",
    beta: float = 0.75,
    gamma: float = 2.0,
    alpha: float = 0.5,
) -> float:
    """Relative amplitude weight for ladder site n ≥ 1 (before train normalization)."""
    inv = inv or InvariantSet()
    base = float(amp0) ** float(n)
    if structure == "geometric":
        return max(base, 0.0)

    if structure == "braiding":
        # Flux visibility modulated by braiding phase on the fiber
        mod = 1.0 + beta * math.cos(braiding_angle)
        return max(base * mod, 0.0)

    if structure == "braiding_lock":
        # Prefer steps whose braiding sits near the locked attractor φ_b^*
        phi_star = inv.braiding_target if inv.braiding_target else DEFAULT_BRAIDING
        # map attractor from toroidal [0,1) to angle if needed
        if 0.0 <= phi_star <= 1.0:
            phi_star_ang = phi_star * 2.0 * math.pi
        else:
            phi_star_ang = float(phi_star)
        dist = _angle_diff(braiding_angle, phi_star_ang)
        return max(base * math.exp(-gamma * dist), 0.0)

    if structure == "flux_kappa":
        # Burst / flux-shed rate tied to holonomy κ (paper: ΔΦ ∝ Δω/W_g, thr ∝ κ)
        # Effective geometric ratio r = amp0 * (κ / κ_ref) with soft floor
        kappa = inv.kappa if inv.kappa else DEFAULT_KAPPA
        r = float(amp0) * (kappa / DEFAULT_KAPPA)
        r = min(max(r, 0.05), 0.95)
        return max(r ** float(n), 0.0)

    if structure == "hopf_winding":
        # Quasi-periodic modulation over one full W_g winding of lattice sites
        wg = inv.wg if inv.wg else LOCKED_WG
        mod = 1.0 + alpha * math.cos(2.0 * math.pi * float(n) / wg)
        return max(base * mod, 0.0)

    raise ValueError(f"Unknown amplitude structure: {structure}")


def normalize_weights(weights: list[float]) -> list[float]:
    """L2-normalize so train energy is O(1); preserve relative shape."""
    s2 = sum(w * w for w in weights)
    if s2 <= 1e-30:
        n = len(weights)
        return [1.0 / math.sqrt(n)] * n if n else []
    norm = math.sqrt(s2)
    return [w / norm for w in weights]


def structure_description(structure: AmpStructure) -> dict[str, Any]:
    return {
        "geometric": {
            "formula": "w_n = amp0^n",
            "physics": "Fixed geometric decay (mapping v2 baseline).",
        },
        "braiding": {
            "formula": "w_n = amp0^n · (1 + β cos ψ_n)",
            "physics": "Visibility modulated by fiber braiding phase.",
        },
        "braiding_lock": {
            "formula": "w_n = amp0^n · exp(−γ · ang(ψ_n, φ_b*))",
            "physics": "Prefer steps near locked braiding attractor φ_b*.",
        },
        "flux_kappa": {
            "formula": "w_n = (amp0 · κ/κ0)^n",
            "physics": "Decay rate tracks holonomy/flux-shed parameter κ.",
        },
        "hopf_winding": {
            "formula": "w_n = amp0^n · (1 + α cos(2π n / W_g))",
            "physics": "Quasi-period over full Hopf winding W_g.",
        },
    }[structure]
