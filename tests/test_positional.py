"""Tests for positional 350/π interpretation."""

import math

from src.invariants import LOCKED_WG
from src.positional import (
    PositionalPhase,
    burst_loci,
    phase_to_frequency,
    phase_to_timing_offset,
    positional_hopf_residual,
)
from src.predictions import gw_echo_delay, gw_burst_spectrum, write_prediction_bundle
from pathlib import Path


def test_fiber_angle_site_zero():
    p = PositionalPhase(lattice_index=0)
    assert p.fiber_angle == 0.0
    assert p.lattice_phase_unit == 0.0


def test_fiber_angle_full_winding():
    # after W_g sites, angle advances by 2π
    p = PositionalPhase(wg=LOCKED_WG, lattice_index=0, fractional_offset=1.0)
    # fractional_offset=1 wraps unit phase to 0
    assert abs(p.lattice_phase_unit) < 1e-12


def test_timing_offset_scales_with_period():
    p = PositionalPhase(wg=LOCKED_WG, lattice_index=1)
    dt1 = phase_to_timing_offset(p, base_period=1.0)
    dt2 = phase_to_timing_offset(p, base_period=2.0)
    assert abs(dt2 - 2 * dt1) < 1e-12
    assert abs(dt1 - (1.0 / LOCKED_WG)) < 1e-12


def test_frequency_positive():
    f = phase_to_frequency(scale_hz=250.0)
    assert f > 0
    p = PositionalPhase(lattice_index=3)
    f2 = phase_to_frequency(p, scale_hz=250.0)
    assert f2 > 0


def test_burst_loci_count():
    loci = burst_loci(5)
    assert len(loci) == 5
    assert loci[0]["site"] == 0.0


def test_positional_residual_at_lock():
    assert positional_hopf_residual(LOCKED_WG, 350.0) < 1e-12


def test_gw_predictions():
    delay = gw_echo_delay(mass_solar=30.0, lattice_index=1)
    assert delay.value > 0
    assert delay.unit == "s"
    assert "falsify" in delay.falsify_if.lower() or "If" in delay.falsify_if

    freq = gw_burst_spectrum(scale_hz=250.0)
    assert freq.value > 0
    assert freq.passes(freq.value)  # exact match
    assert not freq.passes(freq.value + 10 * freq.uncertainty)


def test_write_bundle(tmp_path: Path):
    recs = [gw_echo_delay(lattice_index=1), gw_burst_spectrum()]
    path = write_prediction_bundle(recs, tmp_path / "bundle.json")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "prediction_bundle" in text
