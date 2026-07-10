"""
Published PE / phenomenological IMR waveforms for residual analysis.

Uses GWTC-1 public posterior samples (P1800370) and PyCBC IMRPhenomD
to build a detector-frame template, then fits amplitude, phase (plus/cross
linear combo), and a discrete time lag to public GWOSC strain.

Residual:  r(t) = d(t) − ĥ_PE(t)
Echo tests run on post-merger residual vs residual + positional ladder.
"""

from __future__ import annotations

import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .gw_events import PublicGWEvent, get_event

# GWTC-1 public PE samples (LIGO-P1800370)
PE_URLS: dict[str, str] = {
    "GW150914": "https://dcc.ligo.org/public/0157/P1800370/005/GW150914_GWTC-1.hdf5",
}

PE_DATASET_PREFERRED = "Overall_posterior"


@dataclass
class PEParams:
    """Detector-frame median PE parameters for waveform generation."""

    event: str
    mass1: float
    mass2: float
    distance_mpc: float
    spin1z: float
    spin2z: float
    ra: float
    dec: float
    costheta_jn: float
    approximant: str = "IMRPhenomD"
    posterior_dataset: str = PE_DATASET_PREFERRED
    n_samples: int = 0
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PEFitResult:
    """Best-fit PE template against a strain segment."""

    params: PEParams
    lag_s: float
    """Template peak time relative to event GPS (data time axis)."""
    a_plus: float
    a_cross: float
    chi2: float
    residual: np.ndarray
    template: np.ndarray
    t_rel: np.ndarray
    snr_proxy: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "params": self.params.to_dict(),
            "lag_s": self.lag_s,
            "a_plus": self.a_plus,
            "a_cross": self.a_cross,
            "chi2": self.chi2,
            "snr_proxy": self.snr_proxy,
            "n_samples": int(self.residual.size),
        }


