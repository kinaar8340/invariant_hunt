"""Unit tests for Gate S-1 systematics scoring (no PE download)."""

from __future__ import annotations

from src.premerger_systematics import (
    CORR_R_TAU_FLAG,
    score_systematics_verdict,
)


def test_high_corr_alone_is_soft_robust_anomaly():
    """Loud τ projection implies high corr; alone does not force SYSTEMATICS_RISK."""
    approx = [
        {
            "approximant": "IMRPhenomD",
            "alpha_hat": 8e-4,
            "gate_p_pass": True,
            "error": None,
        },
        {
            "approximant": "IMRPhenomXAS",
            "alpha_hat": 7e-4,
            "gate_p_pass": True,
            "error": None,
        },
    ]
    jitter = [
        {"label": "nominal", "alpha_hat": 8e-4, "gate_p_pass": True, "error": None},
        {"label": "m+3%", "alpha_hat": 8.5e-4, "gate_p_pass": True, "error": None},
    ]
    corr = {
        "detectors": {
            "H1": {"corr_r_tau": 0.25},
            "L1": {"corr_r_tau": 0.22},
        }
    }
    v = score_systematics_verdict(approx, jitter, None, corr)
    assert v["verdict"] == "ROBUST_ANOMALY"
    assert v["soft_flags"]
    assert v["hard_flags"] == []
    assert v["max_abs_corr_r_tau"] >= CORR_R_TAU_FLAG


def test_high_corr_plus_sign_flip_is_systematics():
    approx = [
        {"approximant": "A", "alpha_hat": 8e-4, "gate_p_pass": True, "error": None},
        {"approximant": "B", "alpha_hat": 8e-4, "gate_p_pass": True, "error": None},
    ]
    jitter = [
        {"label": "nominal", "alpha_hat": 8e-4, "gate_p_pass": True, "error": None},
        {"label": "m+3%", "alpha_hat": -8e-4, "gate_p_pass": True, "error": None},
    ]
    corr = {"detectors": {"H1": {"corr_r_tau": 0.3}, "L1": {"corr_r_tau": 0.2}}}
    v = score_systematics_verdict(approx, jitter, None, corr)
    assert v["verdict"] == "SYSTEMATICS_RISK"
    assert "mass_plus_sign_flip" in v["hard_flags"]


def test_robust_anomaly_clean():
    approx = [
        {"approximant": "A", "alpha_hat": 1e-4, "gate_p_pass": True, "error": None},
        {"approximant": "B", "alpha_hat": 1.1e-4, "gate_p_pass": True, "error": None},
        {"approximant": "C", "alpha_hat": 0.9e-4, "gate_p_pass": True, "error": None},
    ]
    jitter = [
        {"label": "nominal", "alpha_hat": 1e-4, "gate_p_pass": True, "error": None},
        {"label": "m+3%", "alpha_hat": 1.05e-4, "gate_p_pass": True, "error": None},
        {"label": "m-3%", "alpha_hat": 0.95e-4, "gate_p_pass": True, "error": None},
    ]
    corr = {"detectors": {"H1": {"corr_r_tau": 0.02}, "L1": {"corr_r_tau": 0.03}}}
    draws = {
        "n_ok": 10,
        "pass_frac": 0.8,
        "frac_positive": 0.9,
    }
    v = score_systematics_verdict(approx, jitter, draws, corr)
    assert v["verdict"] == "ROBUST_ANOMALY"
    assert v["flags"] == []


def test_sign_flip_flag():
    approx = [
        {"approximant": "A", "alpha_hat": 1e-4, "gate_p_pass": True, "error": None},
        {"approximant": "B", "alpha_hat": 1e-4, "gate_p_pass": True, "error": None},
    ]
    jitter = [
        {"label": "nominal", "alpha_hat": 1e-4, "gate_p_pass": True, "error": None},
        {"label": "m+3%", "alpha_hat": -1e-4, "gate_p_pass": True, "error": None},
    ]
    corr = {"detectors": {"H1": {"corr_r_tau": 0.01}, "L1": {"corr_r_tau": 0.01}}}
    v = score_systematics_verdict(approx, jitter, None, corr)
    assert "mass_plus_sign_flip" in v["flags"]
    assert v["verdict"] == "SYSTEMATICS_RISK"


def test_inconclusive_no_approx():
    v = score_systematics_verdict([], [], None, None)
    assert v["verdict"] == "INCONCLUSIVE"
