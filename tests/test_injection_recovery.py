"""Injection recovery smoke tests (no PE required for noise path)."""

import numpy as np

from src.echo_ladder import primary_and_echo_basis, fit_two_amplitudes, chi2, fit_amplitude
from src.gw_events import GW150914
from src.invariants import InvariantSet


def test_injection_recovers_positive_a1():
    inv = InvariantSet()
    fs = 4096.0
    t = np.arange(0.0, 0.1, 1.0 / fs)
    primary, echoes, _ = primary_and_echo_basis(
        t, GW150914, inv, n_echoes=3, mode="geometric"
    )
    sigma = 1.0
    peak = float(np.max(np.abs(echoes))) + 1e-60
    unit = echoes / peak * sigma
    a_inj = 3.0
    rng = np.random.default_rng(1)
    data = a_inj * unit + 0.2 * sigma * rng.standard_normal(t.shape)

    a0, a1 = fit_two_amplitudes(data, primary, unit, sigma)
    assert a1 > 1.0  # recovers substantial positive scale
    a0_only = fit_amplitude(data, primary, sigma)
    dchi = chi2(data, a0_only * primary, sigma) - chi2(data, a0 * primary + a1 * unit, sigma)
    assert dchi > 2.0
