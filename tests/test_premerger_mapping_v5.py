"""Tests for pre-registered mapping v5 scaffolding (no PE)."""

from __future__ import annotations

import math

import numpy as np

from src.invariants import LOCKED_WG
from src.premerger_mapping_v4 import M_F_REF, REMNANT_MASS_CATALOG
from src.premerger_mapping_v5 import (
    MappingV5FitResult,
    PremergerPhaseModelV5,
    evaluate_v5_campaign,
    lambda_hopf,
    phase_basis_template_v5,
    predict_honesty_v5,
    theta_link_locked,
)
from src.premerger_theory import orbital_phase_from_strain, phase_basis_template


def test_theta_link_near_pi():
    th = theta_link_locked(LOCKED_WG)
    assert 3.0 < th < math.pi
    assert abs(th / math.pi - 0.9955) < 1e-3


def test_lambda_primary_at_ref_is_lambda0():
    lam = lambda_hopf(M_F_REF, m_f_ref_solar=M_F_REF)
    lam0 = theta_link_locked() / math.pi
    assert abs(lam - lam0) < 1e-12


def test_lambda_inverse_mass_ratio():
    m914 = REMNANT_MASS_CATALOG["GW150914"]
    m809 = REMNANT_MASS_CATALOG["GW170809"]
    l914 = lambda_hopf(m914, m_f_ref_solar=m914)
    l809 = lambda_hopf(m809, m_f_ref_solar=m914)
    assert abs((l809 / l914) - (m914 / m809)) < 1e-12


def test_control_event_independent():
    a = lambda_hopf(56.3, control=True)
    b = lambda_hopf(63.1, control=True)
    assert abs(a - b) < 1e-15


def test_tau_v5_scales_tau0():
    fs = 4096.0
    t = np.arange(0, 0.5, 1 / fs)
    h = np.cos(2 * np.pi * 50 * t)
    phi = orbital_phase_from_strain(h, fs)
    # choose M_f so Λ = 2 * λ0
    m_f = M_F_REF / 2.0
    v5 = PremergerPhaseModelV5(m_f_solar=m_f, m_f_ref_solar=M_F_REF)
    assert abs(v5.scale_factor - 2.0 * v5.lambda_0) < 1e-12
    tau0 = phase_basis_template(h, phi, v5.base_model())
    tau5 = phase_basis_template_v5(h, phi, v5)
    assert np.allclose(tau5, v5.scale_factor * tau0)


def test_honesty_short_of_12():
    h = predict_honesty_v5()
    assert h["beta_ratio_if_shared_alpha0"] < 2.0
    assert h["empirical_alpha_ratio_v1"] > 10.0


def test_evaluate_v5_falsify_closes_family():
    r809 = MappingV5FitResult(
        event="GW170809",
        mapping="v5_hopf_lambda",
        m_f_solar=56.3,
        m_f_ref_solar=63.1,
        theta_link=3.12,
        lambda_0=0.995,
        scale_factor=1.12,
        alpha_0_hat=7e-4,
        alpha_0_sigma=2e-5,
        beta_eff=8e-4,
        chi2_gr=1000.0,
        chi2_topo=100.0,
        delta_chi2=900.0,
        ln_B_10=100.0,
        B_10=1e40,
        kass_raftery="very_strong_topo",
        gate_p_v5_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=8e-4,
        notes=[],
    )
    r914 = MappingV5FitResult(
        event="GW150914",
        mapping="v5_hopf_lambda",
        m_f_solar=63.1,
        m_f_ref_solar=63.1,
        theta_link=3.12,
        lambda_0=0.995,
        scale_factor=0.995,
        alpha_0_hat=7e-5,
        alpha_0_sigma=1e-5,
        beta_eff=7e-5,
        chi2_gr=100.0,
        chi2_topo=70.0,
        delta_chi2=30.0,
        ln_B_10=10.0,
        B_10=2e4,
        kass_raftery="very_strong_topo",
        gate_p_v5_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=7e-5,
        notes=[],
    )
    camp = evaluate_v5_campaign({"GW170809": r809, "GW150914": r914})
    assert camp["verdict"] == "FALSIFY"
    assert camp["unify_ok"] is False
    assert camp["hopf_lambda_family_closed"] is True
