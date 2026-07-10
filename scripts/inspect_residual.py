#!/usr/bin/env python3
"""
Inspect PE residual vs positional echo ladder.

Loads an existing *_series.npz from compare_benchmark --baseline pe,
or re-runs the PE fit, then reports per-echo local Δχ², MF SNR, and
echo-window RMS vs control windows.

Usage:
  python scripts/inspect_residual.py
  python scripts/inspect_residual.py --series outputs/benchmarks/GW150914_H1_pe_geometric_series.npz
  python scripts/inspect_residual.py --event GW150914 --detector H1 --plot
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.echo_ladder import build_ladder  # noqa: E402
from src.gw_events import get_event  # noqa: E402
from src.gwosc_data import load_event_segment, noise_sigma_premerger  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.residual_diagnostics import summarize_residual  # noqa: E402


def load_or_compute(args: argparse.Namespace):
    event = get_event(args.event)
    inv = InvariantSet()
    steps = build_ladder(
        event, inv, n_echoes=args.n_echoes, mode=args.spacing, amp0=args.amp0
    )

    series_path = Path(args.series) if args.series else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_{args.detector}_pe_{args.spacing}_series.npz"
    )

    if series_path.exists() and not args.refit:
        z = np.load(series_path)
        t_post = z["t_post"]
        # PE residual is stored as obs_post in pe mode
        residual = z["obs_post"]
        print(f"Loaded series {series_path}")
        # sigma from companion json if present
        jpath = series_path.with_name(
            series_path.name.replace("_series.npz", ".json")
        )
        if jpath.exists():
            meta = json.loads(jpath.read_text(encoding="utf-8"))
            sigma = float(meta["noise_sigma_premerger"])
        else:
            sigma = float(np.std(residual) + 1e-30)
        return t_post, residual, steps, event, sigma, series_path

    print("Re-fitting PE residual…")
    from src.pe_waveform import fit_pe_to_strain, pe_params_for_event

    seg = load_event_segment(
        event,
        detector=args.detector,
        cache_dir=project_root / "data" / "gwosc",
        f_low=args.f_low,
        f_high=args.f_high,
        duration_pre_s=0.25,
        duration_post_s=event.duration_post_s,
    )
    sigma = noise_sigma_premerger(seg)
    params = pe_params_for_event(event.name, pe_dir=project_root / "data" / "pe")
    fit = fit_pe_to_strain(
        seg.t_rel,
        seg.h,
        params,
        sample_rate=seg.sample_rate,
        sigma=sigma,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    post = seg.t_rel >= 0.0
    return seg.t_rel[post], fit.residual[post], steps, event, sigma, series_path


def main() -> None:
    p = argparse.ArgumentParser(description="Inspect PE residual vs echo ladder")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detector", default="H1")
    p.add_argument("--spacing", choices=("geometric", "phase_unit"), default="geometric")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--series", type=str, default="")
    p.add_argument("--refit", action="store_true")
    p.add_argument("--f-low", type=float, default=50.0)
    p.add_argument("--f-high", type=float, default=300.0)
    p.add_argument("--half-window-ms", type=float, default=2.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    t, residual, steps, event, sigma, series_path = load_or_compute(args)
    half = args.half_window_ms * 1e-3
    summary = summarize_residual(
        residual, t, event, steps, sigma, half_window_s=half
    )

    print("=" * 60)
    print(f"Residual diagnostics — {event.name} / {args.detector}")
    print(f"  n={summary['n_samples']}  σ={sigma:.3e}")
    print(f"  a0 (leftover RD) = {summary['a0_leftover_ringdown']:.3e}")
    print(f"  a1 (echo scale)  = {summary['a1_echo_scale']:.3e}")
    print(f"  χ² null / base / toe = "
          f"{summary['chi2_null']:.2f} / {summary['chi2_baseline']:.2f} / "
          f"{summary['chi2_toe']:.2f}")
    print(f"  Δχ² global (base−toe) = {summary['delta_chi2_global']:.4f}")
    print(f"  max |MF SNR|          = {summary['max_abs_mf_snr']:.3f}")
    print(
        f"  Σ local Δχ² (a1>0 only) = {summary['sum_local_positive_a1_delta_chi2']:.4f}"
    )
    print("-" * 60)
    print(f"{'n':>3}  {'δt ms':>8}  {'Δχ²_loc':>9}  {'a1_loc':>12}  "
          f"{'MF SNR':>8}  {'RMS_echo':>10}  {'RMS_ctrl':>10}")
    for pe, sn, re, rc in zip(
        summary["per_echo"],
        summary["mf_snr"],
        summary["rms_at_echo_windows"],
        summary["rms_at_control_windows"],
    ):
        print(
            f"{int(pe['n']):3d}  {pe['delay_s']*1e3:8.3f}  "
            f"{pe['delta_chi2_local']:9.4f}  {pe['a1_local']:12.3e}  "
            f"{sn['mf_snr']:8.3f}  {re['window_rms']:10.3e}  "
            f"{rc['window_rms']:10.3e}"
        )
    print("-" * 60)
    print(f"Interpretation: {summary['interpretation']}")
    print("=" * 60)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_{args.detector}_residual_diagnostics.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    # make JSON-safe
    payload = {
        "event": event.name,
        "detector": args.detector,
        "series": str(series_path),
        "half_window_s": half,
        **{k: v for k, v in summary.items()},
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt
            from src.residual_diagnostics import build_unit_echo_templates

            templates = build_unit_echo_templates(t, event, steps)
            train = np.sum(templates, axis=0)
            a1 = summary["a1_echo_scale"]
            a0 = summary["a0_leftover_ringdown"]
            from src.echo_ladder import baseline_ringdown

            pred = a0 * baseline_ringdown(t, event) + a1 * train

            fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
            axes[0].plot(t * 1e3, residual, lw=0.7, color="0.4", label="PE residual")
            axes[0].plot(t * 1e3, pred, lw=1.0, label="fit RD+echoes")
            for s in steps:
                axes[0].axvline(s.delay_s * 1e3, color="C3", alpha=0.4, ls="--")
            axes[0].legend(fontsize=8)
            axes[0].set_ylabel("strain")
            axes[0].set_title(f"{event.name} residual diagnostics")

            # local Δχ² bars
            ns = [d["n"] for d in summary["per_echo"]]
            dc = [d["delta_chi2_local"] for d in summary["per_echo"]]
            axes[1].bar([s.delay_s * 1e3 for s in steps], dc, width=1.0, color="C3", alpha=0.7)
            axes[1].axhline(0, color="k", lw=0.5)
            axes[1].set_xlabel("t − t_merger [ms]")
            axes[1].set_ylabel("local Δχ²")
            fig.tight_layout()
            plot_path = out.with_suffix(".png")
            fig.savefig(plot_path, dpi=150)
            print(f"Wrote {plot_path}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
