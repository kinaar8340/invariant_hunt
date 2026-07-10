#!/usr/bin/env python3
"""
Head-to-head comparison: positional echo ladder vs no-echo ringdown.

Modes
-----
synthetic (default)
    Mock observation = baseline or injected echoes + noise.

event (public GWOSC strain)
    Observation = real band-limited strain around a catalog event
    (default GW150914). Templates are amplitude-fitted to the data;
    χ² and residual power at predicted echo delays are reported.

Usage
-----
  python scripts/compare_benchmark.py
  python scripts/compare_benchmark.py --inject-echoes
  python scripts/compare_benchmark.py --event GW150914
  python scripts/compare_benchmark.py --event GW150914 --detector H1 --n-echoes 5
  python scripts/compare_benchmark.py --event GW150914 --spacing phase_unit
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.echo_ladder import (  # noqa: E402
    baseline_ringdown,
    chi2,
    fit_amplitude,
    fit_two_amplitudes,
    ladder_prediction_records,
    primary_and_echo_basis,
    residual_power_at_delays,
)
from src.gw_events import get_event  # noqa: E402
from src.gwosc_data import load_event_segment, noise_sigma_premerger  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.positional import PositionalPhase, phase_to_frequency  # noqa: E402
from src.predictions import write_prediction_bundle  # noqa: E402


def ringdown(t: np.ndarray, f0: float, tau: float, t0: float = 0.0) -> np.ndarray:
    x = t - t0
    out = np.zeros_like(t)
    m = x >= 0
    out[m] = np.exp(-x[m] / tau) * np.sin(2 * np.pi * f0 * x[m])
    return out


def model_echo_train_synthetic(
    t: np.ndarray,
    inv: InvariantSet,
    mass_solar: float,
    scale_hz: float,
    n_echoes: int,
) -> np.ndarray:
    """Legacy synthetic train (phase_unit delays via t_m·2π·n/W_g·(1+κ))."""
    f0 = phase_to_frequency(PositionalPhase(wg=inv.wg), scale_hz=scale_hz, wg=inv.wg)
    tau = 0.015 * (mass_solar / 30.0)
    h = ringdown(t, f0, tau)
    t_m = 4.925490947e-6 * mass_solar
    for n in range(1, n_echoes + 1):
        delay = t_m * (2.0 * np.pi / inv.wg) * n * (1.0 + inv.kappa)
        amp = 0.35**n
        phase = PositionalPhase(wg=inv.wg, lattice_index=n)
        h = h + amp * ringdown(t, f0, tau * 1.2, t0=delay) * np.cos(phase.braiding_angle)
    return h


def run_synthetic(args: argparse.Namespace) -> dict:
    inv = InvariantSet()
    sample_rate = 4096.0
    duration = 0.25
    t = np.arange(0.0, duration, 1.0 / sample_rate)
    f0 = phase_to_frequency(
        PositionalPhase(wg=inv.wg), scale_hz=args.scale_hz, wg=inv.wg
    )
    tau = 0.015 * (args.mass / 30.0)

    rng = np.random.default_rng(42)
    noise = args.noise * rng.standard_normal(t.shape)

    baseline = ringdown(t, f0, tau)
    toe_model = model_echo_train_synthetic(
        t, inv, args.mass, args.scale_hz, args.n_echoes
    )

    if args.inject_echoes:
        truth = toe_model
        truth_label = "positional_echoes"
    else:
        truth = baseline
        truth_label = "no_echo_ringdown"

    obs = truth + noise
    sigma = args.noise if args.noise > 0 else 1.0

    chi2_baseline = chi2(obs, baseline, sigma)
    chi2_toe = chi2(obs, toe_model, sigma)
    delta = chi2_baseline - chi2_toe

    return {
        "schema": "invariant_hunt.benchmark.v2",
        "mode": "synthetic",
        "truth": truth_label,
        "n_samples": int(len(t)),
        "noise_sigma": args.noise,
        "chi2_baseline_no_echo": chi2_baseline,
        "chi2_toe_positional_echo": chi2_toe,
        "delta_chi2_base_minus_toe": delta,
        "prefers": "toe_positional" if delta > 0 else "baseline",
        "wg": inv.wg,
        "mass_solar": args.mass,
        "f0_hz": f0,
        "note": "Synthetic observation (not public detector strain).",
    }


def run_event(args: argparse.Namespace) -> dict:
    inv = InvariantSet()
    event = get_event(args.event)
    cache = project_root / "data" / "gwosc"

    print(f"Loading public strain: {event.name} / {args.detector}")
    seg = load_event_segment(
        event,
        detector=args.detector,
        cache_dir=cache,
        f_low=args.f_low,
        f_high=args.f_high,
        apply_bandpass=True,
    )
    t = seg.t_rel
    obs = seg.h
    # post-merger-only fit (avoid inspiral mismatch dominating χ²)
    post = t >= 0.0
    t_post = t[post]
    obs_post = obs[post]

    sigma = noise_sigma_premerger(seg)
    print(f"  pre-merger σ ≈ {sigma:.3e}  (band-limited)")
    print(f"  samples post-merger: {t_post.size} @ {seg.sample_rate:.0f} Hz")

    primary, echoes, steps = primary_and_echo_basis(
        t_post,
        event,
        inv,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
    )

    # Nested models:
    #   baseline: obs ≈ a0 * primary
    #   toe:      obs ≈ a0 * primary + a1 * echo_train (relative amps from ladder)
    a_base = fit_amplitude(obs_post, primary, sigma)
    pred_base = a_base * primary
    a0_toe, a1_toe = fit_two_amplitudes(obs_post, primary, echoes, sigma)
    pred_toe = a0_toe * primary + a1_toe * echoes

    chi2_baseline = chi2(obs_post, pred_base, sigma)
    chi2_toe = chi2(obs_post, pred_toe, sigma)
    delta = chi2_baseline - chi2_toe
    dof_base = max(int(t_post.size) - 1, 1)
    dof_toe = max(int(t_post.size) - 2, 1)

    resid_base = obs_post - pred_base
    resid_toe = obs_post - pred_toe
    power_base = residual_power_at_delays(resid_base, t_post, steps)
    power_toe = residual_power_at_delays(resid_toe, t_post, steps)

    # prediction bundle for this event
    recs = ladder_prediction_records(
        event, inv, n_echoes=args.n_echoes, mode=args.spacing
    )
    bundle_path = (
        project_root
        / "outputs"
        / "predictions"
        / f"{event.name}_echo_ladder_{args.spacing}.json"
    )
    write_prediction_bundle(recs, bundle_path)

    ladder = [s.to_dict() for s in steps]
    print(f"  echo ladder ({args.spacing}):")
    for s in steps:
        print(
            f"    n={s.n}: δt={s.delay_s*1e3:.4f} ms  "
            f"(±{s.uncertainty_s*1e3:.4f} ms)  amp_prior={s.amp_prior:.4f}"
        )
    print(f"  wrote prediction bundle → {bundle_path}")

    # optional plot
    plot_path = None
    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
            axes[0].plot(t_post * 1e3, obs_post, lw=0.7, color="0.4", label="obs")
            axes[0].plot(
                t_post * 1e3, pred_base, lw=1.0, label=f"baseline a0={a_base:.2e}"
            )
            axes[0].plot(
                t_post * 1e3,
                pred_toe,
                lw=1.0,
                label=f"toe a0={a0_toe:.2e} a1={a1_toe:.2e}",
            )
            for s in steps:
                axes[0].axvline(s.delay_s * 1e3, color="C3", alpha=0.35, ls="--")
            axes[0].set_ylabel("strain (band-limited)")
            axes[0].legend(loc="upper right", fontsize=8)
            axes[0].set_title(
                f"{event.name} {args.detector} — positional ladder ({args.spacing})"
            )

            axes[1].plot(t_post * 1e3, resid_base, lw=0.7, label="resid baseline")
            axes[1].plot(t_post * 1e3, resid_toe, lw=0.7, label="resid toe")
            for s in steps:
                axes[1].axvline(s.delay_s * 1e3, color="C3", alpha=0.35, ls="--")
            axes[1].set_xlabel("t − t_merger [ms]")
            axes[1].set_ylabel("residual")
            axes[1].legend(loc="upper right", fontsize=8)
            fig.tight_layout()
            plot_path = str(
                project_root
                / "outputs"
                / "benchmarks"
                / f"{event.name}_{args.detector}_{args.spacing}.png"
            )
            Path(plot_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(plot_path, dpi=150)
            print(f"  wrote plot → {plot_path}")
        except ImportError:
            print("  matplotlib not available; skip plot")

    # save npz of series for external re-analysis
    npz_path = (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_{args.detector}_{args.spacing}_series.npz"
    )
    np.savez(
        npz_path,
        t_post=t_post,
        obs_post=obs_post,
        pred_base=pred_base,
        pred_toe=pred_toe,
        resid_base=resid_base,
        resid_toe=resid_toe,
        delays=np.array([s.delay_s for s in steps]),
    )

    prefers = "toe_positional" if delta > 0 else "baseline"
    # Prefer on reduced-χ² and only call a preference if |Δχ²| > 2 (weak threshold)
    if abs(delta) < 2.0:
        prefers = "inconclusive"

    return {
        "schema": "invariant_hunt.benchmark.v2",
        "mode": "public_event",
        "event": event.to_dict(),
        "detector": args.detector,
        "data_path": str(seg.path),
        "spacing_mode": args.spacing,
        "n_echoes": args.n_echoes,
        "n_samples_post": int(t_post.size),
        "sample_rate": seg.sample_rate,
        "noise_sigma_premerger": sigma,
        "bandpass_hz": [args.f_low, args.f_high],
        "fit_amplitude_baseline": a_base,
        "fit_amplitude_toe_primary": a0_toe,
        "fit_amplitude_toe_echoes": a1_toe,
        "chi2_baseline_no_echo": chi2_baseline,
        "chi2_toe_positional_echo": chi2_toe,
        "chi2_red_baseline": chi2_baseline / dof_base,
        "chi2_red_toe": chi2_toe / dof_toe,
        "delta_chi2_base_minus_toe": delta,
        "prefers": prefers,
        "wg": inv.wg,
        "kappa": inv.kappa,
        "f_ring_hz": event.f_ring_hz,
        "mass_final_solar": event.mass_final_solar,
        "echo_ladder": ladder,
        "residual_rms_at_delays_baseline": power_base,
        "residual_rms_at_delays_toe": power_toe,
        "prediction_bundle": str(bundle_path),
        "series_npz": str(npz_path),
        "plot": plot_path,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Public GWOSC strain with a simple damped-sinusoid ringdown family — "
            "not a published GR NR baseline. Positive Δχ² favors the positional "
            "echo template under this toy family only; scientific claims require "
            "full PE waveforms, PSD whitening, and look-elsewhere corrections."
        ),
        "falsify_checkpoint": (
            f"If prefers stays 'baseline' or 'inconclusive' under geometric spacing "
            f"for {event.name} after NR-quality baselines, revise echo mapping "
            f"(κ, spacing, amp priors) before claiming support for the ladder."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark positional echoes")
    parser.add_argument("--event", type=str, default="",
                        help="Public event name (e.g. GW150914). Empty = synthetic.")
    parser.add_argument("--detector", type=str, default="H1")
    parser.add_argument("--mass", type=float, default=30.0, help="Synthetic remnant mass")
    parser.add_argument("--scale-hz", type=float, default=250.0)
    parser.add_argument("--n-echoes", type=int, default=5)
    parser.add_argument("--inject-echoes", action="store_true")
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument(
        "--spacing",
        choices=("geometric", "phase_unit"),
        default="geometric",
        help="Echo delay spacing (geometric is LIGO-resolvable)",
    )
    parser.add_argument("--amp0", type=float, default=0.35, help="Echo amplitude prior base")
    parser.add_argument("--f-low", type=float, default=50.0)
    parser.add_argument("--f-high", type=float, default=300.0)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    if args.event:
        result = run_event(args)
        label = f"public event {args.event}/{args.detector}"
        default_out = (
            f"outputs/benchmarks/{args.event}_{args.detector}_{args.spacing}.json"
        )
    else:
        result = run_synthetic(args)
        label = "synthetic"
        default_out = "outputs/benchmarks/compare.json"

    out = project_root / (args.out or default_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Benchmark comparison ({label})")
    if "truth" in result:
        print(f"  truth model     : {result['truth']}")
    print(f"  χ² baseline     : {result['chi2_baseline_no_echo']:.2f}")
    print(f"  χ² TOE echoes   : {result['chi2_toe_positional_echo']:.2f}")
    print(
        f"  Δχ² (base-toe)  : {result['delta_chi2_base_minus_toe']:.2f}  "
        f"→ prefers {result['prefers']}"
    )
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
