"""Tests for pre-registered mapping v3 scaffolding (no PE)."""

from __future__ import annotations

import numpy as np

from src.premerger_mapping_v3 import (
    INV_SNR_POWER_DEFAULT,
    NETWORK_SNR_GWTC1,
    RHO_REF,
    MappingV3FitResult,
    PremergerPhaseModelV3,
    evaluate_v3_campaign,
    evaluate_v3_family,
    phase_basis_template_v3,
    predict_honesty_v3,
)
from src.premerger_theory import orbital_phase_from_strain, phase_basis_template


def test_defaults_preregistered():
    assert abs(INV_SNR_POWER_DEFAULT - 1.0) < 1e-15
    assert abs(RHO_REF - 24.4) < 1e-12
    assert NETWORK_SNR_GWTC1["GW170809"] == 12.4
    assert NETWORK_SNR_GWTC1["GW150914"] == 24.4


def test_inv_snr_scale_factor():
    m = PremergerPhaseModelV3(
        scale_mode="inv_snr",
        scale_power=1.0,
        scale_value=12.2,
        scale_ref=24.4,
    )
    assert abs(m.scale_factor - 2.0) < 1e-12


def test_distance_scale_factor():
    m = PremergerPhaseModelV3(
        scale_mode="distance",
        scale_power=1.0,
        scale_value=880.0,
        scale_ref=440.0,
    )
    assert abs(m.scale_factor - 2.0) < 1e-12


def test_q0_is_unity():
    m = PremergerPhaseModelV3(
        scale_mode="inv_snr",
        scale_power=0.0,
        scale_value=12.4,
        scale_ref=24.4,
    )
    assert abs(m.scale_factor - 1.0) < 1e-12


def test_tau_v3_scales_tau0():
    fs = 4096.0
    t = np.arange(0, 0.5, 1 / fs)
    h = np.cos(2 * np.pi * 50 * t)
    phi = orbital_phase_from_strain(h, fs)
    v3 = PremergerPhaseModelV3(
        scale_mode="inv_snr",
        scale_power=1.0,
        scale_value=12.2,
        scale_ref=24.4,
    )
    tau0 = phase_basis_template(h, phi, v3.base_model())
    tau3 = phase_basis_template_v3(h, phi, v3)
    assert np.allclose(tau3, 2.0 * tau0)


def test_honesty_inv_snr_short_of_12():
    h = predict_honesty_v3()
    assert h["inv_snr_q1_ratio"] < 3.0
    assert h["empirical_alpha_ratio_v1"] > 10.0
    assert h["distance_s1_ratio"] < 3.0


def _fake_fit(
    event: str,
    alpha0: float,
    sig: float,
    scale: float,
    *,
    gate: bool = True,
    lnb: float = 100.0,
) -> MappingV3FitResult:
    return MappingV3FitResult(
        event=event,
        mapping="v3_inv_snr_p1",
        scale_mode="inv_snr",
        scale_power=1.0,
        scale_value=12.4 if "809" in event else 24.4,
        scale_ref=24.4,
        scale_factor=scale,
        alpha_0_hat=alpha0,
        alpha_0_sigma=sig,
        beta_eff=alpha0 * scale,
        chi2_gr=1000.0,
        chi2_topo=100.0,
        delta_chi2=900.0,
        ln_B_10=lnb,
        B_10=1e40,
        kass_raftery="very_strong_topo",
        gate_p_v3_pass=gate,
        gate_p_v1_pass=True,
        alpha_v1_hat=alpha0 * scale,
        notes=[],
    )


def test_evaluate_v3_falsify_unify():
    r809 = _fake_fit("GW170809", alpha0=4e-4, sig=2e-5, scale=2.0)
    r914 = _fake_fit("GW150914", alpha0=7e-5, sig=1e-5, scale=1.0)
    camp = evaluate_v3_campaign(
        {"GW170809": r809, "GW150914": r914},
        scale_mode="inv_snr",
        scale_power=1.0,
    )
    assert camp["verdict"] == "FALSIFY"
    assert camp["unify_ok"] is False


def test_evaluate_v3_success_unify():
    r809 = _fake_fit("GW170809", alpha0=7.0e-5, sig=1e-5, scale=2.0)
    r914 = _fake_fit("GW150914", alpha0=7.1e-5, sig=1e-5, scale=1.0)
    camp = evaluate_v3_campaign(
        {"GW170809": r809, "GW150914": r914},
        scale_mode="inv_snr",
        scale_power=1.0,
    )
    assert camp["verdict"] == "SUCCESS"
    assert camp["unify_ok"] is True


def test_family_closed_when_both_falsify():
    a = {"verdict": "FALSIFY", "reason": "a"}
    b = {"verdict": "FALSIFY", "reason": "b"}
    fam = evaluate_v3_family(a, b)
    assert fam["family_verdict"] == "FALSIFY"
    assert fam["bulk_pe_power_family_closed"] is True
