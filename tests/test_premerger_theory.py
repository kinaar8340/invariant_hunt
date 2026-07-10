"""Pre-merger phase theory / fit unit tests."""

import numpy as np

from src.premerger_theory import (
    PremergerPhaseModel,
    apply_phase_shift,
    orbital_phase_from_strain,
    phase_basis_template,
    premerger_predictions,
)


def test_coupling_kernel():
    m = PremergerPhaseModel(wg=111.4, phi_b=0.8145)
    assert abs(m.coupling_kernel()) > 1.0


def test_phase_basis_recovers_small_alpha():
    fs = 4096.0
    t = np.arange(0, 1.0, 1 / fs)
    f0, f1 = 40.0, 60.0
    phase = 2 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t**2 / t[-1])
    h = np.cos(phase)
    phi_orb = orbital_phase_from_strain(h, fs)
    # normalize phase so max |Δφ| stays ≪ 1 for linearization
    phi_orb = phi_orb / (np.max(np.abs(phi_orb)) + 1e-30)
    model = PremergerPhaseModel(wg=1.0, phi_b=0.0)  # K=1
    tau = phase_basis_template(h, phi_orb, model)
    alpha_true = 0.02
    h_shift = apply_phase_shift(h, phi_orb, alpha_true, model)
    r = h_shift - h
    sl = slice(int(0.1 * fs), int(0.9 * fs))
    denom = float(np.sum(tau[sl] * tau[sl])) + 1e-30
    alpha_hat = float(np.sum(r[sl] * tau[sl]) / denom)
    assert abs(alpha_hat - alpha_true) / alpha_true < 0.35
    corr = np.corrcoef(r[sl], tau[sl])[0, 1]
    assert corr > 0.95


def test_predictions_keys():
    p = premerger_predictions(63.0, alpha=1e-4)
    assert "cumulative_delta_phi_rad" in p
    assert p["locks"]["wg"] > 100
