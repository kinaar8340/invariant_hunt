"""Tests for Phase 1.1 unified action principle (Gate A-P)."""

from __future__ import annotations

import math

import sympy as sp

from src.action_principle import (
    ActionParameters,
    GaugeSector,
    action_principle_report,
    burst_potential_derivative_symbolic,
    check_no_ghosts,
    conduit_pde_force_symbolic,
    free_energy_density_symbolic,
    gauged_twist_force_terms,
    holonomy_potential,
    latex_action_principle,
    reduce_to_conduit_pde_check,
    total_lagrangian_density_symbolic,
    unified_lagrangian_density_symbolic,
    wave_map_lagrangian_density_symbolic,
    wg_stability_under_perturbation,
    yang_mills_density_symbolic,
)
from src.invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
    braiding_pin_stiffness,
    gauge_group_label,
    holonomy_restoring_eigenvalue,
)


def test_free_energy_has_holonomy_and_drive():
    F = free_energy_density_symbolic()
    assert F.has(sp.Symbol("kappa", positive=True))
    assert F.has(sp.Symbol("Delta_omega", real=True))


def test_wave_map_healthy_kinetic_sign():
    L = wave_map_lagrangian_density_symbolic()
    # +1/2 dt^2 − (D/8) grad^2
    dt = sp.Symbol("dt_theta_sq", nonnegative=True)
    assert L.coeff(dt) > 0


def test_yang_mills_negative_Fsq_prefactor():
    L = yang_mills_density_symbolic()
    F3 = sp.Symbol("F3_sq", nonnegative=True)
    # L = −F3/(4 g3²) + … so coeff of F3 is negative
    g3 = sp.Symbol("g_3", positive=True)
    # substitute unit couplings
    L1 = L.subs({g3: 1, sp.Symbol("g_2", positive=True): 1, sp.Symbol("g_1", positive=True): 1})
    assert L1.coeff(F3) < 0


def test_unified_sectors_present():
    sectors = unified_lagrangian_density_symbolic()
    for key in (
        "L_sigma",
        "L_skyrme",
        "L_yang_mills",
        "L_hopf",
        "L_holonomy",
        "L_drive",
        "L_burst",
    ):
        assert key in sectors


def test_total_lagrangian_is_expr():
    L = total_lagrangian_density_symbolic()
    assert isinstance(L, sp.Expr)


def test_no_ghosts_default():
    r = check_no_ghosts()
    assert r.healthy
    assert r.checks["holonomy_hessian_pos"]
    assert r.checks["ym_couplings_pos"]


def test_ghost_if_negative_kappa():
    p = ActionParameters(kappa=-0.1)
    r = check_no_ghosts(p)
    assert not r.healthy
    assert not r.checks["holonomy_restoring"]


def test_ghost_if_negative_g():
    p = ActionParameters(gauge=GaugeSector(g3=-1.0, g2=1.0, g1=1.0))
    r = check_no_ghosts(p)
    assert not r.healthy


def test_conduit_reduction_structure():
    red = reduce_to_conduit_pde_check()
    assert red["matches_conduit_structure"]
    force = conduit_pde_force_symbolic()
    assert force.has(sp.Symbol("Delta_omega", real=True))


def test_burst_derivative_vanishes_below_crit():
    s_theta = sp.Symbol("theta", real=True)
    s_crit = sp.Symbol("theta_crit", positive=True)
    Uprime = burst_potential_derivative_symbolic()
    # below threshold Max → 0
    val = Uprime.subs(
        {
            s_theta: 1.0,
            s_crit: 5.0,
            sp.Symbol("C_B", positive=True): 50,
            sp.Symbol("p_B", positive=True): 1,
        }
    )
    assert val == 0


def test_wg_stability_pass():
    st = wg_stability_under_perturbation(n_samples=16, seed=1)
    assert st["pass"]
    assert st["wg_locked"]
    assert st["ghost_free_fraction"] == 1.0


def test_holonomy_potential_minimum():
    p = ActionParameters()
    v0 = holonomy_potential(0.0, p.braiding, p)
    v1 = holonomy_potential(0.1, p.braiding + 0.05, p)
    assert v0 < v1
    assert abs(v0) < 1e-15


def test_gauged_force_restoring_holonomy():
    import numpy as np

    th = np.full((4, 4, 4), 1.0)
    terms = gauged_twist_force_terms(th)
    assert terms["holonomy"] == -DEFAULT_KAPPA * 1.0
    assert terms["drive"] > 0


def test_gauged_force_with_flux():
    import numpy as np

    th = np.zeros((2, 2, 2)) + 0.5
    terms = gauged_twist_force_terms(th, a_mu_curl_contrib=0.01)
    assert terms["gauge_flux"] == 0.01


def test_action_principle_report_gate():
    rep = action_principle_report(n_stability=8, seed=0)
    assert rep["schema"] == "invariant_hunt.action_principle.v1"
    assert rep["gate_A_P"]["pass"]
    assert abs(rep["params"]["wg"] - LOCKED_WG) < 1e-12
    assert abs(rep["params"]["wg_base"] - WG_BASE) < 1e-12


def test_latex_fragment_contains_ym():
    tex = latex_action_principle()
    assert r"\mathrm{SU}(3)" in tex or "SU(3)" in tex
    assert "W_g" in tex
    assert "unified-action" in tex


def test_invariants_holonomy_helpers():
    assert holonomy_restoring_eigenvalue() == -DEFAULT_KAPPA
    assert braiding_pin_stiffness() == LOCKED_WG
    assert "SU(3)" in gauge_group_label()
    assert math.isclose(DEFAULT_BRAIDING, 0.8145)
