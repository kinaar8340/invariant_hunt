"""Tests for Phase 1.2 locks-fixed holonomy/gauge meta-sweeps."""

from __future__ import annotations

from src.gauged_meta_sweep import (
    GaugedSweepKnobs,
    evaluate_locks_fixed_trial,
    locked_action_params,
    run_locks_fixed_monte_carlo,
    run_locks_fixed_optuna,
)
from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG, WG_BASE


def test_locked_params_freeze_wg():
    knobs = GaugedSweepKnobs(g3=2.5, g2=0.4, g1=1.2, D=0.08)
    p = locked_action_params(knobs)
    assert p.wg_base == WG_BASE
    assert abs(p.wg - LOCKED_WG) < 1e-12
    assert p.braiding == DEFAULT_BRAIDING
    assert abs(p.kappa - DEFAULT_KAPPA) < 1e-12
    assert p.gauge.g3 == 2.5


def test_kappa_scale_probe_only():
    knobs = GaugedSweepKnobs(kappa_scale=1.1)
    p = locked_action_params(knobs)
    assert abs(p.kappa - DEFAULT_KAPPA * 1.1) < 1e-12
    assert abs(p.wg - LOCKED_WG) < 1e-12


def test_evaluate_default_knobs_ghost_free():
    res = evaluate_locks_fixed_trial(GaugedSweepKnobs())
    assert res.ghost_free
    assert res.wg_residual < 1e-12
    assert res.holonomy_restoring
    assert res.braiding_at_minimum
    assert res.loss < 1.0


def test_evaluate_ghost_if_negative_g():
    res = evaluate_locks_fixed_trial(GaugedSweepKnobs(g3=-1.0))
    assert not res.ghost_free
    assert res.loss >= 100.0


def test_monte_carlo_gate_h_s():
    rep = run_locks_fixed_monte_carlo(n_samples=24, seed=1)
    assert rep["schema"] == "invariant_hunt.gauged_meta_sweep.v1"
    assert rep["wg_residual_max"] < 1e-12
    assert rep["ghost_free_fraction"] == 1.0
    assert rep["gate_H_S"]["pass"]


def test_optuna_locks_fixed_gate():
    rep = run_locks_fixed_optuna(n_trials=12, seed=0)
    assert rep["mode"] == "locks_fixed_optuna"
    assert rep["gate_H_S"]["pass"]
    assert rep["lock_residual"] == 0.0
    assert "g3" in rep["best_params"]
    # Must not re-open free search over wg_base
    assert "wg_base" not in rep["best_params"]
    assert "braiding_target" not in rep["best_params"]


def test_pde_probe_runs():
    res = evaluate_locks_fixed_trial(
        GaugedSweepKnobs(gauge_flux=0.01),
        pde_probe=True,
        pde_nx=6,
        pde_nt=20,
        seed=3,
    )
    assert "pde_final_mean" in res.components
    assert res.ghost_free
