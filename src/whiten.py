"""
PSD estimation and frequency-domain whitening for public GW strain.

Whitened series are scaled so that pre-merger (or reference) samples have
empirical variance ≈ 1, making χ² ≈ Σ r_w² under the white-noise model
after band-limiting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import signal


@dataclass
class PSDEstimate:
    freqs: np.ndarray
    psd: np.ndarray
    sample_rate: float
    nperseg: int
    method: str = "welch"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "nperseg": self.nperseg,
            "method": self.method,
            "f_min": float(self.freqs[0]),
            "f_max": float(self.freqs[-1]),
            "n_bins": int(self.freqs.size),
            "median_psd": float(np.median(self.psd[self.psd > 0])) if np.any(self.psd > 0) else None,
        }


def estimate_psd_welch(
    strain: np.ndarray,
    sample_rate: float,
    *,
    nperseg: int | None = None,
    noverlap: int | None = None,
) -> PSDEstimate:
    """One-sided PSD via Welch on a stretch of data (use pre-merger)."""
    n = int(strain.size)
    if nperseg is None:
        # ~1 s segments at 4096 Hz, or 1/8 of series
        nperseg = int(min(sample_rate, max(256, n // 8)))
        # power of two-ish
        nperseg = int(2 ** int(np.floor(np.log2(nperseg))))
    nperseg = min(nperseg, n)
    if noverlap is None:
        noverlap = nperseg // 2
    freqs, psd = signal.welch(
        strain,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=noverlap,
        window="hann",
        detrend="constant",
        scaling="density",
        average="median",
    )
    return PSDEstimate(
        freqs=np.asarray(freqs, dtype=np.float64),
        psd=np.asarray(psd, dtype=np.float64),
        sample_rate=float(sample_rate),
        nperseg=int(nperseg),
    )


def interpolate_psd(
    freqs_target: np.ndarray,
    psd_est: PSDEstimate,
    *,
    f_low: float,
    f_high: float,
    floor_frac: float = 1e-6,
) -> np.ndarray:
    """Interpolate PSD onto rfft frequency grid; large outside band."""
    psd = np.interp(
        freqs_target,
        psd_est.freqs,
        psd_est.psd,
        left=np.inf,
        right=np.inf,
    )
    # floor inside band to avoid divide-by-zero on notches
    band = (freqs_target >= f_low) & (freqs_target <= f_high) & np.isfinite(psd)
    if np.any(band):
        med = float(np.median(psd[band]))
        floor = max(med * floor_frac, 1e-100)
        psd = np.where(band, np.maximum(psd, floor), psd)
    # outside analysis band → infinite noise (kill)
    outside = (freqs_target < f_low) | (freqs_target > f_high)
    psd = np.where(outside, np.inf, psd)
    psd = np.where(np.isfinite(psd) & (psd > 0), psd, np.inf)
    return psd


def whiten_series(
    strain: np.ndarray,
    sample_rate: float,
    psd_est: PSDEstimate,
    *,
    f_low: float = 50.0,
    f_high: float = 300.0,
    norm_segment: np.ndarray | None = None,
) -> np.ndarray:
    """Frequency-domain whiten: h_w = IFFT( FFT(h) / sqrt(S(f)) ).

    If norm_segment indices or boolean mask provided via a parallel array
    equal length as strain used only for scaling: pass the whitened values
    on that segment separately — see whiten_with_norm.
    """
    n = int(strain.size)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    S = interpolate_psd(freqs, psd_est, f_low=f_low, f_high=f_high)
    inv_sqrt = np.zeros_like(S)
    ok = np.isfinite(S) & (S > 0) & (S < np.inf)
    inv_sqrt[ok] = 1.0 / np.sqrt(S[ok])
    Hw = np.fft.rfft(strain.astype(np.float64)) * inv_sqrt
    return np.fft.irfft(Hw, n=n).real


def whiten_with_norm(
    strain: np.ndarray,
    sample_rate: float,
    psd_est: PSDEstimate,
    *,
    f_low: float = 50.0,
    f_high: float = 300.0,
    norm_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, float]:
    """Whiten and scale so whitened samples on norm_mask have std ≈ 1.

    Returns (h_whitened_unit, scale_applied) where scale multiplies raw whitened.
    """
    hw = whiten_series(
        strain, sample_rate, psd_est, f_low=f_low, f_high=f_high
    )
    if norm_mask is None:
        # use first 25% as proxy for "quiet"
        n = hw.size
        norm_mask = np.zeros(n, dtype=bool)
        norm_mask[: max(n // 4, 1)] = True
    ref = hw[norm_mask]
    std = float(np.std(ref))
    if std < 1e-30:
        scale = 1.0
    else:
        scale = 1.0 / std
    return hw * scale, scale


def apply_same_whiten(
    template: np.ndarray,
    sample_rate: float,
    psd_est: PSDEstimate,
    scale: float,
    *,
    f_low: float = 50.0,
    f_high: float = 300.0,
) -> np.ndarray:
    """Whiten a template with the same PSD and amplitude scale as the data."""
    tw = whiten_series(
        template, sample_rate, psd_est, f_low=f_low, f_high=f_high
    )
    return tw * scale
