"""Tests for Phase 2.3 SM one-loop RG + Gate SM-3."""

from __future__ import annotations

import math

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG
from src.sm_rg import (
    ALPHA_S_MZ,
    B1,
    B2,
    B3,
    MZ_GEV,
    RGBoundaryMZ,
    beta_coefficients,
    check_rg_consistency,
    evolve_alphas,
    gate_sm3_full_report,
    gut_alphas_to_ew,
    mz_to_gut_alphas,
    rg_trajectory,
    sm_rg_summary_table,
)


def test_beta_sm_default():
    b1, b2, b3 = beta_coefficients(3, 1)
    assert abs(b1 - B1) < 1e-12
    assert abs(b2 - B2) < 1e-12
    assert abs(b3 - B3) < 1e-12
    assert abs(b1 - 4.1) < 1e-12
    assert abs(b3 + 7.0) < 1e-12


def test_mz_matching_roundtrip_local():
    a = mz_to_gut_alphas()
    ew = gut_alphas_to_ew(a)
    assert abs(ew["alpha_s"] - ALPHA_S_MZ) < 1e-12
    assert abs(ew["sin2_theta_w"] - 0.23122) < 1e-5
    assert abs(ew["alpha_em"] - 1.0 / 127.951) < 1e-6


def test_alpha_s_asymptotic_freedom():
    a0 = mz_to_gut_alphas()
    a_hi = evolve_alphas(a0, 1e12)
    assert a_hi.alpha3 < a0.alpha3


def test_evolve_identity():
    a0 = mz_to_gut_alphas()
    a1 = evolve_alphas(a0, MZ_GEV)
    assert abs(a1.alpha1 - a0.alpha1) < 1e-12
    assert abs(a1.alpha3 - a0.alpha3) < 1e-12


def test_round_trip_rg():
    a0 = mz_to_gut_alphas()
    a_up = evolve_alphas(a0, 1e10)
    a_back = evolve_alphas(a_up, MZ_GEV)
    assert abs(a_back.alpha3 - a0.alpha3) < 1e-9
    assert abs(a_back.alpha1 - a0.alpha1) < 1e-9


def test_trajectory_monotonic_log():
    traj = rg_trajectory(n_points=20, mu_max=1e10)
    assert traj["asymptotic_freedom_alpha_s"]
    assert traj["landau_free_in_window"]
    mus = [r["mu_GeV"] for r in traj["trajectory"]]
    assert mus == sorted(mus)


def test_rg_consistency_pass():
    r = check_rg_consistency(n_points=40)
    assert r["pass"], r["criteria"]


def test_gate_sm3_full_pass():
    r = gate_sm3_full_report(n_points=40)
    assert r["gate"] == "SM-3"
    assert r["pass"], r["criteria"]
    assert r["criteria"]["anomaly_cancellation"]
    assert r["criteria"]["rg_consistency"]
    assert r["discipline"]["no_unification_claim"]
    assert abs(r["locks"]["W_g"] - LOCKED_WG) < 1e-12
    assert abs(r["locks"]["kappa"] - DEFAULT_KAPPA) < 1e-12
    assert abs(r["locks"]["phi_b"] - DEFAULT_BRAIDING) < 1e-12


def test_summary_table_scales():
    rows = sm_rg_summary_table()
    assert len(rows) >= 4
    assert rows[0]["mu_GeV"] == MZ_GEV
    # α3 falls with scale
    assert rows[-1]["alpha3"] < rows[0]["alpha3"]


def test_custom_boundary():
    bnd = RGBoundaryMZ(alpha_s=0.12, sin2_theta_w=0.23)
    a = mz_to_gut_alphas(bnd)
    assert math.isfinite(a.alpha1) and a.alpha3 == 0.12
