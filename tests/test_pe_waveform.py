"""PE waveform + residual tests (requires pycbc + PE HDF5 cache)."""

from pathlib import Path

import numpy as np
import pytest

from src.gw_events import GW150914

PE = Path(__file__).resolve().parent.parent / "data" / "pe" / "GW150914_GWTC-1.hdf5"
pycbc = pytest.importorskip("pycbc", reason="pycbc not installed")


@pytest.mark.skipif(not PE.exists(), reason="GW150914 PE HDF5 not cached")
def test_load_pe_medians():
    from src.pe_waveform import load_pe_medians

    p = load_pe_medians("GW150914", pe_dir=PE.parent)
    assert p.mass1 > p.mass2 > 0
    assert 30 < p.mass1 < 50
    assert 200 < p.distance_mpc < 800
    assert p.n_samples > 100


@pytest.mark.skipif(not PE.exists(), reason="GW150914 PE HDF5 not cached")
def test_generate_and_place():
    from src.pe_waveform import (
        generate_imr_polarizations,
        load_pe_medians,
        place_template_on_grid,
    )

    p = load_pe_medians("GW150914", pe_dir=PE.parent)
    hp, hc, dt = generate_imr_polarizations(p, sample_rate=4096.0)
    assert hp.size == hc.size
    assert abs(dt - 1 / 4096) < 1e-12
    t = np.arange(-0.2, 0.2, dt)
    g = place_template_on_grid(hp, t, peak_time_rel=0.0, sample_rate=4096.0)
    assert g.shape == t.shape
    # peak near t=0
    i = int(np.argmax(np.abs(g)))
    assert abs(t[i]) < 0.01


@pytest.mark.skipif(not PE.exists(), reason="GW150914 PE HDF5 not cached")
def test_fit_recovers_injected():
    """Inject a PE template into noise and recover lag / amplitude."""
    from src.pe_waveform import (
        fit_pe_to_strain,
        generate_imr_polarizations,
        load_pe_medians,
        place_template_on_grid,
    )

    params = load_pe_medians("GW150914", pe_dir=PE.parent)
    fs = 4096.0
    t = np.arange(-0.2, 0.15, 1.0 / fs)
    hp, hc, _ = generate_imr_polarizations(params, sample_rate=fs)
    true_lag = 0.005
    true_ap, true_ac = 1.2, -0.4
    signal = true_ap * place_template_on_grid(hp, t, true_lag, fs)
    signal = signal + true_ac * place_template_on_grid(hc, t, true_lag, fs)
    # mild noise
    rng = np.random.default_rng(0)
    sigma = 0.05 * np.std(signal)
    data = signal + sigma * rng.standard_normal(t.shape)

    fit = fit_pe_to_strain(
        t,
        data,
        params,
        sample_rate=fs,
        sigma=sigma,
        f_low=20.0,
        f_high=500.0,
        lag_min=-0.02,
        lag_max=0.02,
        fit_t_min=-0.15,
        fit_t_max=0.05,
    )
    assert abs(fit.lag_s - true_lag) < 2.0 / fs + 1e-4
    assert abs(fit.a_plus - true_ap) / abs(true_ap) < 0.25
