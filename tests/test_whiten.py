"""Whitening unit tests."""

import numpy as np

from src.whiten import estimate_psd_welch, whiten_with_norm, apply_same_whiten


def test_whiten_unit_variance_on_noise():
    rng = np.random.default_rng(0)
    fs = 4096.0
    n = 8192
    # colored noise: filter white
    w = rng.standard_normal(n)
    # simple AR coloring
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.9 * x[i - 1] + w[i]
    psd = estimate_psd_welch(x[: n // 2], fs, nperseg=512)
    mask = np.zeros(n, dtype=bool)
    mask[: n // 2] = True
    xw, scale = whiten_with_norm(
        x, fs, psd, f_low=20.0, f_high=500.0, norm_mask=mask
    )
    assert abs(np.std(xw[mask]) - 1.0) < 0.15
    # template whitening same scale
    tw = apply_same_whiten(x, fs, psd, scale, f_low=20.0, f_high=500.0)
    assert tw.shape == x.shape


def test_psd_positive():
    rng = np.random.default_rng(1)
    fs = 4096.0
    x = rng.standard_normal(4096)
    psd = estimate_psd_welch(x, fs, nperseg=256)
    assert np.all(psd.psd >= 0)
    assert psd.freqs[0] == 0.0
