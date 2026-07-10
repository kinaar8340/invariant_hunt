"""Tests for pre-registered mapping v4 scaffolding (no PE)."""

from __future__ import annotations

import numpy as np

from src.premerger_mapping_v4 import (
    MASS_POWER_DEFAULT,
    M_F_REF,
    REMNANT_MASS_CATALOG,
    MappingV4FitResult,
    PremergerPhaseModelV4,
    evaluate_v4_campaign,
    phase_basis_template_v4,
    predict_honesty_v4,
    remnant_mass_solar,
)
from src.premerger_theory import orbital_phase_from_strain, phase_basis_template


def test_defaults_preregistered():
    assert abs(MASS_POWER_DEFAULT - 1.0) < 1e-15
    assert abs(M_F_REF - 63.1) < 1e-12
    assert REMNANT_MASS_CATALOG["GW170809"] == 56.3


def test_remnant_mass_lookup():
    assert remnant_mass_solar("GW150914") == 63.1
    assert remnant_mass_solar("GW170809") == 56.3


def test_scale_factor_p1():
    m = PremergerPhaseModelV4(
        m_f_solar=126.2, mass_power=1.0, m_f_ref_solar=63.1
    )
    assert abs(m.scale_factor - 2.0) < 1e-12


def test_scale_factor_p0_unity():
    m = PremergerPhaseModelV4(
        m_f_solar=56.3, mass_power=0.0, m_f_ref_solar=63.1
    )
    assert abs(m.scale_factor - 1.0) < 1e-12


def test_tau_v4_scales_tau0():
    fs = 4096.0
    t = np.arange(0, 0.5, 1 / fs)
    h = np.cos(2 * np.pi * 50 * t)
    phi = orbital_phase_from_strain(h, fs)
    v4 = PremergerPhaseModelV4(
        m_f_solar=126.2, mass_power=1.0, m_f_ref_solar=63.1
    )
    tau0 = phase_basis_template(h, phi, v4.base_model())
    tau4 = phase_basis_template_v4(h, phi, v4)
    assert np.allclose(tau4, 2.0 * tau0)


def test_honesty_wrong_way():
    h = predict_honesty_v4(p=1.0)
    assert h["beta_ratio_if_shared_alpha0"] < 1.0
    assert h["empirical_alpha_ratio_v1"] > 10.0


def test_evaluate_v4_falsify_closes_family():
    r809 = MappingV4FitResult(
        event="GW170809",
        mapping="v4_remnant_mass",
        mass_power=1.0,
        m_f_solar=56.3,
        m_f_ref_solar=63.1,
        scale_factor=56.3 / 63.1,
        alpha_0_hat=9e-4,
        alpha_0_sigma=2e-5,
        beta_eff=8e-4,
        chi2_gr=1000.0,
        chi2_topo=100.0,
        delta_chi2=900.0,
        ln_B_10=100.0,
        B_10=1e40,
        kass_raftery="very_strong_topo",
        gate_p_v4_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=8e-4,
        notes=[],
    )
    r914 = MappingV4FitResult(
        event="GW150914",
        mapping="v4_remnant_mass",
        mass_power=1.0,
        m_f_solar=63.1,
        m_f_ref_solar=63.1,
        scale_factor=1.0,
        alpha_0_hat=7e-5,
        alpha_0_sigma=1e-5,
        beta_eff=7e-5,
        chi2_gr=100.0,
        chi2_topo=70.0,
        delta_chi2=30.0,
        ln_B_10=10.0,
        B_10=2e4,
        kass_raftery="very_strong_topo",
        gate_p_v4_pass=True,
        gate_p_v1_pass=True,
        alpha_v1_hat=7e-5,
        notes=[],
    )
    camp = evaluate_v4_campaign({"GW170809": r809, "GW150914": r914})
    assert camp["verdict"] == "FALSIFY"
    assert camp["unify_ok"] is False
    assert camp["remnant_mass_family_closed"] is True
