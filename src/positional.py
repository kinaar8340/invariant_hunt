"""
Positional (phase / lattice) interpretation of 350/π and related locks.

Rather than treating W_g ≈ 111.408 purely as a temporal burst cadence,
this module treats it as a **positional / phase coordinate** in the Hopf
lattice:

- phase on S¹ fibers of the Hopf fibration
- lattice-site alignment angle
- braiding angle in the gauged two-gyro structure

Bursts / echoes then arise when dynamical trajectories align with locked
phase loci — generating quasi-periodic observables in both space and time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .invariants import LOCKED_WG, WG_BASE, DEFAULT_KAPPA, burst_threshold


@dataclass(frozen=True)
class PositionalPhase:
    """Phase coordinate derived from locked winding.

    Attributes
    ----------
    wg :
        Geometric winding W_g (default 350/π).
    lattice_index :
        Integer site index along a discrete Hopf chain.
    fractional_offset :
        Extra fractional phase in [0, 1).
    """

    wg: float = LOCKED_WG
    lattice_index: int = 0
    fractional_offset: float = 0.0

    @property
    def action_base(self) -> float:
        """wg_base ≈ W_g · π (≈ 350 when locked)."""
        return self.wg * math.pi

    @property
    def fiber_angle(self) -> float:
        """Angle on the Hopf fiber: 2π · (n + f) / W_g  (rad)."""
        return 2.0 * math.pi * (self.lattice_index + self.fractional_offset) / self.wg

    @property
    def lattice_phase_unit(self) -> float:
        """Phase in toroidal units [0, 1): fractional part of n/W_g + f."""
        return (self.lattice_index / self.wg + self.fractional_offset) % 1.0

    @property
    def braiding_angle(self) -> float:
        """Braiding angle proxy: fiber angle mod 2π."""
        return self.fiber_angle % (2.0 * math.pi)

    def alignment_to_canonical(self) -> float:
        """Distance (in phase units) to nearest multiple of 1/W_g.

        Zero means perfect lattice-site lock.
        """
        x = (self.lattice_index + self.fractional_offset) * self.wg
        nearest = round(x)
        return abs(x - nearest) / max(self.wg, 1e-12)


def phase_to_timing_offset(
    phase: PositionalPhase | float,
    *,
    base_period: float = 1.0,
    wg: float = LOCKED_WG,
) -> float:
    """Map positional phase → timing offset δt for burst/echo forecasts.

    δt = base_period · (φ_unit) where φ_unit ∈ [0, 1) is the lattice phase.

    Parameters
    ----------
    phase :
        PositionalPhase or raw phase in [0, 1) / radians (if float, treated as unit phase).
    base_period :
        Characteristic period of the observable (e.g. ringdown time unit).
    wg :
        Winding used only when converting a bare float fiber angle... unused for unit phase.
    """
    del wg  # reserved for future fiber-angle conversion paths
    if isinstance(phase, PositionalPhase):
        unit = phase.lattice_phase_unit
    else:
        unit = float(phase) % 1.0
    return base_period * unit


def phase_to_frequency(
    phase: PositionalPhase | None = None,
    *,
    scale_hz: float = 1.0,
    wg: float = LOCKED_WG,
) -> float:
    """Characteristic frequency tied to W_g scaling.

    f = scale_hz · W_g / (2π)  — dimensionless lattice rate mapped to Hz
    via an experimental scale. When phase is provided, a cosine modulation
    encodes positional alignment (constructive at lattice lock).
    """
    f0 = scale_hz * wg / (2.0 * math.pi)
    if phase is None:
        return f0
    # mild positional modulation; amplitude 0 keeps pure W_g scaling if desired
    mod = 0.5 * (1.0 + math.cos(phase.braiding_angle))
    return f0 * (0.85 + 0.15 * mod)


def burst_loci(
    n_sites: int,
    wg: float = LOCKED_WG,
    kappa: float = DEFAULT_KAPPA,
) -> list[dict[str, float]]:
    """Generate discrete lattice sites where burst alignment is expected.

    Each locus carries fiber angle, unit phase, timing offset (period=1),
    and the model burst threshold for reference.
    """
    theta_c = burst_threshold(kappa)
    loci = []
    for n in range(n_sites):
        p = PositionalPhase(wg=wg, lattice_index=n)
        loci.append(
            {
                "site": float(n),
                "fiber_angle": p.fiber_angle,
                "phase_unit": p.lattice_phase_unit,
                "timing_offset": phase_to_timing_offset(p, base_period=1.0),
                "theta_crit": theta_c,
                "alignment": p.alignment_to_canonical(),
            }
        )
    return loci


def positional_hopf_residual(geo_w: float, wg_base: float = WG_BASE) -> float:
    """Positional framing of hopf penalty: |geo_w - wg_base/π|.

    Same numeric form as the temporal meta-optimizer penalty, but interpreted
    as misalignment of measured winding from the locked phase lattice constant.
    """
    return abs(geo_w - wg_base / math.pi)
