"""
Load public LIGO strain from GWOSC HDF5 (local cache or download).

Avoids a hard dependency on GWpy; uses h5py + urllib.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .gw_events import GWOSC_32S, PublicGWEvent, get_event


@dataclass
class StrainSegment:
    """Calibrated strain segment relative to merger GPS."""

    event: str
    detector: str
    gps_start: float
    sample_rate: float
    strain: np.ndarray
    """Full file strain array."""
    t_rel: np.ndarray
    """Time relative to merger [s] for the analysis window."""
    h: np.ndarray
    """Strain in the analysis window (same length as t_rel)."""
    path: Path

    @property
    def n(self) -> int:
        return int(self.h.size)


def default_cache_dir(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    return project_root / "data" / "gwosc"


def download_if_needed(
    event: str,
    detector: str = "H1",
    cache_dir: Path | None = None,
) -> Path:
    """Ensure the 32 s GWOSC HDF5 is present; download if missing."""
    cache_dir = cache_dir or default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    meta = GWOSC_32S.get(event)
    if meta is None:
        raise FileNotFoundError(
            f"No bundled GWOSC URL for {event}. Place an HDF5 under {cache_dir}."
        )
    if detector not in meta:
        raise KeyError(f"Detector {detector} not in release table for {event}")

    fname = meta[detector]
    path = cache_dir / fname
    if path.exists() and path.stat().st_size > 1000:
        return path

    url = meta["base_url"] + fname
    print(f"Downloading {url} → {path}")
    urllib.request.urlretrieve(url, path)  # noqa: S310 — public GWOSC URL
    return path


def load_hdf5_strain(path: Path) -> tuple[np.ndarray, float, float, float]:
    """Return (strain, gps_start, duration, sample_rate)."""
    import h5py

    with h5py.File(path, "r") as f:
        strain = np.asarray(f["strain"]["Strain"][()], dtype=np.float64)
        gps_start = float(f["meta"]["GPSstart"][()])
        duration = float(f["meta"]["Duration"][()])
    sample_rate = strain.size / duration
    return strain, gps_start, duration, sample_rate


def bandpass(
    h: np.ndarray,
    sample_rate: float,
    f_low: float = 50.0,
    f_high: float = 300.0,
) -> np.ndarray:
    """Zero-phase FFT bandpass (simple, no SciPy filter design required)."""
    n = h.size
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    H = np.fft.rfft(h)
    mask = (freqs >= f_low) & (freqs <= f_high)
    H[~mask] = 0.0
    # soft edges
    for edge, width in ((f_low, 5.0), (f_high, 10.0)):
        band = (freqs > edge - width) & (freqs < edge + width)
        # raised-cosine halfway
        pass
    out = np.fft.irfft(H, n=n).real
    return out


def highpass(h: np.ndarray, sample_rate: float, f_low: float = 20.0) -> np.ndarray:
    n = h.size
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    H = np.fft.rfft(h)
    H[freqs < f_low] = 0.0
    return np.fft.irfft(H, n=n).real


def load_event_segment(
    event: str | PublicGWEvent,
    detector: str = "H1",
    *,
    cache_dir: Path | None = None,
    f_low: float = 50.0,
    f_high: float = 300.0,
    apply_bandpass: bool = True,
) -> StrainSegment:
    """Load public strain and cut a window around merger."""
    if isinstance(event, str):
        ev = get_event(event)
    else:
        ev = event

    path = download_if_needed(ev.name, detector=detector, cache_dir=cache_dir)
    strain, gps_start, _duration, sample_rate = load_hdf5_strain(path)

    # time of each sample relative to merger
    t_full = gps_start + np.arange(strain.size) / sample_rate - ev.gps
    t0 = -ev.duration_pre_s
    t1 = ev.duration_post_s
    mask = (t_full >= t0) & (t_full < t1)
    t_rel = t_full[mask]
    h = strain[mask].copy()

    # remove mean; optional bandpass on the short window
    h = h - np.mean(h)
    if apply_bandpass:
        # pad to reduce edge ringing
        pad = int(0.05 * sample_rate)
        hp = np.pad(h, pad, mode="reflect")
        hp = bandpass(hp, sample_rate, f_low=f_low, f_high=f_high)
        h = hp[pad : pad + h.size]

    return StrainSegment(
        event=ev.name,
        detector=detector,
        gps_start=gps_start,
        sample_rate=sample_rate,
        strain=strain,
        t_rel=t_rel,
        h=h,
        path=path,
    )


def noise_sigma_premerger(seg: StrainSegment, pre_end: float = -0.01) -> float:
    """RMS of band-limited strain before merger (for χ² weighting)."""
    m = seg.t_rel < pre_end
    if not np.any(m):
        return float(np.std(seg.h) + 1e-30)
    return float(np.std(seg.h[m]) + 1e-30)
