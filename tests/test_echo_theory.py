"""Analytic echo expectation tests."""

import math

from src.echo_theory import (
    ModelParams,
    amp_ratio_sync,
    delta_t_burst,
    expect_echoes,
    f_echo_physical_hz,
    f_lattice,
    sync_suppression_factor,
    theta_crit,
)
from src.invariants import LOCKED_WG


def test_theta_crit():
    assert abs(theta_crit(0.85) - math.pi * 1.85) < 1e-12


def test_f_lattice_from_locks():
    p = ModelParams()
    assert abs(f_lattice(p) - p.delta_omega / p.wg) < 1e-15
    assert abs(p.wg - LOCKED_WG) < 1e-9


def test_sync_suppression_small():
    s = sync_suppression_factor()
    assert 0 < s < 0.01  # ≪ 1
    a = amp_ratio_sync()
    assert a < 1e-4


def test_frequency_scales_inverse_mass():
    f1 = f_echo_physical_hz(30.0)
    f2 = f_echo_physical_hz(60.0)
    assert abs(f1 / f2 - 2.0) < 1e-9


def test_gw150914_not_detectable_sync():
    exp = expect_echoes("GW150914", snr_main=25.0)
    assert not exp.detectable_sync_at_snr2
    assert exp.snr_echo_sync is not None
    assert exp.snr_echo_sync < 1e-3


def test_delta_t_positive():
    assert delta_t_burst() > 100
