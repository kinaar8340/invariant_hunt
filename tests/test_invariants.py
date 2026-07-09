"""Tests for formalized topological invariants."""

import math

from src.invariants import (
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
    burst_threshold,
    geometric_winding_from_base,
    hopf_penalty,
    link_saturation_theta,
)


def test_locked_wg_value():
    assert abs(LOCKED_WG - WG_BASE / math.pi) < 1e-12
    assert abs(LOCKED_WG - 111.408) < 0.01


def test_link_saturation_near_pi():
    theta = link_saturation_theta(LOCKED_WG)
    assert abs(theta - math.pi) / math.pi < 0.01


def test_burst_threshold():
    assert abs(burst_threshold(0.85) - math.pi * 1.85) < 1e-12


def test_invariant_set_lock():
    inv = InvariantSet()
    assert inv.is_locked()
    assert inv.wg == LOCKED_WG
    assert "wg_vs_350_over_pi" in inv.lock_residuals()


def test_from_monitor_stats():
    stats = {
        "geometric_winding": LOCKED_WG,
        "braiding_phase": 0.8145,
        "stability_score": 8.0,
        "bursts_per_step": 0.05,
    }
    inv = InvariantSet.from_monitor_stats(stats)
    assert inv.is_locked()
    assert inv.braiding_phase == 0.8145


def test_hopf_penalty_zero_at_lock():
    assert hopf_penalty(LOCKED_WG, WG_BASE) < 1e-12


def test_geometric_winding():
    assert abs(geometric_winding_from_base(350.0) - LOCKED_WG) < 1e-12
