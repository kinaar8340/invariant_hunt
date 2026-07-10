"""
Positional echo-delay ladder mapped onto a public GW remnant.

Two spacing conventions (documented, selectable):

1. **phase_unit** (strict lattice fraction of W_g)
       δt_n = (GM/c³) · 2π · (n / W_g) · (1+κ)
   Sub-sample for stellar-mass remnants at 4096 Hz — useful as a
   theoretical lock residual, not as a LIGO template spacing.

2. **geometric** (default for public-data mapping; instrument-resolvable)
       δt_n = (GM/c³) · 2π · n · (1+κ)
   Equivalent to counting lattice index in geometric radians of remnant
   time, with holonomy lift κ. For GW150914 (M≈62 M_☉, κ=0.85) the
   first delay is ~3.5 ms — in the band of published echo searches.

W_g still sets spectral / phase structure via PositionalPhase.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np

from .amp_structure import AmpStructure, normalize_weights, step_weight
from .gw_events import T_M_SUN, PublicGWEvent
from .invariants import InvariantSet
from .positional import PositionalPhase
from .predictions import PredictionRecord, gw_echo_delay

SpacingMode = Literal["phase_unit", "geometric"]


@dataclass
class EchoStep:
    n: int
    delay_s: float
    uncertainty_s: float
    amp_prior: float
    fiber_angle: float
    phase_unit: float
    braiding_angle: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def echo_delay_seconds(
    n: int,
    mass_solar: float,
    inv: InvariantSet | None = None,
    mode: SpacingMode = "geometric",
) -> float:
    """Delay of the n-th positional echo after merger (n ≥ 1)."""
    inv = inv or InvariantSet()
    t_m = T_M_SUN * mass_solar
    if mode == "phase_unit":
        # same as predictions.gw_echo_delay
        return t_m * 2.0 * math.pi * (n / inv.wg) * (1.0 + inv.kappa)
    if mode == "geometric":
        return t_m * 2.0 * math.pi * float(n) * (1.0 + inv.kappa)
    raise ValueError(f"Unknown spacing mode: {mode}")


def build_ladder(
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    amp0: float = 0.35,
    rel_uncertainty: float = 0.15,
    amp_structure: AmpStructure = "geometric",
    normalize_amps: bool = True,
) -> list[EchoStep]:
    """Build the echo ladder for a public event + locked invariants.

    ``amp_structure`` selects relative step weights (see ``src/amp_structure.py``).
    Delays still use geometric / phase_unit spacing from W_g, κ.
    """
    inv = inv or InvariantSet()
    raw: list[tuple[int, float, float, float, float, float]] = []
    weights: list[float] = []
    for n in range(1, n_echoes + 1):
        delay = echo_delay_seconds(n, event.mass_final_solar, inv, mode=mode)
        phase = PositionalPhase(wg=inv.wg, lattice_index=n)
        w = step_weight(
            n,
            braiding_angle=phase.braiding_angle,
            inv=inv,
            amp0=amp0,
            structure=amp_structure,
        )
        weights.append(w)
        raw.append(
            (
                n,
                delay,
                rel_uncertainty * delay,
                phase.fiber_angle,
                phase.lattice_phase_unit,
                phase.braiding_angle,
            )
        )
    if normalize_amps:
        weights = normalize_weights(weights)
    steps: list[EchoStep] = []
    for (n, delay, unc, fib, punit, braid), w in zip(raw, weights):
        steps.append(
            EchoStep(
                n=n,
                delay_s=delay,
                uncertainty_s=unc,
                amp_prior=float(w),
                fiber_angle=fib,
                phase_unit=punit,
                braiding_angle=braid,
            )
        )
    return steps


def ladder_prediction_records(
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
) -> list[PredictionRecord]:
    """PredictionRecord list for the event-specific ladder (falsify_if included)."""
    inv = inv or InvariantSet()
    records: list[PredictionRecord] = []
    for step in build_ladder(event, inv, n_echoes=n_echoes, mode=mode):
        if mode == "phase_unit":
            # reuse core formula path
            rec = gw_echo_delay(inv, mass_solar=event.mass_final_solar, lattice_index=step.n)
            rec.assumptions["event"] = event.name
            rec.assumptions["spacing_mode"] = mode
            records.append(rec)
            continue
        records.append(
            PredictionRecord(
                name=f"gw_echo_delay_{event.name}_n{step.n}",
                domain="gw_echo",
                quantity="echo_delay_s",
                value=step.delay_s,
                unit="s",
                uncertainty=step.uncertainty_s,
                assumptions={
                    "event": event.name,
                    "gps": event.gps,
                    "mass_final_solar": event.mass_final_solar,
                    "wg": inv.wg,
                    "kappa": inv.kappa,
                    "lattice_index": step.n,
                    "spacing_mode": mode,
                    "formula": "δt = (GM/c³)·2π·n·(1+κ)",
                    "amp_prior": step.amp_prior,
                },
                falsify_if=(
                    f"If post-merger residuals of {event.name} show no excess near "
                    f"t={step.delay_s*1e3:.3f}±{step.uncertainty_s*1e3:.3f} ms "
                    f"(n={step.n}, geometric spacing), revise κ, mass scale, or "
                    f"spacing mode — not the numerical lock of W_g alone."
                ),
            )
        )
    return records


def ringdown_template(
    t: np.ndarray,
    *,
    f0: float,
    tau: float,
    t0: float = 0.0,
    phase0: float = 0.0,
) -> np.ndarray:
    """Causal damped sinusoid for t ≥ t0."""
    x = t - t0
    out = np.zeros_like(t, dtype=np.float64)
    m = x >= 0.0
    out[m] = np.exp(-x[m] / tau) * np.sin(2.0 * np.pi * f0 * x[m] + phase0)
    return out


def baseline_ringdown(
    t: np.ndarray,
    event: PublicGWEvent,
    *,
    tau_scale: float = 0.015,
) -> np.ndarray:
    """GR-like single ringdown (no echoes), unit amplitude."""
    tau = tau_scale * (event.mass_final_solar / 30.0)
    return ringdown_template(t, f0=event.f_ring_hz, tau=tau, t0=0.0)


def positional_echo_template(
    t: np.ndarray,
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    tau_scale: float = 0.015,
    amp0: float = 0.35,
) -> tuple[np.ndarray, list[EchoStep]]:
    """Unit-scale primary ringdown + positional echo train (summed)."""
    primary, echoes, steps = primary_and_echo_basis(
        t, event, inv, n_echoes=n_echoes, mode=mode, tau_scale=tau_scale, amp0=amp0
    )
    return primary + echoes, steps


def primary_and_echo_basis(
    t: np.ndarray,
    event: PublicGWEvent,
    inv: InvariantSet | None = None,
    *,
    n_echoes: int = 5,
    mode: SpacingMode = "geometric",
    tau_scale: float = 0.015,
    amp0: float = 0.35,
    amp_structure: AmpStructure = "geometric",
) -> tuple[np.ndarray, np.ndarray, list[EchoStep]]:
    """Separate primary ringdown and weighted echo train (unit primary)."""
    inv = inv or InvariantSet()
    tau = tau_scale * (event.mass_final_solar / 30.0)
    primary = baseline_ringdown(t, event, tau_scale=tau_scale)
    steps = build_ladder(
        event,
        inv,
        n_echoes=n_echoes,
        mode=mode,
        amp0=amp0,
        amp_structure=amp_structure,
    )
    echoes = np.zeros_like(t, dtype=np.float64)
    for step in steps:
        echoes = echoes + step.amp_prior * ringdown_template(
            t,
            f0=event.f_ring_hz,
            tau=tau * 1.2,
            t0=step.delay_s,
            phase0=step.braiding_angle,
        )
    return primary, echoes, steps


def fit_amplitude(obs: np.ndarray, template: np.ndarray, sigma: float) -> float:
    """ML amplitude for obs ≈ a * template under white noise."""
    w = 1.0 / (sigma**2 + 1e-60)
    denom = float(np.sum(template * template * w))
    if denom <= 0:
        return 0.0
    return float(np.sum(obs * template * w) / denom)


def fit_two_amplitudes(
    obs: np.ndarray,
    primary: np.ndarray,
    echoes: np.ndarray,
    sigma: float,
) -> tuple[float, float]:
    """ML amplitudes for obs ≈ a0 * primary + a1 * echoes (white noise).

    Returns (a0, a1). If echoes are linearly dependent / zero, a1=0.
    """
    w = 1.0 / (sigma**2 + 1e-60)
    # Normal equations for 2-parameter weighted LS
    p = primary
    e = echoes
    app = float(np.sum(p * p * w))
    aee = float(np.sum(e * e * w))
    ape = float(np.sum(p * e * w))
    bp = float(np.sum(obs * p * w))
    be = float(np.sum(obs * e * w))
    det = app * aee - ape * ape
    if aee < 1e-60 or abs(det) < 1e-60 * max(app, 1.0):
        a0 = bp / app if app > 0 else 0.0
        return float(a0), 0.0
    a0 = (bp * aee - be * ape) / det
    a1 = (be * app - bp * ape) / det
    return float(a0), float(a1)


def chi2(obs: np.ndarray, pred: np.ndarray, sigma: float) -> float:
    r = (obs - pred) / (sigma + 1e-60)
    return float(np.sum(r**2))


def residual_power_at_delays(
    residual: np.ndarray,
    t: np.ndarray,
    steps: list[EchoStep],
    *,
    half_window_s: float = 0.002,
) -> list[dict[str, float]]:
    """RMS residual in a short window around each predicted echo."""
    out = []
    for step in steps:
        m = np.abs(t - step.delay_s) <= half_window_s
        if not np.any(m):
            rms = float("nan")
            n = 0
        else:
            rms = float(np.sqrt(np.mean(residual[m] ** 2)))
            n = int(np.sum(m))
        out.append(
            {
                "n": float(step.n),
                "delay_s": step.delay_s,
                "window_rms": rms,
                "n_samples": float(n),
            }
        )
    return out
