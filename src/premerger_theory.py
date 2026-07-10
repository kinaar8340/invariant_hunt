"""
Pre-merger topological phase signatures from locked Hopf/flux invariants.

Post-merger residual ladders are sync-suppressed (see echo_theory.py).
During adiabatic inspiral the system stays below θ_crit for long times;
cumulative *phase* over many orbits is the natural residual channel.

Primary template (Gate P, first concrete form):

    Δφ(t) = α · W_g · Φ_orb(t) · cos(φ_b)

where Φ_orb is the accumulated orbital phase of the best-fit GR waveform
(relative to a reference time), φ_b is the locked braiding attractor, and
α is a dimensionless coupling to be fit or bounded.

Small-α waveform perturbation (real strain h, Hilbert H[h]):

    h(α) ≈ h − α · [W_g cos(φ_b) Φ_orb] · H[h]

Locks W_g, κ, φ_b fixed; only α is free (or scanned).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy import signal

from .echo_theory import ModelParams, f_lattice
from .gw_events import T_M_SUN
from .invariants import DEFAULT_BRAIDING, LOCKED_WG, InvariantSet


@dataclass(frozen=True)
class PremergerPhaseModel:
    """Fixed locks + free coupling for inspiral phase drift."""

    wg: float = LOCKED_WG
    kappa: float = 0.85
    phi_b: float = DEFAULT_BRAIDING  # toroidal [0,1) attractor
    alpha: float = 0.0  # free coupling (fit)

    @classmethod
    def from_invariants(
        cls, inv: InvariantSet | None = None, alpha: float = 0.0
    ) -> PremergerPhaseModel:
        inv = inv or InvariantSet()
        return cls(wg=inv.wg, kappa=inv.kappa, phi_b=inv.braiding_target, alpha=alpha)

    @property
    def cos_phi_b(self) -> float:
        # φ_b stored as toroidal [0,1) → angle
        return math.cos(self.phi_b * 2.0 * math.pi)

    def coupling_kernel(self) -> float:
        """K = W_g · cos(φ_b) so Δφ = α · K · Φ_orb."""
        return self.wg * self.cos_phi_b

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "cos_phi_b": self.cos_phi_b,
            "coupling_kernel_K": self.coupling_kernel(),
            "formula": "Δφ(t) = α · W_g · Φ_orb(t) · cos(φ_b)",
        }


def hilbert_quadrature(h: np.ndarray) -> np.ndarray:
    """Return H[h] (imaginary part of analytic signal)."""
    return np.asarray(signal.hilbert(h).imag, dtype=np.float64)


def orbital_phase_from_strain(
    h: np.ndarray,
    sample_rate: float,
    *,
    t_rel: np.ndarray | None = None,
    t_ref: float | None = None,
) -> np.ndarray:
    """Unwrapped GW phase / 2  as proxy for orbital phase Φ_orb.

    For dominant (2,2) mode, Φ_orb ≈ Ψ_GW / 2.
    Phase is zeroed at t_ref (default: end of array / merger).
    """
    z = signal.hilbert(h)
    psi = np.unwrap(np.angle(z))
    # orbital proxy
    phi_orb = 0.5 * psi
    if t_rel is not None and t_ref is not None:
        # zero at sample nearest t_ref
        i = int(np.argmin(np.abs(t_rel - t_ref)))
        phi_orb = phi_orb - phi_orb[i]
    else:
        phi_orb = phi_orb - phi_orb[-1]
    return np.asarray(phi_orb, dtype=np.float64)


def phase_basis_template(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    model: PremergerPhaseModel | None = None,
) -> np.ndarray:
    """Linear response template τ = −K · Φ_orb · H[h]  (∂h/∂α at α=0)."""
    m = model or PremergerPhaseModel()
    k = m.coupling_kernel()
    h_quad = hilbert_quadrature(h_gr)
    return -k * phi_orb * h_quad


def apply_phase_shift(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    alpha: float,
    model: PremergerPhaseModel | None = None,
) -> np.ndarray:
    """Finite-α phase modulation: Re[ z exp(i Δφ) ] with Δφ = α K Φ_orb."""
    m = model or PremergerPhaseModel()
    dphi = alpha * m.coupling_kernel() * phi_orb
    h_quad = hilbert_quadrature(h_gr)
    return h_gr * np.cos(dphi) - h_quad * np.sin(dphi)


def instantaneous_f_phys_hz(
    mass_solar: float,
    params: ModelParams | None = None,
) -> float:
    """Lattice emission frequency scaled to physical units (∝ 1/M)."""
    from .echo_theory import f_echo_physical_hz

    return f_echo_physical_hz(mass_solar, params)


def premerger_predictions(
    mass_final_solar: float,
    *,
    n_cycles: float = 100.0,
    alpha: float = 1e-4,
    model: PremergerPhaseModel | None = None,
) -> dict[str, Any]:
    """Pre-register qualitative/quantitative expectations."""
    m = model or PremergerPhaseModel()
    # cumulative phase over n_cycles: Φ_orb ~ 2π n_cycles
    phi_cum = 2.0 * math.pi * n_cycles
    dphi = abs(alpha * m.coupling_kernel() * phi_cum)
    return {
        "formula": "Δφ = α · W_g · Φ_orb · cos(φ_b)",
        "mass_final_solar": mass_final_solar,
        "alpha_example": alpha,
        "n_cycles": n_cycles,
        "cumulative_delta_phi_rad": dphi,
        "cumulative_delta_phi_cycles": dphi / (2.0 * math.pi),
        "f_phys_hz": instantaneous_f_phys_hz(mass_final_solar),
        "locks": m.to_dict(),
        "expectations": [
            "Phase drift is cumulative (grows with orbital cycles), not merger-localized.",
            "Mass dependence enters via waveform Φ_orb(t; M) and f_phys ∝ 1/M.",
            "α should be small; large α would already appear in standard PE systematics.",
            "Post-merger residual ladders remain sync-suppressed (prior campaign).",
        ],
    }


# Gate P numerical bars (pre-registered)
GATE_P_DELTA_CHI2: float = 6.0  # 1 extra param α (use 6 conservative / 2-dof style)
GATE_P_INSPIRAL_F_LOW: float = 20.0
GATE_P_INSPIRAL_F_HIGH: float = 100.0  # focus early–mid inspiral
GATE_P_T_END: float = -0.05  # relative to merger: inspiral window t < t_end