def default_pe_dir(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    return project_root / "data" / "pe"


def download_pe_samples(event: str, pe_dir: Path | None = None) -> Path:
    pe_dir = pe_dir or default_pe_dir()
    pe_dir.mkdir(parents=True, exist_ok=True)
    if event not in PE_URLS:
        raise KeyError(f"No PE URL registered for {event}")
    path = pe_dir / f"{event}_GWTC-1.hdf5"
    if path.exists() and path.stat().st_size > 1000:
        return path
    url = PE_URLS[event]
    print(f"Downloading PE samples {url} → {path}")
    urllib.request.urlretrieve(url, path)  # noqa: S310 — public LIGO DCC
    return path


def load_pe_medians(
    event: str,
    *,
    pe_dir: Path | None = None,
    dataset: str = PE_DATASET_PREFERRED,
) -> PEParams:
    """Median PE parameters from public GWTC-1 HDF5."""
    import h5py

    path = download_pe_samples(event, pe_dir=pe_dir)
    with h5py.File(path, "r") as f:
        if dataset not in f:
            # fall back to first posterior-like group
            keys = [k for k in f.keys() if "posterior" in k.lower()]
            if not keys:
                raise KeyError(f"No posterior dataset in {path}")
            dataset = keys[0]
        post = f[dataset][:]

    m1 = float(np.median(post["m1_detector_frame_Msun"]))
    m2 = float(np.median(post["m2_detector_frame_Msun"]))
    # ensure m1 >= m2
    if m2 > m1:
        m1, m2 = m2, m1
    d_l = float(np.median(post["luminosity_distance_Mpc"]))
    s1 = post["spin1"] * post["costilt1"]
    s2 = post["spin2"] * post["costilt2"]
    return PEParams(
        event=event,
        mass1=m1,
        mass2=m2,
        distance_mpc=d_l,
        spin1z=float(np.median(s1)),
        spin2z=float(np.median(s2)),
        ra=float(np.median(post["right_ascension"])),
        dec=float(np.median(post["declination"])),
        costheta_jn=float(np.median(post["costheta_jn"])),
        posterior_dataset=dataset,
        n_samples=int(post.shape[0]),
        source=str(path),
    )


def generate_imr_polarizations(
    params: PEParams,
    *,
    sample_rate: float = 4096.0,
    f_lower: float = 20.0,
    approximant: str | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Generate plus/cross polarizations; return (hp, hc, delta_t).

    Waveform is truncated/padded so peak amplitude is at a known index;
    callers use lag search for absolute alignment.
    """
    try:
        from pycbc.waveform import get_td_waveform
    except ImportError as e:
        raise ImportError(
            "pycbc is required for PE waveforms: pip install pycbc"
        ) from e

    approx = approximant or params.approximant
    hp, hc = get_td_waveform(
        approximant=approx,
        mass1=params.mass1,
        mass2=params.mass2,
        spin1z=params.spin1z,
        spin2z=params.spin2z,
        distance=params.distance_mpc,
        delta_t=1.0 / sample_rate,
        f_lower=f_lower,
    )
    hp_np = np.asarray(hp.numpy(), dtype=np.float64)
    hc_np = np.asarray(hc.numpy(), dtype=np.float64)
    return hp_np, hc_np, float(hp.delta_t)


def _bandpass_fft(
    h: np.ndarray, sample_rate: float, f_low: float, f_high: float
) -> np.ndarray:
    n = h.size
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    H = np.fft.rfft(h)
    H[(freqs < f_low) | (freqs > f_high)] = 0.0
    return np.fft.irfft(H, n=n).real


def place_template_on_grid(
    pol: np.ndarray,
    t_data: np.ndarray,
    peak_time_rel: float,
    sample_rate: float,
) -> np.ndarray:
    """Interpolate polarization onto data times with peak at peak_time_rel.

    pol is assumed to have its amplitude peak at argmax(|pol|).
    """
    i_peak = int(np.argmax(np.abs(pol)))
    t_pol = (np.arange(pol.size) - i_peak) / sample_rate + peak_time_rel
    # zero outside support
    out = np.interp(t_data, t_pol, pol, left=0.0, right=0.0)
    return out


def fit_pe_to_strain(
    t_rel: np.ndarray,
    strain: np.ndarray,
    params: PEParams,
    *,
    sample_rate: float,
    sigma: float,
    f_low: float = 50.0,
    f_high: float = 300.0,
    lag_min: float = -0.05,
    lag_max: float = 0.05,
    lag_step: float | None = None,
    fit_t_min: float = -0.15,
    fit_t_max: float = 0.05,
) -> PEFitResult:
    """Grid-search lag; LS fit a_plus, a_cross of bandpassed IMR to strain.

    Parameters
    ----------
    t_rel, strain :
        Analysis window relative to merger GPS (same convention as gwosc_data).
    lag :
        Template peak time relative to merger GPS.
    fit_t_min/max :
        Interval used for χ² / LS (inspiral+merger); residual returned on full window.
    """
    if lag_step is None:
        lag_step = 1.0 / sample_rate

    hp, hc, _dt = generate_imr_polarizations(params, sample_rate=sample_rate)
    # bandpass on long arrays then place
    # work in data domain: for each lag, place raw pol then bandpass with data filter
    # more consistent: bandpass data already; bandpass placed template on same grid

    fit_mask = (t_rel >= fit_t_min) & (t_rel <= fit_t_max)
    if not np.any(fit_mask):
        raise ValueError("Empty fit window")

    lags = np.arange(lag_min, lag_max + 0.5 * lag_step, lag_step)
    best: dict[str, Any] | None = None

    w = 1.0 / (sigma**2 + 1e-60)
    d = strain

    for lag in lags:
        hp_g = place_template_on_grid(hp, t_rel, lag, sample_rate)
        hc_g = place_template_on_grid(hc, t_rel, lag, sample_rate)
        hp_g = _bandpass_fft(hp_g, sample_rate, f_low, f_high)
        hc_g = _bandpass_fft(hc_g, sample_rate, f_low, f_high)

        p = hp_g[fit_mask]
        c = hc_g[fit_mask]
        y = d[fit_mask]
        # 2-param LS
        app = float(np.sum(p * p * w))
        acc = float(np.sum(c * c * w))
        apc = float(np.sum(p * c * w))
        bp = float(np.sum(y * p * w))
        bc = float(np.sum(y * c * w))
        det = app * acc - apc * apc
        if abs(det) < 1e-60:
            continue
        a_p = (bp * acc - bc * apc) / det
        a_c = (bc * app - bp * apc) / det
        pred_fit = a_p * p + a_c * c
        chi2 = float(np.sum(((y - pred_fit) ** 2) * w))
        if best is None or chi2 < best["chi2"]:
            template_full = a_p * hp_g + a_c * hc_g
            best = {
                "lag_s": float(lag),
                "a_plus": float(a_p),
                "a_cross": float(a_c),
                "chi2": chi2,
                "template": template_full,
            }

    if best is None:
        raise RuntimeError("PE fit failed for all lags")

    residual = d - best["template"]
    # matched-filter SNR proxy: ||template|| / sigma
    snr = float(np.sqrt(np.sum(best["template"] ** 2)) / (sigma + 1e-60))

    return PEFitResult(
        params=params,
        lag_s=best["lag_s"],
        a_plus=best["a_plus"],
        a_cross=best["a_cross"],
        chi2=best["chi2"],
        residual=residual,
        template=best["template"],
        t_rel=t_rel,
        snr_proxy=snr,
    )


def pe_params_for_event(
    event: str | PublicGWEvent,
    *,
    pe_dir: Path | None = None,
) -> PEParams:
    name = event if isinstance(event, str) else event.name
    if name in PE_URLS:
        return load_pe_medians(name, pe_dir=pe_dir)
    # fallback: use catalog component masses as detector-frame approx
    ev = get_event(name)
    return PEParams(
        event=ev.name,
        mass1=ev.mass1_solar,
        mass2=ev.mass2_solar,
        distance_mpc=400.0,
        spin1z=0.0,
        spin2z=0.0,
        ra=0.0,
        dec=0.0,
        costheta_jn=0.0,
        source="catalog_fallback",
    )
