"""Tests for Phase 2.2 topological Yukawa / Gate SM-2 mass."""

from __future__ import annotations

import numpy as np

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG
from src.sm_yukawa import (
    PDG_MASSES_GEV,
    VEV_GEV,
    YukawaAnsatzParams,
    ckm_from_yukawas,
    evaluate_yukawa,
    gate_sm2_mass_report,
    mass_singular_values,
    optimize_yukawa,
    predict_spectrum,
    yukawa_matrix,
)


def test_yukawa_matrix_shape_and_locks():
    p = YukawaAnsatzParams()
    Yu = yukawa_matrix(p, "u")
    assert Yu.shape == (3, 3)
    assert np.isfinite(Yu).all()
    assert p.phi_b == DEFAULT_BRAIDING
    assert p.kappa == DEFAULT_KAPPA
    assert abs(p.wg - LOCKED_WG) < 1e-12


def test_masses_positive_ordered():
    p = YukawaAnsatzParams(y_u=1.0, beta_u=5.0, alpha_u=2.0)
    m = mass_singular_values(yukawa_matrix(p, "u"))
    assert len(m) == 3
    assert m[0] > 0 and m[1] > 0 and m[2] > 0
    assert m[0] <= m[1] <= m[2]


def test_ckm_unitary_approx():
    p = YukawaAnsatzParams()
    Yu = yukawa_matrix(p, "u")
    Yd = yukawa_matrix(p, "d")
    V = ckm_from_yukawas(Yu, Yd)
    # V should be approximately unitary
    I = V.conj().T @ V
    assert np.allclose(I, np.eye(3), atol=1e-8)


def test_predict_spectrum_keys():
    spec = predict_spectrum(YukawaAnsatzParams())
    for k in PDG_MASSES_GEV:
        assert k in spec["masses_GeV"]
    assert "Vus" in spec["ckm_abs"]
    assert abs(spec["locks"]["W_g"] - LOCKED_WG) < 1e-12


def test_evaluate_yukawa_chi2_finite():
    ev = evaluate_yukawa()
    assert np.isfinite(ev["chi2_total"])
    assert ev["chi2_mass"]["n"] == 9
    assert ev["locks"]["pass"]


def test_optimize_improves_or_equals():
    base = evaluate_yukawa(YukawaAnsatzParams())["chi2_total"]
    opt = optimize_yukawa(n_trials=24, seed=0)
    assert opt["best_loss"] <= base + 1e-6
    assert opt["evaluation"]["chi2_total"] == opt["best_loss"] or abs(
        opt["evaluation"]["chi2_total"] - opt["best_loss"]
    ) < 1e-3


def test_gate_sm2_mass_report_structure():
    # Few trials for CI speed; still must return schema and freeze locks
    r = gate_sm2_mass_report(n_trials=20, seed=1, optimize=True)
    assert r["schema"] == "invariant_hunt.gate_sm2.v1"
    assert r["criteria"]["structure"] is True
    assert r["criteria"]["locks_frozen"] is True
    assert r["criteria"]["sm1_still_pass"] is True
    assert r["grade"] in ("FAIL", "LOOSE", "TIGHT")
    assert r["discipline"]["locks_not_fitted"] is True
    # Locks in best params
    assert abs(r["best_params"]["phi_b"] - DEFAULT_BRAIDING) < 1e-12
    assert abs(r["best_params"]["wg"] - LOCKED_WG) < 1e-12


def test_vev_scale():
    assert VEV_GEV > 200.0
