"""
Whitened multi-detector PE residual + coherent echo network likelihood.

For detectors d ∈ {H1, L1, …} with independent noise after whitening
(σ_d ≈ 1):

    χ²_net = Σ_d || r_d − a0_d RD_d − a_c E_cos_d − a_s E_sin_d ||²

Shared network echo amplitude (a_c, a_s); per-detector leftover ringdown a0_d.
PE subtraction is performed per detector in the whitened domain (lag + A+,Ax).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .amp_structure import AmpStructure
from .coherent_echo import (
    CoherentFitResult,
    coherent_echo_basis,
    fit_linear_combo,
    lee_corrected_threshold,
)
from .echo_ladder import EchoStep, SpacingMode, chi2, fit_amplitude
from .gw_events import PublicGWEvent, get_event
from .gwosc_data import load_event_segment, load_hdf5_strain, download_if_needed
from .invariants import InvariantSet
from .pe_waveform import (
    PEParams,
    generate_imr_polarizations,
    pe_params_for_event,
    place_template_on_grid,
)
from .whiten import (
    PSDEstimate,
    apply_same_whiten,
    estimate_psd_welch,
    whiten_with_norm,
)


@dataclass
class DetectorWhitened:
    """One detector after PSD whitening and PE residual."""

    detector: str
    t_rel: np.ndarray
    strain_raw: np.ndarray
    strain_w: np.ndarray
    residual_w: np.ndarray
    pe_template_w: np.ndarray
    psd: PSDEstimate
    whiten_scale: float
    pe_lag_s: float
    pe_a_plus: float
    pe_a_cross: float
    pe_chi2: float
    pe_snr_proxy: float
    sample_rate: float
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector": self.detector,
            "path": self.path,
            "sample_rate": self.sample_rate,
            "whiten_scale": self.whiten_scale,
            "pe_lag_s": self.pe_lag_s,
            "pe_a_plus": self.pe_a_plus,
            "pe_a_cross": self.pe_a_cross,
            "pe_chi2": self.pe_chi2,
            "pe_snr_proxy": self.pe_snr_proxy,
            "psd": self.psd.to_dict(),
            "n_samples": int(self.t_rel.size),
            "residual_std": float(np.std(self.residual_w)),
        }


@dataclass
class NetworkCoherentResult:
    delay_scale: float
    a0_per_det: dict[str, float]
    a_cos: float
    a_sin: float
    amp: float
    phase: float
    chi2_base: float
    chi2_toe: float
    delta_chi2: float
    mf_snr: float
    steps: list[EchoStep]
    detectors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay_scale": self.delay_scale,
            "a0_per_det": self.a0_per_det,
            "a_cos": self.a_cos,
            "a_sin": self.a_sin,
            "amp": self.amp,
            "phase": self.phase,
            "chi2_base": self.chi2_base,
            "chi2_toe": self.chi2_toe,
            "delta_chi2": self.delta_chi2,
            "mf_snr": self.mf_snr,
            "detectors": self.detectors,
            "steps": [s.to_dict() for s in self.steps],
        }


def load_raw_window(
    event: PublicGWEvent,
    detector: str,
    *,
    cache_dir: Path,
    duration_pre_s: float = 0.25,
    duration_post_s: float = 0.20,
) -> tuple[np.ndarray, np.ndarray, float, Path]:
    """Load unfiltered strain window (t_rel, h, sample_rate, path)."""
    path = download_if_needed(event.name, detector=detector, cache_dir=cache_dir)
    strain, gps_start, _dur, sample_rate = load_hdf5_strain(path)
    t_full = gps_start + np.arange(strain.size) / sample_rate - event.gps
    t0, t1 = -duration_pre_s, duration_post_s
    mask = (t_full >= t0) & (t_full < t1)
    t_rel = t_full[mask]
    h = strain[mask].copy()
    h = h - np.mean(h)
    return t_rel, h, sample_rate, path


def fit_pe_whitened(
    t_rel: np.ndarray,
    strain_w: np.ndarray,
    params: PEParams,
    psd: PSDEstimate,
    whiten_scale: float,
    sample_rate: float,
    *,
    f_low: float,
    f_high: float,
    lag_min: float = -0.05,
    lag_max: float = 0.05,
    fit_t_min: float = -0.15,
    fit_t_max: float = 0.05,
    approximant: str | None = None,
) -> tuple[np.ndarray, float, float, float, float, float, np.ndarray]:
    """Fit PE IMR in whitened domain.

    Returns residual_w, lag, Ap, Ac, chi2, snr, template_w.
    """
    hp, hc, _ = generate_imr_polarizations(
        params, sample_rate=sample_rate, approximant=approximant
    )
    lag_step = 1.0 / sample_rate
    lags = np.arange(lag_min, lag_max + 0.5 * lag_step, lag_step)
    fit_mask = (t_rel >= fit_t_min) & (t_rel <= fit_t_max)
    best = None
    d = strain_w
    # whitened noise ~ unit variance
    sigma = 1.0
    w = 1.0

    # Zero-pad templates to ≥4 s before whitening to reduce FD edge effects
    pad_s = 4.0
    n_pad = int(pad_s * sample_rate)
    n = t_rel.size
    t0 = float(t_rel[0])
    t_pad = t0 - pad_s + np.arange(n + 2 * n_pad) / sample_rate
    center = slice(n_pad, n_pad + n)

    for lag in lags:
        hp_g = place_template_on_grid(hp, t_pad, lag, sample_rate)
        hc_g = place_template_on_grid(hc, t_pad, lag, sample_rate)
        hp_w_full = apply_same_whiten(
            hp_g, sample_rate, psd, whiten_scale, f_low=f_low, f_high=f_high
        )
        hc_w_full = apply_same_whiten(
            hc_g, sample_rate, psd, whiten_scale, f_low=f_low, f_high=f_high
        )
        hp_w = hp_w_full[center]
        hc_w = hc_w_full[center]
        p, c = hp_w[fit_mask], hc_w[fit_mask]
        y = d[fit_mask]
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
        pred = a_p * p + a_c * c
        c2 = float(np.sum((y - pred) ** 2))
        if best is None or c2 < best["chi2"]:
            templ = a_p * hp_w + a_c * hc_w
            best = {
                "lag": float(lag),
                "ap": float(a_p),
                "ac": float(a_c),
                "chi2": c2,
                "template": templ,
            }
    if best is None:
        raise RuntimeError("whitened PE fit failed")
    residual = d - best["template"]
    snr = float(np.sqrt(np.sum(best["template"] ** 2)))
    return (
        residual,
        best["lag"],
        best["ap"],
        best["ac"],
        best["chi2"],
        snr,
        best["template"],
    )


def prepare_detector(
    event: PublicGWEvent,
    detector: str,
    params: PEParams,
    *,
    cache_dir: Path,
    f_low: float = 50.0,
    f_high: float = 300.0,
    duration_pre_s: float = 0.25,
    duration_post_s: float = 0.20,
    psd_pre_end: float = -0.05,
    psd_duration_s: float = 8.0,
    approximant: str | None = None,
) -> DetectorWhitened:
    """Load → PSD from long pre-merger stretch → whiten → PE residual.

    PSD is estimated from up to ``psd_duration_s`` of data ending at
    ``psd_pre_end`` relative to merger (from the full 32 s file), not only
    the short analysis window — much more stable ASD for whitening.
    """
    path = download_if_needed(event.name, detector=detector, cache_dir=cache_dir)
    strain_full, gps_start, _dur, fs = load_hdf5_strain(path)
    t_full = gps_start + np.arange(strain_full.size) / fs - event.gps

    # Long pre-merger for PSD (exclude late pre-merger / signal)
    psd_mask = (t_full >= psd_pre_end - psd_duration_s) & (t_full < psd_pre_end)
    if np.sum(psd_mask) < int(fs):  # fallback: anything before -1 s
        psd_mask = (t_full >= -16.0) & (t_full < -1.0)
    psd_seg = strain_full[psd_mask]
    psd_seg = psd_seg - np.mean(psd_seg)
    psd = estimate_psd_welch(psd_seg, fs)

    # Whiten the full file (high spectral resolution), then cut analysis window
    h_full = strain_full - np.mean(strain_full)
    pre_full = (t_full >= psd_pre_end - psd_duration_s) & (t_full < psd_pre_end)
    h_full_w, scale = whiten_with_norm(
        h_full, fs, psd, f_low=f_low, f_high=f_high, norm_mask=pre_full
    )

    t0, t1 = -duration_pre_s, duration_post_s
    mask = (t_full >= t0) & (t_full < t1)
    t_rel = t_full[mask]
    h = h_full[mask].copy()
    h_w = h_full_w[mask].copy()

    residual, lag, ap, ac, pe_chi2, pe_snr, templ = fit_pe_whitened(
        t_rel,
        h_w,
        params,
        psd,
        scale,
        fs,
        f_low=f_low,
        f_high=f_high,
        approximant=approximant,
    )
    return DetectorWhitened(
        detector=detector,
        t_rel=t_rel,
        strain_raw=h,
        strain_w=h_w,
        residual_w=residual,
        pe_template_w=templ,
        psd=psd,
        whiten_scale=scale,
        pe_lag_s=lag,
        pe_a_plus=ap,
        pe_a_cross=ac,
        pe_chi2=pe_chi2,
        pe_snr_proxy=pe_snr,
        sample_rate=fs,
        path=str(path),
    )


def _align_post_merger(
    dets: list[DetectorWhitened],
) -> tuple[np.ndarray, list[np.ndarray], list[str]]:
    """Restrict to post-merger samples; require identical t grids."""
    t0 = dets[0].t_rel
    post = t0 >= 0.0
    t = t0[post]
    residuals = []
    names = []
    for d in dets:
        if d.t_rel.shape != t0.shape or not np.allclose(d.t_rel, t0):
            # interpolate residual onto common post grid
            r = np.interp(t, d.t_rel, d.residual_w, left=0.0, right=0.0)
        else:
            r = d.residual_w[post]
        residuals.append(r)
        names.append(d.detector)
    return t, residuals, names


def fit_network_coherent(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    amp_structure: AmpStructure = "geometric",
) -> NetworkCoherentResult:
    """Network LS: per-det a0 + shared (a_c, a_s) on whitened residual."""
    inv = inv or InvariantSet()
    t, residuals, names = _align_post_merger(dets)
    n_det = len(dets)

    # Build whitened echo bases per detector
    primaries_w = []
    e_cos_w = []
    e_sin_w = []
    steps_ref: list[EchoStep] = []
    for d in dets:
        primary, e_cos, e_sin, steps = coherent_echo_basis(
            t,
            event,
            inv,
            n_echoes=n_echoes,
            mode=mode,
            amp0=amp0,
            delay_scale=delay_scale,
            amp_structure=amp_structure,
        )
        steps_ref = steps
        # Templates generated on post-merger grid only — whiten via zero-pad to full window
        # Simpler: apply same spectral whitening on post-only by embedding in full t_rel
        p_w = _whiten_on_detector_grid(primary, t, d, f_low=f_low, f_high=f_high)
        c_w = _whiten_on_detector_grid(e_cos, t, d, f_low=f_low, f_high=f_high)
        s_w = _whiten_on_detector_grid(e_sin, t, d, f_low=f_low, f_high=f_high)
        primaries_w.append(p_w)
        e_cos_w.append(c_w)
        e_sin_w.append(s_w)

    # Stack: params = [a0_0, ..., a0_{n-1}, a_c, a_s]
    templates: list[np.ndarray] = []
    # each a0 multiplies primary only on its detector block
    n_post = t.size
    for i in range(n_det):
        block = np.zeros(n_det * n_post)
        block[i * n_post : (i + 1) * n_post] = primaries_w[i]
        templates.append(block)
    # shared a_c, a_s
    block_c = np.concatenate(e_cos_w)
    block_s = np.concatenate(e_sin_w)
    templates.append(block_c)
    templates.append(block_s)
    obs = np.concatenate(residuals)

    # baseline: only a0's
    coeffs_base, pred_base = fit_linear_combo(obs, templates[:n_det], sigma=1.0)
    chi_base = float(np.sum((obs - pred_base) ** 2))

    coeffs, pred_toe = fit_linear_combo(obs, templates, sigma=1.0)
    chi_toe = float(np.sum((obs - pred_toe) ** 2))
    a0s = {names[i]: coeffs[i] for i in range(n_det)}
    a_c, a_s = coeffs[n_det], coeffs[n_det + 1]
    amp = float(math.hypot(a_c, a_s))
    phase = float(math.atan2(a_s, a_c))

    # Network MF SNR for (a_c, a_s) sector only (project out primaries)
    mf = _network_echo_mf_snr(residuals, primaries_w, e_cos_w, e_sin_w)

    return NetworkCoherentResult(
        delay_scale=delay_scale,
        a0_per_det=a0s,
        a_cos=a_c,
        a_sin=a_s,
        amp=amp,
        phase=phase,
        chi2_base=chi_base,
        chi2_toe=chi_toe,
        delta_chi2=chi_base - chi_toe,
        mf_snr=mf,
        steps=steps_ref,
        detectors=names,
    )


def _whiten_on_detector_grid(
    series_post: np.ndarray,
    t_post: np.ndarray,
    det: DetectorWhitened,
    *,
    f_low: float,
    f_high: float,
) -> np.ndarray:
    """Embed post-merger series on full detector t_rel, whiten, extract post."""
    full = np.zeros_like(det.t_rel)
    # map t_post onto det.t_rel
    post = det.t_rel >= 0.0
    if post.sum() == series_post.size and np.allclose(det.t_rel[post], t_post):
        full[post] = series_post
    else:
        full = np.interp(det.t_rel, t_post, series_post, left=0.0, right=0.0)
    w = apply_same_whiten(
        full,
        det.sample_rate,
        det.psd,
        det.whiten_scale,
        f_low=f_low,
        f_high=f_high,
    )
    if post.sum() == series_post.size and np.allclose(det.t_rel[post], t_post):
        return w[post]
    return np.interp(t_post, det.t_rel, w, left=0.0, right=0.0)


def _network_echo_mf_snr(
    residuals: list[np.ndarray],
    primaries: list[np.ndarray],
    e_cos: list[np.ndarray],
    e_sin: list[np.ndarray],
) -> float:
    """2-dof echo SNR after projecting out per-detector primary."""
    # residualize e_cos, e_sin, data against primaries per det then stack
    y_list, c_list, s_list = [], [], []
    for r, p, c, s in zip(residuals, primaries, e_cos, e_sin):
        def proj_out(x, p=p):
            denom = float(np.sum(p * p)) + 1e-60
            a = float(np.sum(x * p)) / denom
            return x - a * p

        y_list.append(proj_out(r))
        c_list.append(proj_out(c))
        s_list.append(proj_out(s))
    y = np.concatenate(y_list)
    c = np.concatenate(c_list)
    s = np.concatenate(s_list)
    g11 = float(np.sum(c * c))
    g22 = float(np.sum(s * s))
    g12 = float(np.sum(c * s))
    b1 = float(np.sum(y * c))
    b2 = float(np.sum(y * s))
    det = g11 * g22 - g12 * g12
    if det <= 1e-60:
        return 0.0
    snr2 = (b1 * b1 * g22 + b2 * b2 * g11 - 2 * b1 * b2 * g12) / det
    return float(math.sqrt(max(snr2, 0.0)))


def _whitened_echo_bases(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    amp_structure: AmpStructure = "geometric",
) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray], list[np.ndarray], list[EchoStep]]:
    """Return t_post, primaries_w, e_cos_w, e_sin_w, steps for network."""
    inv = inv or InvariantSet()
    t, _residuals, _names = _align_post_merger(dets)
    primaries_w, e_cos_w, e_sin_w = [], [], []
    steps_ref: list[EchoStep] = []
    for d in dets:
        primary, e_cos, e_sin, steps = coherent_echo_basis(
            t,
            event,
            inv,
            n_echoes=n_echoes,
            mode=mode,
            amp0=amp0,
            delay_scale=delay_scale,
            amp_structure=amp_structure,
        )
        steps_ref = steps
        primaries_w.append(
            _whiten_on_detector_grid(primary, t, d, f_low=f_low, f_high=f_high)
        )
        e_cos_w.append(
            _whiten_on_detector_grid(e_cos, t, d, f_low=f_low, f_high=f_high)
        )
        e_sin_w.append(
            _whiten_on_detector_grid(e_sin, t, d, f_low=f_low, f_high=f_high)
        )
    return t, primaries_w, e_cos_w, e_sin_w, steps_ref


def network_unit_echo_train(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    phase: float = 0.0,
    amp_structure: AmpStructure = "geometric",
) -> list[np.ndarray]:
    """Per-detector whitened unit echo train with peak network RMS = 1.

    unit_d = (cos φ E_cos_d + sin φ E_sin_d) / rms_network
    so a_inj is in units of whitened residual RMS (network-averaged).
    """
    _t, _p, e_cos_w, e_sin_w, _ = _whitened_echo_bases(
        dets,
        event,
        inv,
        n_echoes=n_echoes,
        mode=mode,
        amp0=amp0,
        delay_scale=delay_scale,
        f_low=f_low,
        f_high=f_high,
        amp_structure=amp_structure,
    )
    c, s = math.cos(phase), math.sin(phase)
    trains = [c * ec + s * es for ec, es in zip(e_cos_w, e_sin_w)]
    # network RMS
    stack = np.concatenate(trains)
    rms = float(np.sqrt(np.mean(stack**2))) + 1e-60
    return [tr / rms for tr in trains]


def fit_network_on_residuals(
    dets: list[DetectorWhitened],
    residuals_post: list[np.ndarray],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    amp_structure: AmpStructure = "geometric",
) -> NetworkCoherentResult:
    """Like fit_network_coherent but with explicit post-merger residual lists."""
    # temporarily swap residual_w on shallow copies
    clones: list[DetectorWhitened] = []
    t0 = dets[0].t_rel
    post = t0 >= 0.0
    for d, r_post in zip(dets, residuals_post):
        r_full = d.residual_w.copy()
        if d.t_rel.shape == t0.shape and np.allclose(d.t_rel, t0):
            r_full[post] = r_post
        else:
            # map r_post onto d.t_rel post samples
            dpost = d.t_rel >= 0.0
            r_full[dpost] = np.interp(d.t_rel[dpost], t0[post], r_post)
        clones.append(
            DetectorWhitened(
                detector=d.detector,
                t_rel=d.t_rel,
                strain_raw=d.strain_raw,
                strain_w=d.strain_w,
                residual_w=r_full,
                pe_template_w=d.pe_template_w,
                psd=d.psd,
                whiten_scale=d.whiten_scale,
                pe_lag_s=d.pe_lag_s,
                pe_a_plus=d.pe_a_plus,
                pe_a_cross=d.pe_a_cross,
                pe_chi2=d.pe_chi2,
                pe_snr_proxy=d.pe_snr_proxy,
                sample_rate=d.sample_rate,
                path=d.path,
            )
        )
    return fit_network_coherent(
        clones,
        event,
        inv,
        n_echoes=n_echoes,
        mode=mode,
        amp0=amp0,
        delay_scale=delay_scale,
        f_low=f_low,
        f_high=f_high,
        amp_structure=amp_structure,
    )


def network_injection_recovery(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    a_injs: list[float] | None = None,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    phase: float = 0.0,
    into: str = "residual",
    seed: int = 42,
    gate_delta_chi2: float = 6.0,
    gate_mf_snr: float = 2.0,
    amp_structure: AmpStructure = "geometric",
) -> dict[str, Any]:
    """Inject coherent train into whitened network residuals; recover Δχ² / SNR.

    a_inj units: network RMS of the unit whitened train (see network_unit_echo_train).
    into='residual' uses PE residuals; into='noise' uses N(0,1) whitened noise.
    """
    inv = inv or InvariantSet()
    t, residuals0, names = _align_post_merger(dets)
    units = network_unit_echo_train(
        dets,
        event,
        inv,
        n_echoes=n_echoes,
        mode=mode,
        amp0=amp0,
        delay_scale=delay_scale,
        f_low=f_low,
        f_high=f_high,
        phase=phase,
        amp_structure=amp_structure,
    )

    if into == "noise":
        rng = np.random.default_rng(seed)
        backgrounds = [rng.standard_normal(t.shape) for _ in dets]
    elif into == "residual":
        backgrounds = [r.copy() for r in residuals0]
    else:
        raise ValueError(into)

    if a_injs is None:
        a_injs = list(np.linspace(0.0, 3.0, 10))

    rows = []
    thr_a = None
    for a in a_injs:
        injected = [b + float(a) * u for b, u in zip(backgrounds, units)]
        fit = fit_network_on_residuals(
            dets,
            injected,
            event,
            inv,
            n_echoes=n_echoes,
            mode=mode,
            amp0=amp0,
            delay_scale=delay_scale,
            f_low=f_low,
            f_high=f_high,
            amp_structure=amp_structure,
        )
        # recovered amplitude in unit-train units: |A| relative to unit
        # fit returns a_c, a_s on un-normalized E_cos/E_sin, not unit train.
        # Report mf_snr and delta_chi2 as primary recovery stats.
        row = {
            "a_inj": float(a),
            "delta_chi2": fit.delta_chi2,
            "mf_snr": fit.mf_snr,
            "amp_raw": fit.amp,
            "a_cos": fit.a_cos,
            "a_sin": fit.a_sin,
            "phase": fit.phase,
            "passes_gate_c_strict": (
                fit.delta_chi2 >= gate_delta_chi2 and fit.mf_snr >= gate_mf_snr
            ),
        }
        rows.append(row)
        if (
            thr_a is None
            and a > 0
            and row["passes_gate_c_strict"]
        ):
            thr_a = float(a)

    bg = rows[0] if rows and abs(rows[0]["a_inj"]) < 1e-15 else None
    return {
        "schema": "invariant_hunt.network_injection.v1",
        "into": into,
        "detectors": names,
        "phase_inj": phase,
        "delay_scale": delay_scale,
        "amp_structure": amp_structure,
        "gate_delta_chi2": gate_delta_chi2,
        "gate_mf_snr": gate_mf_snr,
        "detection_threshold_a_inj": thr_a,
        "background": bg,
        "rows": rows,
        "note": (
            "a_inj multiplies a network-RMS-normalized whitened coherent train. "
            "Gate C strict default: Δχ²≥6 (2-dof), MF SNR≥2."
        ),
    }


def network_delay_scan(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    scan_min: float = 0.80,
    scan_max: float = 1.20,
    n_scales: int = 21,
    gate_a_threshold: float = 4.0,
    f_low: float = 50.0,
    f_high: float = 300.0,
    amp_structure: AmpStructure = "geometric",
) -> dict[str, Any]:
    inv = inv or InvariantSet()
    scales = list(np.linspace(scan_min, scan_max, n_scales))
    if not any(abs(s - 1.0) < 1e-12 for s in scales):
        scales.append(1.0)
        scales = sorted(scales)

    results = []
    for s in scales:
        results.append(
            fit_network_coherent(
                dets,
                event,
                inv,
                n_echoes=n_echoes,
                mode=mode,
                amp0=amp0,
                delay_scale=float(s),
                f_low=f_low,
                f_high=f_high,
                amp_structure=amp_structure,
            )
        )
    best = max(results, key=lambda r: r.delta_chi2)
    nom = next(r for r in results if abs(r.delay_scale - 1.0) < 1e-9)
    n_trials = len(scales)
    thr_lee = lee_corrected_threshold(gate_a_threshold, n_trials)
    return {
        "scales": [float(s) for s in scales],
        "delta_chi2": [r.delta_chi2 for r in results],
        "amps": [r.amp for r in results],
        "mf_snrs": [r.mf_snr for r in results],
        "best": best.to_dict(),
        "nominal": nom.to_dict(),
        "n_trials": n_trials,
        "lee_threshold_raw": gate_a_threshold,
        "lee_threshold_corrected": thr_lee,
        "passes_gate_a_nominal": nom.delta_chi2 >= gate_a_threshold and nom.mf_snr >= 2.0,
        "passes_gate_a_best_raw": best.delta_chi2 >= gate_a_threshold and best.mf_snr >= 2.0,
        "passes_gate_a_best_lee": best.delta_chi2 >= thr_lee and best.mf_snr >= 2.0,
    }


def prepare_network(
    event_name: str,
    detectors: list[str],
    *,
    project_root: Path,
    f_low: float | None = None,
    f_high: float | None = None,
) -> tuple[PublicGWEvent, PEParams, list[DetectorWhitened]]:
    event = get_event(event_name)
    # Event-dependent analysis band (lighter BBHs need higher f_high)
    f_lo = float(f_low if f_low is not None else event.f_low_hz)
    f_hi = float(f_high if f_high is not None else event.f_high_hz)
    pe_dir = project_root / "data" / "pe"
    cache = project_root / "data" / "gwosc"
    params = pe_params_for_event(event.name, pe_dir=pe_dir)
    dets = [
        prepare_detector(
            event,
            det,
            params,
            cache_dir=cache,
            f_low=f_lo,
            f_high=f_hi,
        )
        for det in detectors
    ]
    return event, params, dets
