"""GWOSC loader tests — skip if local HDF5 not present."""

from pathlib import Path

import pytest

from src.gw_events import GW150914
from src.gwosc_data import load_event_segment, load_hdf5_strain, noise_sigma_premerger

CACHE = Path(__file__).resolve().parent.parent / "data" / "gwosc"
H1 = CACHE / "H-H1_LOSC_4_V2-1126259446-32.hdf5"


@pytest.mark.skipif(not H1.exists(), reason="GW150914 H1 HDF5 not cached")
def test_load_hdf5():
    strain, gps, dur, fs = load_hdf5_strain(H1)
    assert strain.size == 131072
    assert abs(fs - 4096.0) < 1e-6
    assert gps == 1126259446
    assert dur == 32


@pytest.mark.skipif(not H1.exists(), reason="GW150914 H1 HDF5 not cached")
def test_event_segment():
    seg = load_event_segment(GW150914, detector="H1", cache_dir=CACHE)
    assert seg.h.size > 100
    assert seg.t_rel[0] < 0 < seg.t_rel[-1]
    sig = noise_sigma_premerger(seg)
    assert sig > 0
