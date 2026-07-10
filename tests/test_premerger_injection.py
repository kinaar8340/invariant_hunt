"""Pre-merger injection recovery unit test (synthetic)."""

import numpy as np

from src.gw_events import GW150914
from src.invariants import InvariantSet
from src.network_likelihood import DetectorWhitened
from src.premerger_phase import premerger_injection_recovery
from src.premerger_theory import PremergerPhaseModel, phase_basis_template, orbital_phase_from_strain
from src.whiten import PSDEstimate


def _fake_det(name: str, n: int = 4096, fs: float = 4096.0) -> DetectorWhitened:
    rng = np.random.default_rng(abs(hash(name)) % (2**31))
    t = np.linspace(-1.0, 0.05, n)
    # GR-like chirp in whitened domain
    phase = 2 * np.pi * (40 * (t - t[0]) + 10 * (t - t[0]) ** 2)
    h = np.cos(phase)
    residual = 0.3 * rng.standard_normal(n)
    psd = PSDEstimate(
        freqs=np.linspace(0, fs / 2, 64),
        psd=np.ones(64),
        sample_rate=fs,
        nperseg=64,
    )
    return DetectorWhitened(
        detector=name,
        t_rel=t,
        strain_raw=h,
        strain_w=h + residual,
        residual_w=residual,
        pe_template_w=h,
        psd=psd,
        whiten_scale=1.0,
        pe_lag_s=0.0,
        pe_a_plus=1.0,
        pe_a_cross=0.0,
        pe_chi2=0.0,
        pe_snr_proxy=10.0,
        sample_rate=fs,
        path="fake",
    )


def test_injection_recovers_alpha_on_noise():
    dets = [_fake_det("H1"), _fake_det("L1")]
    # Use noise into path with coherent injections
    out = premerger_injection_recovery(
        dets,
        GW150914,
        alpha_injs=[0.0, 0.01],
        into="noise",
        t_end=-0.05,
        gate_dchi2=1.0,  # loose for short synthetic
        seed=1,
    )
    rows = {r["alpha_inj"]: r for r in out["rows"]}
    # recovery at finite injection should be closer to truth than background
    assert abs(rows[0.01]["alpha_hat"] - 0.01) < abs(rows[0.0]["alpha_hat"] - 0.01) + 0.05
