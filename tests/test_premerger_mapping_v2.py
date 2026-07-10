"""Tests for pre-registered mapping v2 scaffolding (no PE)."""

from __future__ import annotations

import numpy as np

from src.premerger_mapping_v2 import (
    MASS_POWER_DEFAULT,
    M_REF_SOLAR,
    PremergerPhaseModelV2,
    phase_basis_template_v2,
    predict_beta_ratio_gw170809_vs_150914,
)
from src.premerger_theory import PremergerPhaseModel, orbital_phase_from_strain, phase_basis_template


def test_defaults_preregistered():
    assert abs(MASS_POWER_DEFAULT - 1.0) < 1e-15
    assert abs(M_REF_SOLAR - 60.0) < 1e-15


def test_scale_factor_p1():
    m = PremergerPhaseModelV2(m_tot_solar=120.0, mass_power=1.0, m_ref_solar=60.0)
    assert abs(m.scale_factor - 2.0) < 1e-12


def test_scale_factor_p0_is_unity():
    m = PremergerPhaseModelV2(m_tot_solar=120.0, mass_power=0.0, m_ref_solar=60.0)
    assert abs(m.scale_factor - 1.0) < 1e-12


def test_tau_v2_scales_tau0():
    fs = 4096.0
    t = np.arange(0, 0.5, 1 / fs)
    h = np.cos(2 * np.pi * 50 * t)
    phi = orbital_phase_from_strain(h, fs)
    v2 = PremergerPhaseModelV2(m_tot_solar=120.0, mass_power=1.0, m_ref_solar=60.0)
    tau0 = phase_basis_template(h, phi, v2.base_model())
    tau2 = phase_basis_template_v2(h, phi, v2)
    assert np.allclose(tau2, 2.0 * tau0)


def test_beta_ratio_honesty_note():
    d = predict_beta_ratio_gw170809_vs_150914(p=1.0)
    assert d["beta_ratio_if_shared_alpha0"] < 2.0
    assert d["empirical_alpha_ratio_v1"] > 5.0


def test_evaluate_v2_campaign_falsify_mass_unify():
    from src.premerger_mapping_v2 import MappingV2FitResult, evaluate_v2_campaign

    r809 = MappingV2FitResult(
        event="GW170809",
        mapping="v2_mass_power",
        mass_power=1.0,
        m_tot_solar=60.0,
        m_ref_solar=60.0,
        scale_factor=1.0,
        alpha_0_hat=8e-4,
        alpha_0_sigma=2e-5,
        beta_eff=8e-4,
        chi2_gr=1000.0,
        chi2_topo=100.0,
        delta_chi2=900.0,
        ln_B_10=100.0,
        B_10=1e40,
        kass_raftery="very_strong_topo",
        gate_p_v2_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=8e-4,
        notes=[],
    )
    r914 = MappingV2FitResult(
        event="GW150914",
        mapping="v2_mass_power",
        mass_power=1.0,
        m_tot_solar=66.0,
        m_ref_solar=60.0,
        scale_factor=66 / 60,
        alpha_0_hat=7e-5,
        alpha_0_sigma=1e-5,
        beta_eff=7e-5 * 66 / 60,
        chi2_gr=100.0,
        chi2_topo=70.0,
        delta_chi2=30.0,
        ln_B_10=10.0,
        B_10=2e4,
        kass_raftery="very_strong_topo",
        gate_p_v2_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=7e-5,
        notes=[],
    )
    camp = evaluate_v2_campaign({"GW170809": r809, "GW150914": r914})
    assert camp["verdict"] == "FALSIFY"
    assert camp["mass_unify_ok"] is False
