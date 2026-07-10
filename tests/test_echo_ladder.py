"""Tests for event catalog and positional echo ladder."""

import numpy as np

from src.echo_ladder import (
    build_ladder,
    echo_delay_seconds,
    fit_amplitude,
    positional_echo_template,
)
from src.gw_events import GW150914, get_event
from src.invariants import InvariantSet


def test_get_event_gw150914():
    ev = get_event("gw150914")
    assert ev.name == "GW150914"
    assert abs(ev.mass_final_solar - 63.1) < 0.2
    assert ev.t_m > 0


def test_geometric_delay_resolvable():
    inv = InvariantSet()
    dt = echo_delay_seconds(1, 63.1, inv, mode="geometric")
    # ~ few ms for ~63 M_sun
    assert 1e-3 < dt < 2e-2
    # 4096 Hz sample duration
    assert dt > 1.0 / 4096.0


def test_phase_unit_smaller_than_geometric():
    inv = InvariantSet()
    d_g = echo_delay_seconds(1, 63.1, inv, mode="geometric")
    d_p = echo_delay_seconds(1, 63.1, inv, mode="phase_unit")
    assert d_p < d_g
    assert d_p / d_g < 0.05  # roughly 1/W_g


def test_ladder_length():
    steps = build_ladder(GW150914, n_echoes=5, mode="geometric")
    assert len(steps) == 5
    assert steps[0].delay_s < steps[1].delay_s
    assert steps[1].delay_s == steps[0].delay_s * 2


def test_template_and_fit():
    t = np.linspace(0, 0.1, 4096)
    h, steps = positional_echo_template(t, GW150914, n_echoes=3, mode="geometric")
    assert h.shape == t.shape
    assert len(steps) == 3
    a = fit_amplitude(2.5 * h, h, sigma=0.01)
    assert abs(a - 2.5) < 0.05


def test_two_amplitude_fit_recovers():
    from src.echo_ladder import fit_two_amplitudes, primary_and_echo_basis

    t = np.linspace(0, 0.1, 4096)
    p, e, _ = primary_and_echo_basis(t, GW150914, n_echoes=3, mode="geometric")
    obs = 3.0 * p + 1.5 * e
    a0, a1 = fit_two_amplitudes(obs, p, e, sigma=0.01)
    assert abs(a0 - 3.0) < 0.05
    assert abs(a1 - 1.5) < 0.05
