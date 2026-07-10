"""Tests for coherent complex amplitude + delay scale scan."""

import numpy as np

from src.coherent_echo import (
    coherent_echo_basis,
    delay_scale_scan,
    fit_coherent_echoes,
    lee_corrected_threshold,
)
from src.gw_events import GW150914
from src.invariants import InvariantSet


def test_lee_threshold_grows_with_trials():
    assert lee_corrected_threshold(4.0, 1) == 4.0
    assert lee_corrected_threshold(4.0, 21) > 4.0


def test_coherent_recovers_injected_complex_amp():
    inv = InvariantSet()
    fs = 4096.0
    t = np.arange(0.0, 0.12, 1.0 / fs)
    primary, e_cos, e_sin, steps = coherent_echo_basis(
        t, GW150914, inv, n_echoes=4, mode="geometric", delay_scale=1.0
    )
    assert len(steps) == 4
    true_ac, true_as = 2.0, -1.5
    sigma = 0.05 * max(np.max(np.abs(e_cos)), 1e-30)
    rng = np.random.default_rng(0)
    data = true_ac * e_cos + true_as * e_sin + sigma * rng.standard_normal(t.shape)

    fit = fit_coherent_echoes(
        data, t, GW150914, inv, sigma=sigma, n_echoes=4, delay_scale=1.0
    )
    assert fit.delta_chi2 > 10
    assert abs(fit.a_cos - true_ac) / abs(true_ac) < 0.3
    assert abs(fit.a_sin - true_as) / abs(true_as) < 0.3


def test_delay_scan_finds_injected_scale():
    inv = InvariantSet()
    fs = 4096.0
    t = np.arange(0.0, 0.12, 1.0 / fs)
    true_s = 1.1
    primary, e_cos, e_sin, _ = coherent_echo_basis(
        t, GW150914, inv, n_echoes=3, delay_scale=true_s
    )
    sigma = 0.05 * (np.max(np.abs(e_cos)) + 1e-30)
    rng = np.random.default_rng(1)
    data = 2.5 * e_cos + sigma * rng.standard_normal(t.shape)

    scan = delay_scale_scan(
        data,
        t,
        GW150914,
        inv,
        sigma=sigma,
        n_echoes=3,
        scan_min=0.85,
        scan_max=1.15,
        n_scales=13,
        gate_a_threshold=4.0,
    )
    assert scan.best.delta_chi2 > scan.nominal_delta_chi2 - 1e-6
    # best scale near truth
    assert abs(scan.best.delay_scale - true_s) < 0.08
