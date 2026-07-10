"""
Diagnostics on PE residuals vs positional echo ladder.

Answers: does any Δχ² come from structure at predicted delays,
or from broadband noise fitting?
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .echo_ladder import EchoStep, chi2, fit_two_amplitudes, residual_power_at_delays
from .gw_events import PublicGWEvent
from .invariants import InvariantSet


def window_mask(
    t: np.ndarray, center: float, half_window_s: float
) -> np.ndarray:
    return np.abs(t - center) <= half_window_s


def per_echo_delta_chi2(
    residual: np.ndarray,
    t: np.ndarray,
    echo_templates: list[np.ndarray],
    steps: list[EchoStep],
    sigma: float,
    half_window_s: float = 0.002,
) -> list[dict[str, Any]]:
    """For each echo, fit only that component and report local Δχ²."""
    out = []
    for step, templ in zip(steps, echo_templates):
        m = window_mask(t, step.delay_s, half_window_s)
        if not np.any(m) or float(np.std(templ[m])) < 1e-40:
            out.append(
                {
                    "n": step.n,
                    "delay_s": step.delay_s,
                    "delta_chi2_local": 0.0,
                    "a1_local": 0.0,
                    "rms_residual": float("nan"),
                    "rms_template": float("nan"),
                    "n_samples": int(np.sum(m)),
                }
            )
            continue
        # local 1-param fit on window
        y = residual[m]
        x = templ[m]
        w = 1.0 / (sigma**2 + 1e-60)
        a1 = float(np.sum(y * x * w) / (np.sum(x * x * w) + 1e-60))
        chi0 = float(np.sum((y**2) * w))
        chi1 = float(np.sum(((y - a1 * x) ** 2) * w))
        out.append(
            {
                "n": step.n,
                "delay_s": step.delay_s,
                "delta_chi2_local": chi0 - chi1,
                "a1_local": a1,
                "rms_residual": float(np.sqrt(np.mean(y**2))),
                "rms_template": float(np.sqrt(np.mean(x**2))),
                "n_samples": int(np.sum(m)),
            }
        )
    return out


def matched_filter_snr_at_delays(
    residual: np.ndarray,
    t: np.ndarray,
    echo_templates: list[np.ndarray],
    steps: list[EchoStep],
    sigma: float,
) -> list[dict[str, Any]]:
    """White-noise matched-filter SNR of each unit echo template vs residual."""
    out = []
    for step, templ in zip(steps, echo_templates):
        # normalize template energy
        norm = float(np.sqrt(np.sum(templ**2))) + 1e-60
        snr = float(np.sum(residual * templ) / (sigma * norm))
        out.append(
            {
                "n": step.n,
                "delay_s": step.delay_s,
                "mf_snr": snr,
                "template_norm": norm,
            }
        )
    return out


def build_unit_echo_templates(
    t: np.ndarray,
    event: PublicGWEvent,
    steps: list[EchoStep],
    *,
    tau_scale: float = 0.015,
) -> list[np.ndarray]:
    """One template per ladder step (amp_prior folded in for train consistency)."""
    from .echo_ladder import ringdown_template

    tau = tau_scale * (event.mass_final_solar / 30.0)
    templates = []
    for step in steps:
        templates.append(
            step.amp_prior
            * ringdown_template(
                t,
                f0=event.f_ring_hz,
                tau=tau * 1.2,
                t0=step.delay_s,
                phase0=step.braiding_angle,
            )
        )
    return templates


def summarize_residual(
    residual: np.ndarray,
    t: np.ndarray,
    event: PublicGWEvent,
    steps: list[EchoStep],
    sigma: float,
    *,
    primary: np.ndarray | None = None,
    half_window_s: float = 0.002,
) -> dict[str, Any]:
    """Full residual vs ladder diagnostic bundle."""
    inv = InvariantSet()
    templates = build_unit_echo_templates(t, event, steps)
    echo_train = np.sum(templates, axis=0) if templates else np.zeros_like(t)

    if primary is None:
        from .echo_ladder import baseline_ringdown

        primary = baseline_ringdown(t, event)

    a0, a1 = fit_two_amplitudes(residual, primary, echo_train, sigma)
    pred = a0 * primary + a1 * echo_train
    chi_null = chi2(residual, np.zeros_like(residual), sigma)
    chi_base = chi2(residual, a0 * primary, sigma)
    chi_toe = chi2(residual, pred, sigma)

    power = residual_power_at_delays(residual, t, steps, half_window_s=half_window_s)
    # off-echo control windows: midway between delays
    control_steps = []
    for i, step in enumerate(steps):
        if i + 1 < len(steps):
            mid = 0.5 * (step.delay_s + steps[i + 1].delay_s)
        else:
            mid = step.delay_s + (step.delay_s - steps[0].delay_s)
        control_steps.append(
            EchoStep(
                n=-(step.n),
                delay_s=mid,
                uncertainty_s=step.uncertainty_s,
                amp_prior=0.0,
                fiber_angle=0.0,
                phase_unit=0.0,
                braiding_angle=0.0,
            )
        )
    power_ctrl = residual_power_at_delays(
        residual, t, control_steps, half_window_s=half_window_s
    )

    local = per_echo_delta_chi2(
        residual, t, templates, steps, sigma, half_window_s=half_window_s
    )
    snrs = matched_filter_snr_at_delays(residual, t, templates, steps, sigma)

    # Local free-amp Δχ² is always ≥0 (can fit noise); only count a1_local>0
    local_pos = sum(
        d["delta_chi2_local"] for d in local if d["a1_local"] > 0 and d["delta_chi2_local"] > 0
    )
    global_delta = chi_base - chi_toe
    max_mf = max((abs(s["mf_snr"]) for s in snrs), default=0.0)

    return {
        "wg": inv.wg,
        "kappa": inv.kappa,
        "sigma": sigma,
        "n_samples": int(residual.size),
        "a0_leftover_ringdown": a0,
        "a1_echo_scale": a1,
        "chi2_null": chi_null,
        "chi2_baseline": chi_base,
        "chi2_toe": chi_toe,
        "delta_chi2_global": global_delta,
        "sum_local_positive_a1_delta_chi2": local_pos,
        "max_abs_mf_snr": max_mf,
        "per_echo": local,
        "mf_snr": snrs,
        "rms_at_echo_windows": power,
        "rms_at_control_windows": power_ctrl,
        "note_local_dchi2": (
            "Per-echo Δχ² uses unconstrained a1 on a short window and can fit noise; "
            "prefer MF SNR and global a1 for support claims."
        ),
        "interpretation": _interpret(global_delta, a1, local, snrs),
    }


def _interpret(
    delta: float,
    a1: float,
    local: list[dict[str, Any]],
    snrs: list[dict[str, Any]],
) -> str:
    max_local = max((d["delta_chi2_local"] for d in local), default=0.0)
    max_snr = max((abs(s["mf_snr"]) for s in snrs), default=0.0)
    if abs(delta) < 0.5 and abs(a1) < 1e-30 and max_snr < 2.0:
        return (
            "Near-null: global Δχ² tiny, a1≈0, no echo window exceeds ~2σ MF SNR. "
            "Ladder is not capturing residual structure under this noise model."
        )
    if max_local > 2.0 and delta < 1.0:
        return (
            "Local windows show some Δχ² but global fit does not; "
            "possible noise spikes or template mismatch (phase/amp)."
        )
    if delta > 2.0 and a1 > 0:
        return (
            "Positive support for echo scale with Δχ²>2; "
            "verify with injections and multi-detector coherence before claims."
        )
    if a1 < 0 and delta > 0:
        return (
            "Fit prefers negative echo scale (anti-template); "
            "not physical support for the ladder — often noise or phase error."
        )
    return (
        f"Weak/ambiguous: Δχ²={delta:.3f}, a1={a1:.3e}, max|MF SNR|={max_snr:.2f}."
    )
