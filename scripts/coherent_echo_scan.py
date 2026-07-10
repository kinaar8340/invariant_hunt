#!/usr/bin/env python3
"""
Coherent complex-amplitude echo train + delay-scale scan on PE residual.

Keeps W_g, κ, braiding locks fixed. Refines only the template mapping:
  - one complex amplitude (a_cos, a_sin) for the whole ladder
  - optional s-scan: δt_n → s · δt_n(geometric) with LEE threshold

Usage:
  python scripts/coherent_echo_scan.py --event GW150914 --plot
  python scripts/coherent_echo_scan.py --scan-min 0.8 --scan-max 1.2 --n-scales 21
  python scripts/coherent_echo_scan.py --no-scan   # coherent at s=1 only
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

from src.coherent_echo import (  # noqa: E402
    coherent_matched_filter_snr,
    delay_scale_scan,
    fit_coherent_echoes,
)
from src.gw_events import get_event  # noqa: E402
from src.gwosc_data import load_event_segment, noise_sigma_premerger  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.pe_waveform import fit_pe_to_strain, pe_params_for_event  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Coherent echo + delay scale scan")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detector", default="H1")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--spacing", choices=("geometric", "phase_unit"), default="geometric")
    p.add_argument("--no-scan", action="store_true", help="Only evaluate s=1")
    p.add_argument("--scan-min", type=float, default=0.80)
    p.add_argument("--scan-max", type=float, default=1.20)
    p.add_argument("--n-scales", type=int, default=21)
    p.add_argument("--gate-a-thr", type=float, default=4.0)
    p.add_argument("--f-low", type=float, default=50.0)
    p.add_argument("--f-high", type=float, default=300.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    event = get_event(args.event)
    inv = InvariantSet()

    print(f"Loading {event.name}/{args.detector} and PE residual…")
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
    pe = fit_pe_to_strain(
        seg.t_rel,
        seg.h,
        params,
        sample_rate=seg.sample_rate,
        sigma=sigma,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    post = seg.t_rel >= 0.0
    t = seg.t_rel[post]
    residual = pe.residual[post]

    # Nominal coherent at s=1
    nom = fit_coherent_echoes(
        residual,
        t,
        event,
        inv,
        sigma=sigma,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
        delay_scale=1.0,
    )
    mf = coherent_matched_filter_snr(residual, nom.e_cos, nom.e_sin, sigma)

    print("=" * 60)
    print(f"Coherent echo train @ s=1 (geometric) — {event.name}/{args.detector}")
    print(f"  a0={nom.a0:.3e}  |A|={nom.amp:.3e}  φ={nom.phase:.3f} rad")
    print(f"  a_cos={nom.a_cos:.3e}  a_sin={nom.a_sin:.3e}")
    print(f"  χ² base/toe = {nom.chi2_base:.2f} / {nom.chi2_toe:.2f}")
    print(f"  Δχ² = {nom.delta_chi2:.4f}   coherent MF SNR = {mf:.3f}")
    print(
        f"  Gate A (nominal): "
        f"{'PASS' if (nom.delta_chi2 >= args.gate_a_thr and nom.amp > 0 and mf >= 2) else 'FAIL'}"
        f"  [need Δχ²≥{args.gate_a_thr}, |A|>0, MF SNR≥2]"
    )

    scan_payload = None
    best = nom
    if not args.no_scan:
        scan = delay_scale_scan(
            residual,
            t,
            event,
            inv,
            sigma=sigma,
            n_echoes=args.n_echoes,
            mode=args.spacing,
            amp0=args.amp0,
            scan_min=args.scan_min,
            scan_max=args.scan_max,
            n_scales=args.n_scales,
            gate_a_threshold=args.gate_a_thr,
        )
        best = scan.best
        print("-" * 60)
        print(
            f"Delay-scale scan s ∈ [{args.scan_min}, {args.scan_max}]  "
            f"n_trials={scan.n_trials}"
        )
        print(f"  nominal Δχ² (s=1)     = {scan.nominal_delta_chi2:.4f}")
        print(
            f"  best    Δχ² (s={best.delay_scale:.3f}) = {best.delta_chi2:.4f}  "
            f"|A|={best.amp:.3e}"
        )
        print(f"  LEE thr raw / corr    = {scan.lee_threshold_raw:.2f} / "
              f"{scan.lee_threshold_corrected:.2f}")
        print(f"  Gate A best raw       = "
              f"{'PASS' if scan.passes_gate_a_best_raw else 'FAIL'}")
        print(f"  Gate A best + LEE     = "
              f"{'PASS' if scan.passes_gate_a_best_lee else 'FAIL'}")
        scan_payload = scan.to_dict()
        # recompute MF at best scale
        best_fit = fit_coherent_echoes(
            residual, t, event, inv, sigma=sigma,
            n_echoes=args.n_echoes, mode=args.spacing, amp0=args.amp0,
            delay_scale=best.delay_scale,
        )
        mf_best = coherent_matched_filter_snr(
            residual, best_fit.e_cos, best_fit.e_sin, sigma
        )
        print(f"  coherent MF SNR @ best s = {mf_best:.3f}")
    else:
        mf_best = mf
        best_fit = nom

    print("=" * 60)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_{args.detector}_coherent_scan.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.coherent_scan.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": event.name,
        "detector": args.detector,
        "echo_model": "coherent_complex",
        "invariants_fixed": {"wg": inv.wg, "kappa": inv.kappa},
        "nominal": {**nom.to_dict(), "coherent_mf_snr": mf},
        "scan": scan_payload,
        "best": {**best_fit.to_dict(), "coherent_mf_snr": mf_best},
        "note": (
            "Core locks W_g and κ held fixed. Template mapping uses one complex "
            "amplitude for the train; optional delay scale s multiplies geometric "
            "δt_n. LEE threshold is approximate Bonferroni for discrete grid."
        ),
    }
    # strip large arrays from steps-only dicts already ok
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    # series for plots
    npz_path = out.with_name(out.stem + "_series.npz")
    np.savez(
        npz_path,
        t=t,
        residual=residual,
        pred_base=best_fit.pred_base,
        pred_toe=best_fit.pred_toe,
        e_cos=best_fit.e_cos,
        e_sin=best_fit.e_sin,
        delays=np.array([s.delay_s for s in best_fit.steps]),
    )

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig = plt.figure(figsize=(10, 7))
            if scan_payload is not None:
                gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.0, 1.0])
                ax0 = fig.add_subplot(gs[0])
                ax1 = fig.add_subplot(gs[1])
                ax2 = fig.add_subplot(gs[2])
            else:
                gs = fig.add_gridspec(2, 1)
                ax0 = fig.add_subplot(gs[0])
                ax1 = fig.add_subplot(gs[1])
                ax2 = None

            ax0.plot(t * 1e3, residual, lw=0.7, color="0.45", label="PE residual")
            ax0.plot(t * 1e3, best_fit.pred_toe, lw=1.0, label="coherent fit")
            for s in best_fit.steps:
                ax0.axvline(s.delay_s * 1e3, color="C3", alpha=0.35, ls="--")
            ax0.set_ylabel("strain")
            ax0.legend(fontsize=8)
            ax0.set_title(
                f"{event.name} coherent echoes  s={best_fit.delay_scale:.3f}  "
                f"Δχ²={best_fit.delta_chi2:.2f}"
            )

            ax1.plot(t * 1e3, residual - best_fit.pred_base, lw=0.7, label="resid−RD")
            ax1.plot(
                t * 1e3,
                best_fit.pred_toe - best_fit.pred_base,
                lw=1.0,
                label="echo model",
            )
            for s in best_fit.steps:
                ax1.axvline(s.delay_s * 1e3, color="C3", alpha=0.35, ls="--")
            ax1.set_xlabel("t − t_merger [ms]" if ax2 is None else "")
            ax1.set_ylabel("echo sector")
            ax1.legend(fontsize=8)

            if ax2 is not None and scan_payload is not None:
                ax2.plot(scan_payload["scales"], scan_payload["delta_chi2"], "o-")
                ax2.axvline(1.0, color="k", ls=":", lw=0.8, label="s=1")
                ax2.axhline(
                    scan_payload["lee_threshold_raw"], color="C1", ls="--",
                    label=f"raw thr={scan_payload['lee_threshold_raw']}",
                )
                ax2.axhline(
                    scan_payload["lee_threshold_corrected"], color="C3", ls="--",
                    label=f"LEE thr={scan_payload['lee_threshold_corrected']:.1f}",
                )
                ax2.set_xlabel("delay scale s")
                ax2.set_ylabel("Δχ²")
                ax2.legend(fontsize=8)

            fig.tight_layout()
            plot_path = out.with_suffix(".png")
            fig.savefig(plot_path, dpi=150)
            print(f"Wrote {plot_path}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
