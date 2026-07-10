"""
Coherent complex-amplitude echo train + controlled delay-scale scan.

Mapping refinements that keep core locks fixed (W_g, κ, braiding attractor):

1. **Coherent train** — relative step weights amp0^n and relative braiding
   phases stay fixed; one complex amplitude (A cos φ, A sin φ) multiplies
   the whole train. Equivalent basis:
       residual ≈ a0 · RD + a_c · E_cos + a_s · E_sin
   with E_cos, E_sin built from cos/sin carrier at each ladder step.

2. **Delay scale** s — δt_n(s) = s · δt_n(geometric). Scan s ∈ [1−ε, 1+ε]
   with documented trial count for look-elsewhere (LEE) correction on Gate A.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np

from .echo_ladder import (
    EchoStep,
    SpacingMode,
    baseline_ringdown,
    build_ladder,
    chi2,
    echo_delay_seconds,
    fit_amplitude,
    ringdown_template,
)
from .gw_events import PublicGWEvent
from .invariants import InvariantSet
from .positional import PositionalPhase

EchoModel = Literal["independent", "coherent"]


@dataclass
class CoherentFitResult:
    """Fit of leftover ringdown + coherent echo train at fixed delay scale."""

    delay_scale: float
    a0: float
    a_cos: float
    a_sin: float
    amp: float
    """Overall |A| = hypot(a_cos, a_sin)."""
    phase: float
    """atan2(a_sin, a_cos)."""
    chi2_base: float
    chi2_toe: float
    delta_chi2: float
    steps: list[EchoStep]
    pred_base: np.ndarray
    pred_toe: np.ndarray
    e_cos: np.ndarray
    e_sin: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay_scale": self.delay_scale,
            "a0": self.a0,
            "a_cos": self.a_cos,
            "a_sin": self.a_sin,
            "amp": self.amp,
            "phase": self.phase,
            "chi2_base": self.chi2_base,
            "chi2_toe": self.chi2_toe,
            "delta_chi2": self.delta_chi2,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class DelayScanResult:
    """Scan over delay_scale with look-elsewhere bookkeeping."""

    scales: list[float]
    delta_chi2: list[float]
    amps: list[float]
    best: CoherentFitResult
    n_trials: int
    scan_min: float
    scan_max: float
    nominal_delta_chi2: float
    """Δχ² at s=1 (geometric, no scan freedom)."""
    lee_threshold_raw: float
    """Gate A raw threshold (e.g. 4)."""
    lee_threshold_corrected: float
    """Bonferroni-style: thr + 2 ln(n_trials) for approx χ²_1 max (rough)."""
    passes_gate_a_nominal: bool
    passes_gate_a_best_raw: bool
    passes_gate_a_best_lee: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "scales": self.scales,
            "delta_chi2": self.delta_chi2,
            "amps": self.amps,
            "best": self.best.to_dict(),
            "n_trials": self.n_trials,
            "scan_min": self.scan_min,
            "scan_max": self.scan_max,
            "nominal_delta_chi2": self.nominal_delta_chi2,
            "lee_threshold_raw": self.lee_threshold_raw,
            "lee_threshold_corrected": self.lee_threshold_corrected,
            "passes_gate_a_nominal": self.passes_gate_a_nominal,
            "passes_gate_a_best_raw": self.passes_gate_a_best_raw,
            "passes_gate_a_best_lee": self.passes_gate_a_best_lee,
            "lee_method": "bonferroni_chi2_approx: thr_corr = thr + 2*ln(n_trials)",
        }


def scaled_ladder(
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
) -> list[EchoStep]:
    """Ladder with δt_n → delay_scale · δt_n; braiding from site index unchanged."""
    inv = inv or InvariantSet()
    base = build_ladder(event, inv, n_echoes=n_echoes, mode=mode, amp0=amp0)
    out: list[EchoStep] = []
    for step in base:
        out.append(
            EchoStep(
                n=step.n,
                delay_s=step.delay_s * delay_scale,
                uncertainty_s=step.uncertainty_s * delay_scale,
                amp_prior=step.amp_prior,
                fiber_angle=step.fiber_angle,
                phase_unit=step.phase_unit,
                braiding_angle=step.braiding_angle,
            )
        )
    return out


def coherent_echo_basis(
    t: np.ndarray,
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    tau_scale: float = 0.015,
    amp0: float = 0.35,
    delay_scale: float = 1.0,
    use_braiding_offset: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[EchoStep]]:
    """Build (primary, E_cos, E_sin, steps) for coherent complex fit.

    Each step n contributes:
      amp0^n · exp(−(t−t_n)/τ) · sin(2π f t + ψ_n + φ)
    with shared φ. Expand:
      sin(ωt + ψ_n + φ) = cos φ · sin(ωt+ψ_n) + sin φ · cos(ωt+ψ_n)
    so E_cos uses sin(·+ψ_n), E_sin uses cos(·+ψ_n).
    """
    inv = inv or InvariantSet()
    tau = tau_scale * (event.mass_final_solar / 30.0)
    primary = baseline_ringdown(t, event, tau_scale=tau_scale)
    steps = scaled_ladder(
        event, inv, n_echoes=n_echoes, mode=mode, amp0=amp0, delay_scale=delay_scale
    )
    e_cos = np.zeros_like(t, dtype=np.float64)
    e_sin = np.zeros_like(t, dtype=np.float64)
    f0 = event.f_ring_hz
    for step in steps:
        psi = step.braiding_angle if use_braiding_offset else 0.0
        e_cos = e_cos + step.amp_prior * ringdown_template(
            t, f0=f0, tau=tau * 1.2, t0=step.delay_s, phase0=psi
        )
        # cos carrier = sin(· + π/2)
        e_sin = e_sin + step.amp_prior * ringdown_template(
            t, f0=f0, tau=tau * 1.2, t0=step.delay_s, phase0=psi + 0.5 * math.pi
        )
    return primary, e_cos, e_sin, steps


def fit_linear_combo(
    obs: np.ndarray,
    templates: list[np.ndarray],
    sigma: float,
) -> tuple[list[float], np.ndarray]:
    """Weighted least squares: obs ≈ Σ a_i templates[i]."""
    w = 1.0 / (sigma**2 + 1e-60)
    k = len(templates)
    g = np.zeros((k, k), dtype=np.float64)
    b = np.zeros(k, dtype=np.float64)
    for i in range(k):
        ti = templates[i]
        b[i] = float(np.sum(obs * ti * w))
        for j in range(i, k):
            g[i, j] = float(np.sum(ti * templates[j] * w))
            g[j, i] = g[i, j]
    try:
        coeffs = np.linalg.solve(g, b)
    except np.linalg.LinAlgError:
        coeffs = np.linalg.lstsq(g, b, rcond=None)[0]
    pred = np.zeros_like(obs, dtype=np.float64)
    for a, templ in zip(coeffs, templates):
        pred = pred + float(a) * templ
    return [float(c) for c in coeffs], pred


def fit_coherent_echoes(
    residual: np.ndarray,
    t: np.ndarray,
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    sigma: float,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    delay_scale: float = 1.0,
) -> CoherentFitResult:
    """3-param fit: a0·RD + a_c·E_cos + a_s·E_sin at fixed delay_scale."""
    inv = inv or InvariantSet()
    primary, e_cos, e_sin, steps = coherent_echo_basis(
        t,
        event,
        inv,
        n_echoes=n_echoes,
        mode=mode,
        amp0=amp0,
        delay_scale=delay_scale,
    )
    a0_only = fit_amplitude(residual, primary, sigma)
    pred_base = a0_only * primary
    chi_base = chi2(residual, pred_base, sigma)

    coeffs, pred_toe = fit_linear_combo(residual, [primary, e_cos, e_sin], sigma)
    a0, a_c, a_s = coeffs
    chi_toe = chi2(residual, pred_toe, sigma)
    amp = float(math.hypot(a_c, a_s))
    phase = float(math.atan2(a_s, a_c))

    return CoherentFitResult(
        delay_scale=delay_scale,
        a0=a0,
        a_cos=a_c,
        a_sin=a_s,
        amp=amp,
        phase=phase,
        chi2_base=chi_base,
        chi2_toe=chi_toe,
        delta_chi2=chi_base - chi_toe,
        steps=steps,
        pred_base=pred_base,
        pred_toe=pred_toe,
        e_cos=e_cos,
        e_sin=e_sin,
    )


def lee_corrected_threshold(raw_thr: float, n_trials: int) -> float:
    """Rough Bonferroni correction for max of n independent χ²_1-like stats.

    For Gaussian trials, max SNR² threshold scales as thr + 2 ln N.
    Documented as approximate — not a full continuous-scan asymptotic.
    """
    n = max(int(n_trials), 1)
    return float(raw_thr + 2.0 * math.log(n))


def delay_scale_scan(
    residual: np.ndarray,
    t: np.ndarray,
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    sigma: float,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    scan_min: float = 0.80,
    scan_max: float = 1.20,
    n_scales: int = 21,
    gate_a_threshold: float = 4.0,
) -> DelayScanResult:
    """Grid scan delay_scale; report best Δχ² with LEE-corrected threshold."""
    inv = inv or InvariantSet()
    scales = list(np.linspace(scan_min, scan_max, n_scales))
    # ensure s=1 is included
    if not any(abs(s - 1.0) < 1e-12 for s in scales):
        scales.append(1.0)
        scales = sorted(scales)

    results: list[CoherentFitResult] = []
    for s in scales:
        results.append(
            fit_coherent_echoes(
                residual,
                t,
                event,
                inv,
                sigma=sigma,
                n_echoes=n_echoes,
                mode=mode,
                amp0=amp0,
                delay_scale=float(s),
            )
        )

    dchis = [r.delta_chi2 for r in results]
    amps = [r.amp for r in results]
    best = max(results, key=lambda r: r.delta_chi2)
    nom = next(r for r in results if abs(r.delay_scale - 1.0) < 1e-9)
    n_trials = len(scales)
    thr_lee = lee_corrected_threshold(gate_a_threshold, n_trials)

    return DelayScanResult(
        scales=[float(s) for s in scales],
        delta_chi2=dchis,
        amps=amps,
        best=best,
        n_trials=n_trials,
        scan_min=scan_min,
        scan_max=scan_max,
        nominal_delta_chi2=nom.delta_chi2,
        lee_threshold_raw=gate_a_threshold,
        lee_threshold_corrected=thr_lee,
        passes_gate_a_nominal=(
            nom.delta_chi2 >= gate_a_threshold and nom.amp > 0
        ),
        passes_gate_a_best_raw=(
            best.delta_chi2 >= gate_a_threshold and best.amp > 0
        ),
        passes_gate_a_best_lee=(
            best.delta_chi2 >= thr_lee and best.amp > 0
        ),
    )


def coherent_matched_filter_snr(
    residual: np.ndarray,
    e_cos: np.ndarray,
    e_sin: np.ndarray,
    sigma: float,
) -> float:
    """Network SNR of coherent (2-dof) echo template vs residual."""
    # SNR² = b^T G^{-1} b for the two echo components (ignore primary)
    w = 1.0 / (sigma**2 + 1e-60)
    g11 = float(np.sum(e_cos * e_cos * w))
    g22 = float(np.sum(e_sin * e_sin * w))
    g12 = float(np.sum(e_cos * e_sin * w))
    b1 = float(np.sum(residual * e_cos * w))
    b2 = float(np.sum(residual * e_sin * w))
    det = g11 * g22 - g12 * g12
    if det <= 1e-60:
        return 0.0
    # quadratic form
    snr2 = (b1 * b1 * g22 + b2 * b2 * g11 - 2 * b1 * b2 * g12) / det
    return float(math.sqrt(max(snr2, 0.0)))
