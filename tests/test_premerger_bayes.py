"""Tests for pre-merger Bayes factor (topo vs GR)."""

from __future__ import annotations

import math

import numpy as np

from src.premerger_bayes import (
    ALPHA_PRIOR_SIGMA,
    bayes_factor_from_vectors,
    kass_raftery_grade,
)


def test_prior_sigma_preregistered():
    assert abs(ALPHA_PRIOR_SIGMA - 1e-3) < 1e-15


def test_bf_zero_injection_favors_gr():
    rng = np.random.default_rng(0)
    n = 5000
    tau = rng.normal(0, 1.0, size=n)
    tau = tau / np.linalg.norm(tau) * 50.0  # moderate SNR capacity
    r = rng.normal(0, 1.0, size=n)  # pure noise
    bf = bayes_factor_from_vectors(r, tau, alpha_prior_sigma=1e-3)
    # Occam penalty: should not strongly prefer topo on pure noise
    assert bf.ln_B_10 < 2.0
    assert bf.delta_chi2 >= -1e-6


def test_bf_loud_injection_favors_topo():
    rng = np.random.default_rng(1)
    n = 8000
    tau = rng.normal(0, 1.0, size=n)
    # Loud: α·||τ|| ≫ 1 so Δχ² large even with σ_prior=1e-3
    tau = tau / (np.linalg.norm(tau) + 1e-30) * 5000.0
    alpha_true = 5e-4
    r = alpha_true * tau + rng.normal(0, 1.0, size=n)
    bf = bayes_factor_from_vectors(r, tau, alpha_prior_sigma=1e-3)
    assert bf.ln_B_10 > 3.0
    # MLE within ~noise: σ_α = 1/||τ|| ≈ 2e-4
    assert abs(bf.alpha_hat_mle - alpha_true) < 5.0 * bf.alpha_sigma_mle
    assert "topo" in bf.kass_raftery


def test_savage_dickey_matches_exact():
    rng = np.random.default_rng(2)
    n = 3000
    tau = rng.normal(0, 1.0, size=n)
    r = 2e-4 * tau + rng.normal(0, 1.0, size=n)
    bf = bayes_factor_from_vectors(r, tau, alpha_prior_sigma=1e-3)
    assert abs(bf.ln_B_10 - bf.ln_B_10_savage_dickey) < 1e-6


def test_kass_raftery_labels():
    assert "GR" in kass_raftery_grade(-5.0)
    assert "topo" in kass_raftery_grade(5.0)


def test_map_shrinks_toward_zero():
    """MAP with finite prior should shrink vs MLE for weak signals."""
    rng = np.random.default_rng(3)
    n = 2000
    tau = rng.normal(0, 1.0, size=n)
    tau = tau / (np.linalg.norm(tau) + 1e-30) * 20.0
    r = 1e-5 * tau + rng.normal(0, 1.0, size=n)
    bf = bayes_factor_from_vectors(r, tau, alpha_prior_sigma=1e-3)
    # |MAP| <= |MLE| typically under zero-mean prior
    assert abs(bf.alpha_hat_map) <= abs(bf.alpha_hat_mle) + 1e-12
