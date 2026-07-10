#!/usr/bin/env python3
"""
Whitened H1+L1 network PE residual + coherent echo ladder.

Credibility upgrade over single-detector band-limited white noise:
  1. Welch PSD from pre-merger per detector
  2. Frequency-domain whitening (band-limited)
  3. PE IMR fit in whitened domain (per detector lag + A+,Ax)
  4. Network coherent echo fit: shared (a_c, a_s), per-det a0
  5. Optional delay-scale scan with LEE

Usage:
  python scripts/network_whiten_scan.py --event GW150914 --plot
  python scripts/network_whiten_scan.py --detectors H1,L1 --no-scan
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

from src.invariants import InvariantSet  # noqa: E402
from src.network_likelihood import (  # noqa: E402
    fit_network_coherent,
    network_delay_scan,
    prepare_network,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Whitened multi-detector echo scan")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--spacing", choices=("geometric", "phase_unit"), default="geometric")
    p.add_argument("--no-scan", action="store_true")
    p.add_argument("--scan-min", type=float, default=0.80)
    p.add_argument("--scan-max", type=float, default=1.20)
    p.add_argument("--n-scales", type=int, default=21)
    p.add_argument("--gate-a-thr", type=float, default=4.0)
    p.add_argument("--f-low", type=float, default=50.0)
    p.add_argument("--f-high", type=float, default=300.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()

    print(f"Preparing whitened network: {args.event} / {detectors}")
    event, params, dets = prepare_network(
        args.event,
        detectors,
        project_root=project_root,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    print(
        f"  PE medians: m1={params.mass1:.2f} m2={params.mass2:.2f}  "
        f"d_L={params.distance_mpc:.0f} Mpc"
    )
    for d in dets:
        print(
            f"  {d.detector}: PE lag={d.pe_lag_s*1e3:.2f} ms  "
            f"SNR≈{d.pe_snr_proxy:.1f}  χ²_PE={d.pe_chi2:.1f}  "
            f"resid_std={np.std(d.residual_w):.3f}"
        )

    nom = fit_network_coherent(
        dets,
        event,
        inv,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
        delay_scale=1.0,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    print("=" * 60)
    print(f"Whitened network coherent echoes @ s=1 — {event.name} {detectors}")
    print(f"  a0 per det: { {k: f'{v:.3e}' for k,v in nom.a0_per_det.items()} }")
    print(f"  |A|={nom.amp:.3e}  φ={nom.phase:.3f}  a_c={nom.a_cos:.3e}  a_s={nom.a_sin:.3e}")
    print(f"  χ² base/toe = {nom.chi2_base:.2f} / {nom.chi2_toe:.2f}")
    print(f"  Δχ² = {nom.delta_chi2:.4f}   network MF SNR = {nom.mf_snr:.3f}")
    gate_nom = nom.delta_chi2 >= args.gate_a_thr and nom.mf_snr >= 2.0
    print(
        f"  Gate A (nominal, whitened network): "
        f"{'PASS' if gate_nom else 'FAIL'}  "
        f"[Δχ²≥{args.gate_a_thr}, MF SNR≥2]"
    )

    scan_payload = None
    best = nom
    if not args.no_scan:
        scan = network_delay_scan(
            dets,
            event,
            inv,
            n_echoes=args.n_echoes,
            mode=args.spacing,
            amp0=args.amp0,
            scan_min=args.scan_min,
            scan_max=args.scan_max,
            n_scales=args.n_scales,
            gate_a_threshold=args.gate_a_thr,
            f_low=args.f_low,
            f_high=args.f_high,
        )
        scan_payload = scan
        best_d = scan["best"]
        print("-" * 60)
        print(
            f"Delay-scale scan s ∈ [{args.scan_min},{args.scan_max}]  "
            f"n_trials={scan['n_trials']}"
        )
        print(f"  nominal Δχ² (s=1) = {scan['nominal']['delta_chi2']:.4f}")
        print(
            f"  best Δχ² (s={best_d['delay_scale']:.3f}) = {best_d['delta_chi2']:.4f}  "
            f"MF SNR={best_d['mf_snr']:.3f}"
        )
        print(
            f"  LEE thr raw/corr = {scan['lee_threshold_raw']:.2f} / "
            f"{scan['lee_threshold_corrected']:.2f}"
        )
        print(
            f"  Gate A best raw  = {'PASS' if scan['passes_gate_a_best_raw'] else 'FAIL'}"
        )
        print(
            f"  Gate A best+LEE  = {'PASS' if scan['passes_gate_a_best_lee'] else 'FAIL'}"
        )
        best = fit_network_coherent(
            dets,
            event,
            inv,
            n_echoes=args.n_echoes,
            mode=args.spacing,
            amp0=args.amp0,
            delay_scale=best_d["delay_scale"],
            f_low=args.f_low,
            f_high=args.f_high,
        )
    print("=" * 60)

    tag = f"{event.name}_{'-'.join(detectors)}_whitened_network"
    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / f"{tag}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.whitened_network.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": event.to_dict(),
        "detectors": detectors,
        "f_band_hz": [args.f_low, args.f_high],
        "pe_params": params.to_dict(),
        "detector_details": [d.to_dict() for d in dets],
        "echo_model": "coherent_complex_network",
        "invariants_fixed": {"wg": inv.wg, "kappa": inv.kappa},
        "nominal": nom.to_dict(),
        "best": best.to_dict(),
        "scan": scan_payload,
        "gate_a_nominal": gate_nom,
        "note": (
            "Whitened multi-detector analysis: Welch PSD (pre-merger), "
            "FD whitening, per-detector PE residual, network coherent "
            "(a_c,a_s) echo amplitude. Noise model is whitened-unit-variance "
            "white noise in-band — not a full bayesian PE with calibration "
            "marginalization."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    # save series
    t = dets[0].t_rel
    post = t >= 0.0
    npz = {
        "t_post": t[post],
    }
    for d in dets:
        npz[f"residual_w_{d.detector}"] = d.residual_w[post]
        npz[f"strain_w_{d.detector}"] = d.strain_w[post]
        npz[f"pe_w_{d.detector}"] = d.pe_template_w[post]
    np.savez(out.with_name(out.stem + "_series.npz"), **npz)

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            n_det = len(dets)
            nrows = n_det + (0 if args.no_scan else 1)
            fig, axes = plt.subplots(nrows, 1, figsize=(10, 2.2 * nrows), sharex=False)
            if nrows == 1:
                axes = [axes]
            for i, d in enumerate(dets):
                tp = d.t_rel[post] * 1e3
                axes[i].plot(tp, d.residual_w[post], lw=0.7, color="0.4", label="PE resid (w)")
                for s in best.steps:
                    axes[i].axvline(s.delay_s * 1e3, color="C3", alpha=0.3, ls="--")
                axes[i].set_ylabel(f"{d.detector} w")
                axes[i].legend(fontsize=8, loc="upper right")
                if i == 0:
                    axes[i].set_title(
                        f"{event.name} whitened network  Δχ²={best.delta_chi2:.2f}  "
                        f"SNR={best.mf_snr:.2f}  s={best.delay_scale:.3f}"
                    )
            if not args.no_scan and scan_payload is not None:
                ax = axes[-1]
                ax.plot(scan_payload["scales"], scan_payload["delta_chi2"], "o-")
                ax.axvline(1.0, color="k", ls=":", lw=0.8)
                ax.axhline(scan_payload["lee_threshold_raw"], color="C1", ls="--",
                           label="raw thr")
                ax.axhline(scan_payload["lee_threshold_corrected"], color="C3", ls="--",
                           label="LEE thr")
                ax.set_xlabel("delay scale s")
                ax.set_ylabel("Δχ² net")
                ax.legend(fontsize=8)
            else:
                axes[-1].set_xlabel("t − t_merger [ms]")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
