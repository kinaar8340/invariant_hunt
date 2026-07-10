"""
Core topological / geometric invariants for the gauged Hopf lattice.

Formalizes locked quantities that appear numerically in the TOE conduit
(W_g ≈ 350/π, braiding attractor, burst thresholds) so they can be:

1. Checked for stability under parameter sweeps (meta-optimizer)
2. Mapped analytically to observables (predictions pipeline)
3. Falsified with explicit precision targets
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

# Canonical lock target from Hopf-lattice numerics / papers
WG_BASE: float = 350.0
LOCKED_WG: float = WG_BASE / math.pi  # ≈ 111.408
DEFAULT_KAPPA: float = 0.85
DEFAULT_BRAIDING: float = 0.8145

# Tolerance for "locked" declaration (relative)
DEFAULT_LOCK_TOL: float = 1e-3


def link_saturation_theta(wg: float = LOCKED_WG) -> float:
    """Hopf linking saturation: Θ_link = 2π W_g / (2 W_g + 1).

    Near π for W_g ≈ 111.408 (see papers/GW_Burst_Threshold.tex).
    """
    return (2.0 * math.pi * wg) / (2.0 * wg + 1.0)


def burst_threshold(kappa: float = DEFAULT_KAPPA) -> float:
    """Effective PDE/lattice burst threshold: θ_crit = π(1 + κ)."""
    return math.pi * (1.0 + kappa)


def geometric_winding_from_base(wg_base: float) -> float:
    """Map action-like base constant to geometric winding W_g = wg_base / π."""
    return wg_base / math.pi


@dataclass
class InvariantSet:
    """Bundle of locked / candidate invariants for one model state."""

    wg_base: float = WG_BASE
    kappa: float = DEFAULT_KAPPA
    braiding_target: float = DEFAULT_BRAIDING
    geometric_winding: float | None = None
    braiding_phase: float | None = None
    stability_score: float | None = None
    bursts_per_step: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.geometric_winding is None:
            self.geometric_winding = geometric_winding_from_base(self.wg_base)

    @property
    def wg(self) -> float:
        return float(self.geometric_winding if self.geometric_winding is not None else LOCKED_WG)

    @property
    def theta_link(self) -> float:
        return link_saturation_theta(self.wg)

    @property
    def theta_crit(self) -> float:
        return burst_threshold(self.kappa)

    def lock_residuals(self) -> dict[str, float]:
        """How far measured values sit from canonical locks."""
        residuals: dict[str, float] = {
            "wg_vs_350_over_pi": abs(self.wg - LOCKED_WG),
            "wg_base_vs_350": abs(self.wg_base - WG_BASE),
        }
        if self.braiding_phase is not None:
            residuals["braiding_vs_target"] = abs(self.braiding_phase - self.braiding_target)
        return residuals

    def is_locked(self, tol: float = DEFAULT_LOCK_TOL) -> bool:
        """True if W_g is within relative tolerance of 350/π."""
        return abs(self.wg - LOCKED_WG) / LOCKED_WG <= tol

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["theta_link"] = self.theta_link
        d["theta_crit"] = self.theta_crit
        d["locked"] = self.is_locked()
        d["residuals"] = self.lock_residuals()
        return d

    @classmethod
    def from_monitor_stats(
        cls,
        stats: dict[str, Any],
        wg_base: float = WG_BASE,
        kappa: float = DEFAULT_KAPPA,
        braiding_target: float = DEFAULT_BRAIDING,
    ) -> InvariantSet:
        """Build from conduit.monitor_topological_winding() output."""
        return cls(
            wg_base=wg_base,
            kappa=kappa,
            braiding_target=braiding_target,
            geometric_winding=float(stats.get("geometric_winding", wg_base / math.pi)),
            braiding_phase=float(stats["braiding_phase"]) if "braiding_phase" in stats else None,
            stability_score=float(stats["stability_score"]) if "stability_score" in stats else None,
            bursts_per_step=float(stats["bursts_per_step"]) if "bursts_per_step" in stats else None,
            extra={k: v for k, v in stats.items() if k not in {
                "geometric_winding", "braiding_phase", "stability_score", "bursts_per_step"
            }},
        )


def hopf_penalty(geo_w: float, wg_base: float) -> float:
    """Penalty used by meta-optimizer: |geo_w - wg_base/π|."""
    return abs(geo_w - geometric_winding_from_base(wg_base))


def holonomy_restoring_eigenvalue(kappa: float = DEFAULT_KAPPA) -> float:
    """Mean-field holonomy linearization eigenvalue: ∂_t θ̄ ≈ −κ θ̄ + …

    Must be strictly negative for Gate A-P (no runaway / ghost holonomy).
    """
    return -float(kappa)


def braiding_pin_stiffness(wg: float = LOCKED_WG) -> float:
    """Quadratic pin stiffness for (φ_b − φ_b*)² term in the action: W_g > 0."""
    return float(wg)


def gauge_group_label() -> str:
    """Target gauge structure for Phase 1.1 action scaffolding."""
    return "SU(3)×SU(2)×U(1)"
