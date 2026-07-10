"""Network injection recovery smoke test."""

from pathlib import Path

import pytest

CACHE = Path(__file__).resolve().parent.parent / "data" / "gwosc"
H1 = CACHE / "H-H1_LOSC_4_V2-1126259446-32.hdf5"
L1 = CACHE / "L-L1_LOSC_4_V2-1126259446-32.hdf5"

pytest.importorskip("pycbc")


@pytest.mark.skipif(not (H1.exists() and L1.exists()), reason="H1/L1 missing")
def test_network_injection_monotonic():
    from pathlib import Path

    from src.network_likelihood import network_injection_recovery, prepare_network

    root = Path(__file__).resolve().parent.parent
    event, _, dets = prepare_network(
        "GW150914", ["H1", "L1"], project_root=root
    )
    out = network_injection_recovery(
        dets,
        event,
        a_injs=[0.0, 1.0, 2.0],
        into="noise",
        n_echoes=3,
        gate_delta_chi2=6.0,
    )
    rows = out["rows"]
    assert rows[0]["a_inj"] == 0.0
    assert rows[-1]["delta_chi2"] > rows[0]["delta_chi2"]
    assert rows[-1]["mf_snr"] > rows[0]["mf_snr"]
