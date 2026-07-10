"""Network whitened likelihood smoke tests (needs H1+L1 cache + pycbc)."""

from pathlib import Path

import numpy as np
import pytest

CACHE = Path(__file__).resolve().parent.parent / "data" / "gwosc"
H1 = CACHE / "H-H1_LOSC_4_V2-1126259446-32.hdf5"
L1 = CACHE / "L-L1_LOSC_4_V2-1126259446-32.hdf5"

pytest.importorskip("pycbc")


@pytest.mark.skipif(not (H1.exists() and L1.exists()), reason="H1/L1 HDF5 missing")
def test_prepare_network_and_fit():
    from pathlib import Path

    from src.network_likelihood import fit_network_coherent, prepare_network

    root = Path(__file__).resolve().parent.parent
    event, params, dets = prepare_network(
        "GW150914", ["H1", "L1"], project_root=root, f_low=50.0, f_high=300.0
    )
    assert len(dets) == 2
    assert params.mass1 > 0
    for d in dets:
        assert d.residual_w.size == d.t_rel.size
        assert np.std(d.strain_w[d.t_rel < -0.05]) < 2.5  # ~unit after norm

    res = fit_network_coherent(dets, event, delay_scale=1.0, n_echoes=3)
    assert res.delta_chi2 == res.delta_chi2  # finite
    assert res.mf_snr >= 0
    assert set(res.detectors) == {"H1", "L1"}
