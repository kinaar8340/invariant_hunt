#!/usr/bin/env python3
"""
Head-to-head comparison: positional echo ladder vs GR baseline.

Modes
-----
synthetic (default)
    Mock observation = baseline or injected echoes + noise.

event + --baseline toy
    Observation = public GWOSC strain. Baseline = damped-sinusoid ringdown.

event + --baseline pe  (recommended)
    Observation = public GWOSC strain.
    Baseline = published GWTC-1 PE medians → IMRPhenomD (PyCBC), lag + (A+,Ax) fit.
    Echo test runs on the **PE residual** post-merger:
        residual ≈ 0   vs   residual ≈ a1 * echo_train

Usage
-----
  python scripts/compare_benchmark.py
  python scripts/compare_benchmark.py --inject-echoes
  python scripts/compare_benchmark.py --event GW150914 --baseline pe --plot
  python scripts/compare_benchmark.py --event GW150914 --baseline toy --detector H1
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
        "schema": "invariant_hunt.benchmark.v3",
        "mode": "synthetic",
        "baseline_model": "toy_ringdown",
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


def _prefers_label(delta: float, threshold: float = 2.0) -> str:
    if abs(delta) < threshold:
        return "inconclusive"
    return "toe_positional" if delta > 0 else "baseline"


def run_event_toy(args: argparse.Namespace, seg, event, inv, sigma: float) -> dict:
    """Legacy: toy damped sinusoid as GR stand-in on raw post-merger strain."""
    t = seg.t_rel
    obs = seg.h
    post = t >= 0.0
    t_post = t[post]
    obs_post = obs[post]

    primary, echoes, steps = primary_and_echo_basis(
        t_post,
        event,
        inv,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
    )

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

    return {
        "obs_label": "bandpassed_strain_post",
        "t_post": t_post,
        "obs_post": obs_post,
        "pred_base": pred_base,
        "pred_toe": pred_toe,
        "resid_base": resid_base,
        "resid_toe": resid_toe,
        "steps": steps,
        "a_base": a_base,
        "a0_toe": a0_toe,
        "a1_toe": a1_toe,
        "chi2_baseline": chi2_baseline,
        "chi2_toe": chi2_toe,
        "delta": delta,
        "dof_base": dof_base,
        "dof_toe": dof_toe,
        "pe_fit": None,
        "note": (
            "Toy damped-sinusoid ringdown family on raw post-merger strain — "
            "not a published GR PE/NR baseline."
        ),
    }


def run_event_pe(args: argparse.Namespace, seg, event, inv, sigma: float) -> dict:
    """PE residual analysis: subtract IMRPhenomD(PE medians), then test echoes."""
    from src.pe_waveform import fit_pe_to_strain, pe_params_for_event

    pe_dir = project_root / "data" / "pe"
    params = pe_params_for_event(event.name, pe_dir=pe_dir)
    print(
        f"  PE medians: m1={params.mass1:.2f} m2={params.mass2:.2f} M☉  "
        f"d_L={params.distance_mpc:.0f} Mpc  "
        f"χ1z={params.spin1z:.3f} χ2z={params.spin2z:.3f}  "
        f"[{params.posterior_dataset}, n={params.n_samples}]"
    )
    print(f"  approximant: {params.approximant}")

    pe_fit = fit_pe_to_strain(
        seg.t_rel,
        seg.h,
        params,
        sample_rate=seg.sample_rate,
        sigma=sigma,
        f_low=args.f_low,
        f_high=args.f_high,
        lag_min=args.lag_min,
        lag_max=args.lag_max,
        fit_t_min=args.fit_t_min,
        fit_t_max=args.fit_t_max,
    )
    print(
        f"  PE fit: lag={pe_fit.lag_s*1e3:.2f} ms  "
        f"A+={pe_fit.a_plus:.3f}  Ax={pe_fit.a_cross:.3f}  "
        f"χ²_fit={pe_fit.chi2:.1f}  SNR_proxy={pe_fit.snr_proxy:.1f}"
    )

    # Echo ladder on PE residual, post-merger only
    t = seg.t_rel
    residual = pe_fit.residual
    post = t >= 0.0
    t_post = t[post]
    # baseline prediction on residual is 0 (GR PE already subtracted)
    # toe: residual ≈ a1 * echo_train  (primary of echo basis unused)
    _primary, echoes, steps = primary_and_echo_basis(
        t_post,
        event,
        inv,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
    )
    # Use only the echo train piece; optional weak primary allows residual ringdown
    # that PE did not capture — fit a0 * primary + a1 * echoes on residual
    primary_rd = baseline_ringdown(t_post, event)
    resid_post = residual[post]

    # baseline: residual ≈ 0  (optionally residual ≈ a0 * leftover ringdown)
    a_base = fit_amplitude(resid_post, primary_rd, sigma)
    pred_base = a_base * primary_rd  # leftover ringdown only; no echoes
    a0_toe, a1_toe = fit_two_amplitudes(resid_post, primary_rd, echoes, sigma)
    pred_toe = a0_toe * primary_rd + a1_toe * echoes

    # pure-null baseline (residual ≡ 0) also reported
    chi2_null = chi2(resid_post, np.zeros_like(resid_post), sigma)
    chi2_baseline = chi2(resid_post, pred_base, sigma)
    chi2_toe = chi2(resid_post, pred_toe, sigma)
    # Primary comparison for "prefers": null residual vs residual+echoes
    # (leftover ringdown is a nuisance; report both)
    delta = chi2_baseline - chi2_toe
    delta_null = chi2_null - chi2_toe

    resid_base = resid_post - pred_base
    resid_toe = resid_post - pred_toe

    return {
        "obs_label": "pe_residual_post",
        "t_post": t_post,
        "obs_post": resid_post,
        "obs_raw_post": seg.h[post],
        "pe_template_post": pe_fit.template[post],
        "pred_base": pred_base,
        "pred_toe": pred_toe,
        "resid_base": resid_base,
        "resid_toe": resid_toe,
        "steps": steps,
        "a_base": a_base,
        "a0_toe": a0_toe,
        "a1_toe": a1_toe,
        "chi2_baseline": chi2_baseline,
        "chi2_toe": chi2_toe,
        "chi2_null": chi2_null,
        "delta": delta,
        "delta_null": delta_null,
        "dof_base": max(int(t_post.size) - 1, 1),
        "dof_toe": max(int(t_post.size) - 2, 1),
        "pe_fit": pe_fit,
        "note": (
            "Baseline = GWTC-1 Overall_posterior medians → IMRPhenomD (PyCBC), "
            "with lag + (A+, Ax) LS fit on the inspiral–merger window. "
            "Echo model is fit on the post-merger PE residual. "
            "Not a full coherent multi-detector PE with PSD whitening; "
            "Δχ² is under a white band-limited noise model only."
        ),
    }


def run_event(args: argparse.Namespace) -> dict:
    inv = InvariantSet()
    event = get_event(args.event)
    cache = project_root / "data" / "gwosc"

    # PE needs longer pre-merger context for IMR template
    pre = 0.25 if args.baseline == "pe" else event.duration_pre_s
    post_s = event.duration_post_s

    print(f"Loading public strain: {event.name} / {args.detector}")
    print(f"  baseline model: {args.baseline}")
    seg = load_event_segment(
        event,
        detector=args.detector,
        cache_dir=cache,
        f_low=args.f_low,
        f_high=args.f_high,
        apply_bandpass=True,
        duration_pre_s=pre,
        duration_post_s=post_s,
    )
    sigma = noise_sigma_premerger(seg)
    print(f"  pre-merger σ ≈ {sigma:.3e}  (band-limited)")
    print(
        f"  window [{seg.t_rel[0]:.3f}, {seg.t_rel[-1]:.3f}] s  "
        f"@ {seg.sample_rate:.0f} Hz  (n={seg.n})"
    )

    if args.baseline == "pe":
        pack = run_event_pe(args, seg, event, inv, sigma)
    else:
        pack = run_event_toy(args, seg, event, inv, sigma)

    t_post = pack["t_post"]
    steps = pack["steps"]
    power_base = residual_power_at_delays(pack["resid_base"], t_post, steps)
    power_toe = residual_power_at_delays(pack["resid_toe"], t_post, steps)

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

    tag = f"{event.name}_{args.detector}_{args.baseline}_{args.spacing}"
    plot_path = None
    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(3 if args.baseline == "pe" else 2, 1,
                                     figsize=(10, 7 if args.baseline == "pe" else 5),
                                     sharex=True)
            if args.baseline == "pe":
                axes[0].plot(
                    t_post * 1e3, pack["obs_raw_post"], lw=0.7, color="0.5", label="strain"
                )
                axes[0].plot(
                    t_post * 1e3,
                    pack["pe_template_post"],
                    lw=1.0,
                    label="PE IMR fit",
                )
                axes[0].set_ylabel("strain")
                axes[0].legend(loc="upper right", fontsize=8)
                axes[0].set_title(
                    f"{event.name} {args.detector} — PE residual + positional ladder"
                )
                ax_r, ax_e = axes[1], axes[2]
            else:
                axes[0].plot(
                    t_post * 1e3, pack["obs_post"], lw=0.7, color="0.4", label="obs"
                )
                axes[0].plot(
                    t_post * 1e3,
                    pack["pred_base"],
                    lw=1.0,
                    label=f"baseline a0={pack['a_base']:.2e}",
                )
                axes[0].plot(
                    t_post * 1e3,
                    pack["pred_toe"],
                    lw=1.0,
                    label=f"toe a0={pack['a0_toe']:.2e} a1={pack['a1_toe']:.2e}",
                )
                axes[0].set_ylabel("strain")
                axes[0].legend(loc="upper right", fontsize=8)
                axes[0].set_title(
                    f"{event.name} {args.detector} — toy baseline ({args.spacing})"
                )
                ax_r, ax_e = axes[0], axes[1]

            if args.baseline == "pe":
                ax_r.plot(
                    t_post * 1e3, pack["obs_post"], lw=0.7, color="0.4", label="PE residual"
                )
                ax_r.plot(
                    t_post * 1e3,
                    pack["pred_base"],
                    lw=1.0,
                    label=f"leftover RD a={pack['a_base']:.2e}",
                )
                ax_r.plot(
                    t_post * 1e3,
                    pack["pred_toe"],
                    lw=1.0,
                    label=f"RD+echoes a1={pack['a1_toe']:.2e}",
                )
                ax_r.set_ylabel("PE residual")
                ax_r.legend(loc="upper right", fontsize=8)

            ax_e.plot(t_post * 1e3, pack["resid_base"], lw=0.7, label="resid baseline")
            ax_e.plot(t_post * 1e3, pack["resid_toe"], lw=0.7, label="resid toe")
            for s in steps:
                for ax in (ax_r, ax_e) if args.baseline == "pe" else (axes[0], ax_e):
                    ax.axvline(s.delay_s * 1e3, color="C3", alpha=0.35, ls="--")
            ax_e.set_xlabel("t − t_merger [ms]")
            ax_e.set_ylabel("final residual")
            ax_e.legend(loc="upper right", fontsize=8)
            fig.tight_layout()
            plot_path = str(
                project_root / "outputs" / "benchmarks" / f"{tag}.png"
            )
            Path(plot_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(plot_path, dpi=150)
            print(f"  wrote plot → {plot_path}")
        except ImportError:
            print("  matplotlib not available; skip plot")

    npz_path = project_root / "outputs" / "benchmarks" / f"{tag}_series.npz"
    save_kw = dict(
        t_post=t_post,
        obs_post=pack["obs_post"],
        pred_base=pack["pred_base"],
        pred_toe=pack["pred_toe"],
        resid_base=pack["resid_base"],
        resid_toe=pack["resid_toe"],
        delays=np.array([s.delay_s for s in steps]),
    )
    if pack.get("obs_raw_post") is not None:
        save_kw["obs_raw_post"] = pack["obs_raw_post"]
        save_kw["pe_template_post"] = pack["pe_template_post"]
    np.savez(npz_path, **save_kw)

    prefers = _prefers_label(pack["delta"])
    result = {
        "schema": "invariant_hunt.benchmark.v3",
        "mode": "public_event",
        "baseline_model": args.baseline,
        "event": event.to_dict(),
        "detector": args.detector,
        "data_path": str(seg.path),
        "spacing_mode": args.spacing,
        "n_echoes": args.n_echoes,
        "n_samples_post": int(t_post.size),
        "sample_rate": seg.sample_rate,
        "noise_sigma_premerger": sigma,
        "bandpass_hz": [args.f_low, args.f_high],
        "obs_label": pack["obs_label"],
        "fit_amplitude_baseline": pack["a_base"],
        "fit_amplitude_toe_primary": pack["a0_toe"],
        "fit_amplitude_toe_echoes": pack["a1_toe"],
        "chi2_baseline_no_echo": pack["chi2_baseline"],
        "chi2_toe_positional_echo": pack["chi2_toe"],
        "chi2_red_baseline": pack["chi2_baseline"] / pack["dof_base"],
        "chi2_red_toe": pack["chi2_toe"] / pack["dof_toe"],
        "delta_chi2_base_minus_toe": pack["delta"],
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
        "note": pack["note"],
        "falsify_checkpoint": (
            f"If prefers stays 'baseline' or 'inconclusive' under PE residual + "
            f"geometric spacing for {event.name} after PSD-whitened multi-detector "
            f"analysis, revise echo mapping (κ, spacing, amp priors) before claiming "
            f"support for the ladder."
        ),
    }
    if pack.get("chi2_null") is not None:
        result["chi2_pe_residual_null"] = pack["chi2_null"]
        result["delta_chi2_null_minus_toe"] = pack["delta_null"]
    if pack.get("pe_fit") is not None:
        result["pe_fit"] = pack["pe_fit"].to_dict()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark positional echoes")
    parser.add_argument("--event", type=str, default="",
                        help="Public event name (e.g. GW150914). Empty = synthetic.")
    parser.add_argument("--detector", type=str, default="H1")
    parser.add_argument(
        "--baseline",
        choices=("toy", "pe"),
        default="pe",
        help="GR baseline: toy ringdown or published PE→IMRPhenomD (default: pe)",
    )
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
    parser.add_argument("--lag-min", type=float, default=-0.05)
    parser.add_argument("--lag-max", type=float, default=0.05)
    parser.add_argument("--fit-t-min", type=float, default=-0.15)
    parser.add_argument("--fit-t-max", type=float, default=0.05)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    if args.event:
        result = run_event(args)
        label = f"public event {args.event}/{args.detector} baseline={args.baseline}"
        default_out = (
            f"outputs/benchmarks/{args.event}_{args.detector}_"
            f"{args.baseline}_{args.spacing}.json"
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
    if "chi2_pe_residual_null" in result:
        print(f"  χ² PE residual=0: {result['chi2_pe_residual_null']:.2f}")
    print(
        f"  Δχ² (base-toe)  : {result['delta_chi2_base_minus_toe']:.2f}  "
        f"→ prefers {result['prefers']}"
    )
    if result.get("fit_amplitude_toe_echoes") is not None:
        print(f"  echo scale a1   : {result['fit_amplitude_toe_echoes']:.3e}")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
