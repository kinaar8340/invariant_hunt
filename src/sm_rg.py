"""
Phase 2.3 — SM gauge coupling RG flow (one-loop) + Gate SM-3 completion.

One-loop β-functions for GUT-normalized couplings (g₁, g₂, g₃):

  d α_i^{-1} / d ln μ  =  − b_i / (2π)

with  b = (41/10, −19/6, −7)  for  i = 1,2,3  (SM, n_g = 3, one Higgs).

Boundary data at μ = M_Z (PDG-ish):
  α_s(M_Z), α_em(M_Z), sin²θ_W(M_Z) → (α₁, α₂, α₃).

Discipline:
  - Core locks (W_g, κ, φ_b) frozen — mild optional dressing only, not fitted.
  - Anomaly cancellation required (from sm_mapping).
  - No gravity / unification claim unless a later gate is registered.
  - FAIL demotes the RG *mapping*, not the locks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG, WG_BASE
from src.sm_mapping import (
    check_anomaly_cancellation,
    check_locks_frozen,
    gate_sm1_report,
)

# ---------------------------------------------------------------------------
# Constants / PDG-ish inputs
# ---------------------------------------------------------------------------
MZ_GEV: float = 91.1876
MT_GEV: float = 172.69  # top threshold (optional 2-loop later)
GUT_NORM: float = 5.0 / 3.0  # g1² = (5/3) g'²

# One-loop SM β coefficients (GUT-normalized α_i), n_gen=3, n_Higgs=1
# b_i in: d α_i^{-1}/d ln μ = −b_i/(2π)
B1: float = 41.0 / 10.0  # U(1)_Y (GUT)
B2: float = -19.0 / 6.0  # SU(2)_L
B3: float = -7.0  # SU(3)_c

# MZ boundary (approximate PDG)
ALPHA_EM_MZ: float = 1.0 / 127.951
ALPHA_S_MZ: float = 0.1179
SIN2_THETA_W_MZ: float = 0.23122

# Gate thresholds
ALPHA_S_MZ_TOL: float = 0.005  # absolute on α_s after round-trip
SIN2W_TOL: float = 0.005
ALPHA_EM_REL_TOL: float = 0.02
# Evolution health
MU_MAX_GEV: float = 1.0e16
MU_MIN_GEV: float = 1.0  # not below QCD Landau pole in this simple 1-loop SM
ALPHA_S_MUST_DECREASE: bool = True


@dataclass
class RGBoundaryMZ:
    """Electroweak / QCD inputs at M_Z."""

    alpha_em: float = ALPHA_EM_MZ
    alpha_s: float = ALPHA_S_MZ
    sin2_theta_w: float = SIN2_THETA_W_MZ
    mu_GeV: float = MZ_GEV

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class GaugeAlphas:
    """GUT-normalized α₁, α₂, α₃ and inverse."""

    alpha1: float
    alpha2: float
    alpha3: float
    mu_GeV: float

    @property
    def inv1(self) -> float:
        return 1.0 / self.alpha1 if self.alpha1 else math.inf

    @property
    def inv2(self) -> float:
        return 1.0 / self.alpha2 if self.alpha2 else math.inf

    @property
    def inv3(self) -> float:
        return 1.0 / self.alpha3 if self.alpha3 else math.inf

    def to_dict(self) -> dict[str, float]:
        return {
            "alpha1": self.alpha1,
            "alpha2": self.alpha2,
            "alpha3": self.alpha3,
            "inv1": self.inv1,
            "inv2": self.inv2,
            "inv3": self.inv3,
            "mu_GeV": self.mu_GeV,
        }


def mz_to_gut_alphas(bnd: RGBoundaryMZ | None = None) -> GaugeAlphas:
    """Map (α_em, sin²θ_W, α_s) at M_Z → GUT-normalized (α₁, α₂, α₃)."""
    b = bnd or RGBoundaryMZ()
    # α_em = e²/(4π),  e = g sinθ = g' cosθ
    # α2 = α_em / sin²θ_W,  α' = α_em / cos²θ_W,  α1 = (5/3) α'
    s2 = b.sin2_theta_w
    c2 = 1.0 - s2
    alpha2 = b.alpha_em / s2
    alpha_prime = b.alpha_em / c2
    alpha1 = GUT_NORM * alpha_prime
    alpha3 = b.alpha_s
    return GaugeAlphas(alpha1=alpha1, alpha2=alpha2, alpha3=alpha3, mu_GeV=b.mu_GeV)


def gut_alphas_to_ew(alphas: GaugeAlphas) -> dict[str, float]:
    """Inverse map: (α₁,α₂,α₃) → α_em, sin²θ_W, α_s (tree matching)."""
    alpha_prime = alphas.alpha1 / GUT_NORM
    # 1/α_em = 1/α' + 1/α2
    inv_em = 1.0 / alpha_prime + 1.0 / alphas.alpha2
    alpha_em = 1.0 / inv_em
    # sin²θ_W = α_em / α2
    sin2 = alpha_em / alphas.alpha2
    return {
        "alpha_em": float(alpha_em),
        "sin2_theta_w": float(sin2),
        "alpha_s": float(alphas.alpha3),
        "mu_GeV": float(alphas.mu_GeV),
    }


def beta_coefficients(n_gen: int = 3, n_higgs: int = 1) -> tuple[float, float, float]:
    """One-loop b_i for SM-like content (default n_gen=3, n_H=1).

    Standard SM: (41/10, −19/6, −7).
    General formulas (GUT-normalized):
      b1 = 4/3 n_g + 1/10 n_H
      b2 = −22/3 + 4/3 n_g + 1/6 n_H
      b3 = −11 + 4/3 n_g
    """
    ng = float(n_gen)
    nh = float(n_higgs)
    b1 = (4.0 / 3.0) * ng + (1.0 / 10.0) * nh
    b2 = -22.0 / 3.0 + (4.0 / 3.0) * ng + (1.0 / 6.0) * nh
    b3 = -11.0 + (4.0 / 3.0) * ng
    return b1, b2, b3


def evolve_inv_alpha(
    inv_alpha0: float,
    b_i: float,
    mu0: float,
    mu1: float,
) -> float:
    """α^{-1}(μ1) = α^{-1}(μ0) − (b_i / 2π) ln(μ1/μ0)."""
    return inv_alpha0 - (b_i / (2.0 * math.pi)) * math.log(mu1 / mu0)


def evolve_alphas(
    alphas0: GaugeAlphas,
    mu1: float,
    *,
    n_gen: int = 3,
    n_higgs: int = 1,
) -> GaugeAlphas:
    """One-loop run of (α1,α2,α3) from alphas0.mu to mu1."""
    b1, b2, b3 = beta_coefficients(n_gen=n_gen, n_higgs=n_higgs)
    inv1 = evolve_inv_alpha(alphas0.inv1, b1, alphas0.mu_GeV, mu1)
    inv2 = evolve_inv_alpha(alphas0.inv2, b2, alphas0.mu_GeV, mu1)
    inv3 = evolve_inv_alpha(alphas0.inv3, b3, alphas0.mu_GeV, mu1)
    # Protect against Landau poles (inv ≤ 0)
    a1 = 1.0 / inv1 if inv1 > 1e-12 else float("inf")
    a2 = 1.0 / inv2 if inv2 > 1e-12 else float("inf")
    a3 = 1.0 / inv3 if inv3 > 1e-12 else float("inf")
    return GaugeAlphas(alpha1=a1, alpha2=a2, alpha3=a3, mu_GeV=mu1)


def rg_trajectory(
    *,
    mu_min: float = MZ_GEV,
    mu_max: float = 1.0e16,
    n_points: int = 80,
    bnd: RGBoundaryMZ | None = None,
    n_gen: int = 3,
    n_higgs: int = 1,
    lock_dress: bool = True,
) -> dict[str, Any]:
    """Sample α_i(μ) on a log grid from mu_min to mu_max (starting at M_Z match)."""
    bnd = bnd or RGBoundaryMZ()
    a0 = mz_to_gut_alphas(bnd)
    if lock_dress:
        # Extremely mild frozen-lock dressing (does not re-fit locks)
        dress = 1.0 + 1e-4 * (DEFAULT_KAPPA - 0.85) + 1e-6 * (LOCKED_WG - WG_BASE / math.pi)
        a0 = GaugeAlphas(
            alpha1=a0.alpha1 * dress,
            alpha2=a0.alpha2 * dress,
            alpha3=a0.alpha3 * dress,
            mu_GeV=a0.mu_GeV,
        )

    mus = np.logspace(math.log10(mu_min), math.log10(mu_max), n_points)
    rows = []
    for mu in mus:
        a = evolve_alphas(a0, float(mu), n_gen=n_gen, n_higgs=n_higgs)
        ew = gut_alphas_to_ew(a)
        rows.append(
            {
                "mu_GeV": float(mu),
                **a.to_dict(),
                **{f"ew_{k}": v for k, v in ew.items() if k != "mu_GeV"},
            }
        )

    # Asymptotic freedom: α3 should fall as μ increases from MZ
    a_mz = evolve_alphas(a0, MZ_GEV, n_gen=n_gen, n_higgs=n_higgs)
    a_hi = evolve_alphas(a0, min(mu_max, 1e12), n_gen=n_gen, n_higgs=n_higgs)
    af_ok = a_hi.alpha3 < a_mz.alpha3

    # Landau poles in window: inv_alpha > 0 for all samples
    landau_free = all(
        r["inv1"] > 0 and r["inv2"] > 0 and r["inv3"] > 0 and math.isfinite(r["alpha3"])
        for r in rows
    )

    # Round-trip: evolve MZ → 10^10 → MZ and compare α_s, sin²θ_W
    a_up = evolve_alphas(a0, 1.0e10, n_gen=n_gen, n_higgs=n_higgs)
    a_back = evolve_alphas(a_up, MZ_GEV, n_gen=n_gen, n_higgs=n_higgs)
    ew_back = gut_alphas_to_ew(a_back)
    ew0 = gut_alphas_to_ew(a0)

    return {
        "schema": "invariant_hunt.sm_rg_trajectory.v1",
        "boundary_MZ": bnd.to_dict(),
        "alphas_MZ": a0.to_dict(),
        "beta": {"b1": B1, "b2": B2, "b3": B3, "n_gen": n_gen, "n_higgs": n_higgs},
        "beta_check": {
            "b1": beta_coefficients(n_gen, n_higgs)[0],
            "b2": beta_coefficients(n_gen, n_higgs)[1],
            "b3": beta_coefficients(n_gen, n_higgs)[2],
            "matches_SM_default": n_gen == 3 and n_higgs == 1,
        },
        "mu_min": mu_min,
        "mu_max": mu_max,
        "n_points": n_points,
        "trajectory": rows,
        "asymptotic_freedom_alpha_s": af_ok,
        "landau_free_in_window": landau_free,
        "round_trip": {
            "mu_mid": 1.0e10,
            "ew_start": ew0,
            "ew_back": ew_back,
            "delta_alpha_s": abs(ew_back["alpha_s"] - ew0["alpha_s"]),
            "delta_sin2w": abs(ew_back["sin2_theta_w"] - ew0["sin2_theta_w"]),
            "delta_alpha_em_rel": abs(ew_back["alpha_em"] - ew0["alpha_em"])
            / max(ew0["alpha_em"], 1e-30),
        },
        "locks": {
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
            "dressing_applied": lock_dress,
        },
    }


def check_rg_consistency(
    *,
    n_points: int = 60,
    mu_max: float = MU_MAX_GEV,
) -> dict[str, Any]:
    """Gate SM-3 RG criteria (one-loop SM)."""
    traj = rg_trajectory(n_points=n_points, mu_max=mu_max)
    rt = traj["round_trip"]
    bcheck = traj["beta_check"]

    # SM default beta coefficients
    b_ok = (
        abs(bcheck["b1"] - B1) < 1e-12
        and abs(bcheck["b2"] - B2) < 1e-12
        and abs(bcheck["b3"] - B3) < 1e-12
    )

    criteria = {
        "beta_coefficients_SM": b_ok,
        "asymptotic_freedom_alpha_s": bool(traj["asymptotic_freedom_alpha_s"]),
        "landau_free_MZ_to_mu_max": bool(traj["landau_free_in_window"]),
        "round_trip_alpha_s": rt["delta_alpha_s"] <= ALPHA_S_MZ_TOL,
        "round_trip_sin2w": rt["delta_sin2w"] <= SIN2W_TOL,
        "round_trip_alpha_em": rt["delta_alpha_em_rel"] <= ALPHA_EM_REL_TOL,
        "locks_frozen": check_locks_frozen()["pass"],
    }

    # High-scale sample values (for tables, not a unification claim)
    a_gut = evolve_alphas(mz_to_gut_alphas(), 1.0e16)
    ew_gut = gut_alphas_to_ew(a_gut)

    return {
        "schema": "invariant_hunt.sm_rg_check.v1",
        "pass": all(criteria.values()),
        "criteria": criteria,
        "thresholds": {
            "alpha_s_mz_tol": ALPHA_S_MZ_TOL,
            "sin2w_tol": SIN2W_TOL,
            "alpha_em_rel_tol": ALPHA_EM_REL_TOL,
            "mu_max_GeV": mu_max,
        },
        "round_trip": rt,
        "alphas_at_1e16": a_gut.to_dict(),
        "ew_at_1e16": ew_gut,
        "beta": traj["beta"],
        "trajectory_head": traj["trajectory"][:3],
        "trajectory_tail": traj["trajectory"][-3:],
        "n_trajectory_points": len(traj["trajectory"]),
        "locks": traj["locks"],
        "note": (
            "One-loop SM RG only. No claim of gauge coupling unification. "
            "Locks are not free parameters of the β-functions."
        ),
    }


def gate_sm3_full_report(
    *,
    n_points: int = 60,
    mu_max: float = MU_MAX_GEV,
) -> dict[str, Any]:
    """Complete Gate SM-3: anomaly cancellation + RG consistency."""
    anom = check_anomaly_cancellation()
    rg = check_rg_consistency(n_points=n_points, mu_max=mu_max)
    sm1 = gate_sm1_report()
    locks = check_locks_frozen()

    criteria = {
        "anomaly_cancellation": anom["pass"],
        "rg_consistency": rg["pass"],
        "sm1_still_pass": sm1["pass"],
        "locks_frozen": locks["pass"],
    }
    # Detailed RG criteria bubble up
    for k, v in rg["criteria"].items():
        criteria[f"rg_{k}"] = v

    return {
        "schema": "invariant_hunt.gate_sm3.v1",
        "phase": "2.3",
        "gate": "SM-3",
        "pass": all(
            [
                anom["pass"],
                rg["pass"],
                sm1["pass"],
                locks["pass"],
            ]
        ),
        "criteria": {
            "anomaly_cancellation": anom["pass"],
            "rg_consistency": rg["pass"],
            "sm1_still_pass": sm1["pass"],
            "locks_frozen": locks["pass"],
        },
        "rg_criteria_detail": rg["criteria"],
        "anomaly": anom,
        "rg": rg,
        "locks": locks,
        "note": (
            "Gate SM-3 complete: anomalies + one-loop SM gauge RG. "
            "No unification or gravity claim."
        ),
        "discipline": {
            "locks_not_fitted": True,
            "no_unification_claim": True,
            "no_gravity_claim": True,
            "premerger_freeze_untouched": True,
        },
    }


def sm_rg_summary_table() -> list[dict[str, Any]]:
    """Compact multi-scale table for papers / CLI."""
    a0 = mz_to_gut_alphas()
    scales = [MZ_GEV, 1e3, 1e6, 1e10, 1e16]
    rows = []
    for mu in scales:
        a = evolve_alphas(a0, mu)
        ew = gut_alphas_to_ew(a)
        rows.append(
            {
                "mu_GeV": mu,
                "alpha1": a.alpha1,
                "alpha2": a.alpha2,
                "alpha3": a.alpha3,
                "inv1": a.inv1,
                "inv2": a.inv2,
                "inv3": a.inv3,
                "alpha_em": ew["alpha_em"],
                "sin2_theta_w": ew["sin2_theta_w"],
                "alpha_s": ew["alpha_s"],
            }
        )
    return rows
