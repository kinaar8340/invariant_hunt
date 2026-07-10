"""Tests for Phase 3 emergent gravity (Gate GR-1 / GR-2)."""

from __future__ import annotations

import math

from src.gravity_emergence import (
    G_CODATA,
    GravityParams,
    defect_curvature_scalar,
    effective_stress_energy_density,
    einstein_limit_symbolic,
    g_n_schema,
    g_n_si_matched,
    gate_gr1_report,
    gate_gr2_report,
    gr_light_deflection_solar,
    gr_perihelion_mercury,
    newtonian_potential,
    poisson_source,
)
from src.invariants import DEFAULT_KAPPA, LOCKED_WG


def test_g_schema_positive_locks():
    s = g_n_schema()
    assert s["positive"]
    assert s["G_schema"] > 0
    assert abs(s["W_g"] - LOCKED_WG) < 1e-12
    assert abs(s["kappa"] - DEFAULT_KAPPA) < 1e-12


def test_g_schema_scales_with_lambda():
    g1 = g_n_schema(GravityParams(lambda_sigma=1.0))["G_schema"]
    g2 = g_n_schema(GravityParams(lambda_sigma=2.0))["G_schema"]
    assert abs(g2 / g1 - 2.0) < 1e-9


def test_si_match_default_codata():
    m = g_n_si_matched()
    assert abs(m["ratio_to_codata"] - 1.0) < 1e-12
    assert abs(m["G_SI_matched"] - G_CODATA) < 1e-20


def test_stress_energy_positive():
    te = effective_stress_energy_density(grad_theta_sq=0.1, theta_bar=0.2)
    assert te["positive_energy"]
    assert te["rho_eff"] > 0


def test_curvature_finite():
    c = defect_curvature_scalar(holonomy_gap=0.1, twist_laplacian=0.05)
    assert c["finite"]
    assert math.isfinite(c["R_eff"])


def test_newtonian_attractive():
    pot = newtonian_potential(1.98847e30, 1.496e11)
    assert pot["Phi"] < 0
    assert pot["g_accel"] > 0


def test_poisson_source():
    s = poisson_source(1.0, G=G_CODATA)
    assert abs(s - 4 * math.pi * G_CODATA) < 1e-20


def test_einstein_scaffold():
    e = einstein_limit_symbolic()
    assert "8\\pi G_N" in e["einstein_equation"] or "8\\pi" in e["einstein_equation"]


def test_gate_gr1_pass():
    r = gate_gr1_report()
    assert r["pass"], r["criteria"]
    assert r["discipline"]["locks_not_fitted"]
    assert r["discipline"]["premerger_freeze_untouched"]


def test_gate_gr2_pass():
    r = gate_gr2_report()
    assert r["pass"], r["criteria"]
    assert abs(r["light_deflection"]["delta_arcsec"] - 1.75) < 0.05


def test_gr_analytics_near_targets():
    d = gr_light_deflection_solar()
    assert abs(d["delta_arcsec"] - 1.751) < 0.05
    p = gr_perihelion_mercury()
    assert abs(p["arcsec_per_century"] - 42.98) < 2.0


def test_locks_not_overwritten():
    p = GravityParams(wg=1.0, kappa=0.1)
    p.freeze_locks()
    assert abs(p.wg - LOCKED_WG) < 1e-12
    assert abs(p.kappa - DEFAULT_KAPPA) < 1e-12
