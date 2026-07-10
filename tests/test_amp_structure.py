"""Amplitude structure weight tests."""

import math

from src.amp_structure import AMP_STRUCTURES, normalize_weights, step_weight
from src.echo_ladder import build_ladder
from src.gw_events import GW150914
from src.invariants import InvariantSet


def test_all_structures_nonneg():
    inv = InvariantSet()
    for s in AMP_STRUCTURES:
        for n in range(1, 6):
            w = step_weight(n, braiding_angle=0.1 * n, inv=inv, structure=s)
            assert w >= 0.0


def test_normalize_l2():
    w = normalize_weights([3.0, 4.0])
    assert abs(math.sqrt(sum(x * x for x in w)) - 1.0) < 1e-12


def test_build_ladder_structures_differ():
    inv = InvariantSet()
    g = build_ladder(GW150914, inv, n_echoes=5, amp_structure="geometric")
    b = build_ladder(GW150914, inv, n_echoes=5, amp_structure="braiding")
    f = build_ladder(GW150914, inv, n_echoes=5, amp_structure="flux_kappa")
    # not all identical shapes
    wg = [s.amp_prior for s in g]
    wb = [s.amp_prior for s in b]
    wf = [s.amp_prior for s in f]
    assert wg != wb or wg != wf
    # L2 normalized
    assert abs(math.sqrt(sum(x * x for x in wg)) - 1.0) < 1e-9


def test_geometric_decay_shape():
    inv = InvariantSet()
    steps = build_ladder(
        GW150914, inv, n_echoes=4, amp_structure="geometric", normalize_amps=False
    )
    raw = [s.amp_prior for s in steps]
    # amp0^n with amp0=0.35
    assert abs(raw[0] - 0.35) < 1e-12
    assert abs(raw[1] - 0.35**2) < 1e-12
