#!/usr/bin/env python3
"""
Injection recovery for pre-merger topological phase α (Gate B-P).

Injects coherent α·τ into whitened PE residuals (or Gaussian noise) and
measures recovery of α_hat, Δχ², and Gate P (incl. H1/L1 sign consistency).

Also runs residual–τ correlation and time-cut robustness diagnostics.

Usage:
  python scripts/premerger_injection_recovery.py --event GW150914 --plot
  python scripts/premerger_injection_recovery.py --into noise --plot
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
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    prepare_premerger_network,
    premerger_injection_recovery,
    residual_tau_correlation,
    time_cut_robustness,
)
from src.premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Pre-merger α injection recovery")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--into", choices=("residual", "noise", "both"), default="both")
    p.add_argument("--duration-pre", type=float, default=4.0)
    p.add_argument("--t-end", type=float, default=GATE_P_T_END)
    p.add_argument("--f-low", type=float, default=20.0)
    p.add_argument("--f-high", type=float, default=100.0)
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument(
        "--alphas",
        default="0,2e-5,5e-5,7e-5,1e-4,2e-4,5e-4",
        help="Comma-separated α injection values",
    )
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    alphas = [float(x) for x in args.alphas.split(",") if x.strip()]
    inv = InvariantSet()

    print("=" * 70)
    print(f"PRE-MERGER α INJECTION RECOVERY — {args.event}")
    print(f"  Gate P: Δχ²≥{args.gate_dchi2}, |α|>2σ, H1/L1 sign consistent")
    print("=" * 70)

    event, dets = prepare_premerger_network(
        args.event,
        detectors,
        project_root=project_root,
        duration_pre_s=args.duration_pre,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    for d in dets:
        print(f"  {d.detector}: PE SNR≈{d.pe_snr_proxy:.1f}")

    # Baseline real-data fit
    real = fit_premerger_phase_network(
        dets,
        event,
        t_end=args.t_end,
        f_low=args.f_low,
        f_high=args.f_high,
        gate_dchi2=args.gate_dchi2,
        inv=inv,
    )
    print(
        f"\nReal residual: α={real.alpha_hat:.3e}±{real.alpha_sigma:.3e}  "
        f"Δχ²={real.delta_chi2:.2f}  Gate P={'PASS' if real.gate_p_pass else 'fail'}"
    )

    # Systematics diagnostics
    corr = residual_tau_correlation(dets, inv, t_end=args.t_end)
    print("\nResidual–τ correlation (systematics):")
    for det, v in corr["detectors"].items():
        print(
            f"  {det}: corr={v['corr_r_tau']:+.4f}  "
            f"power_frac={v['power_frac_along_tau']:.4f}"
        )

    cuts = time_cut_robustness(
        dets,
        event,
        f_low=args.f_low,
        f_high=args.f_high,
        gate_dchi2=args.gate_dchi2,
        inv=inv,
    )
    print("\nTime-cut robustness:")
    print(f"  {'t_end':>8}  {'α_hat':>12}  {'Δχ²':>8}  pass")
    for row in cuts["t_ends"]:
        print(
            f"  {row['t_end']:8.3f}  {row['alpha_hat']:12.3e}  "
            f"{row['delta_chi2']:8.2f}  {'Y' if row['gate_p_pass'] else 'n'}"
        )

    into_list = ["residual", "noise"] if args.into == "both" else [args.into]
    inj_all = {}
    for into in into_list:
        print(f"\n--- injection into {into} ---")
        print(f"  {'α_inj':>10}  {'α_hat':>12}  {'frac':>8}  {'Δχ²':>8}  pass")
        res = premerger_injection_recovery(
            dets,
            event,
            alpha_injs=alphas,
            t_end=args.t_end,
            f_low=args.f_low,
            f_high=args.f_high,
            gate_dchi2=args.gate_dchi2,
            inv=inv,
            into=into,
        )
        for row in res["rows"]:
            frac = row["recovered_frac"]
            frac_s = f"{frac:8.3f}" if frac == frac else f"{'nan':>8}"
            print(
                f"  {row['alpha_inj']:10.2e}  {row['alpha_hat']:12.3e}  {frac_s}  "
                f"{row['delta_chi2']:8.2f}  {'YES' if row['gate_p_pass'] else 'no'}"
            )
        print(f"  Gate P thr α_inj ≈ {res['detection_threshold_alpha']}")
        if res["background"]:
            bg = res["background"]
            print(
                f"  Background α_inj=0: Δχ²={bg['delta_chi2']:.2f}  "
                f"α_hat={bg['alpha_hat']:.3e}  "
                f"pass={bg['gate_p_pass']}"
            )
        inj_all[into] = res

    # Calibrate real α against recovery
    print("\n" + "=" * 70)
    print("CALIBRATION vs REAL GW150914-scale result")
    real_a = real.alpha_hat
    if "residual" in inj_all:
        # find nearest injection
        rows = inj_all["residual"]["rows"]
        nearest = min(rows, key=lambda r: abs(r["alpha_inj"] - abs(real_a)))
        thr = inj_all["residual"]["detection_threshold_alpha"]
        print(f"  Real |α| ≈ {abs(real_a):.3e}")
        print(
            f"  Nearest inj α={nearest['alpha_inj']:.2e}: "
            f"recovered {nearest['alpha_hat']:.3e} (frac={nearest['recovered_frac']})  "
            f"Δχ²={nearest['delta_chi2']:.1f}"
        )
        if thr is not None:
            print(f"  Injection thr for Gate P: α ≳ {thr:.2e}")
            if abs(real_a) >= thr and real.gate_p_pass:
                print(
                    "  Real |α| sits at/above recovery thr — interesting but still "
                    "needs multi-event + systematics before claim."
                )
            elif abs(real_a) < thr:
                print("  Real |α| below injection thr for reliable Gate P recovery.")
        noise_bg = (inj_all.get("noise") or {}).get("background")
        if noise_bg:
            print(
                f"  Pure-noise false Gate P rate (this seed, α=0): "
                f"pass={noise_bg['gate_p_pass']} Δχ²={noise_bg['delta_chi2']:.2f}"
            )
    print("=" * 70)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{args.event}_premerger_injection.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_injection.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": args.event,
        "real_fit": real.to_dict(),
        "residual_tau_correlation": corr,
        "time_cut_robustness": cuts,
        "injections": {
            k: {
                "detection_threshold_alpha": v["detection_threshold_alpha"],
                "background": v["background"],
                "rows": v["rows"],
            }
            for k, v in inj_all.items()
        },
        "gate_p": {
            "delta_chi2": args.gate_dchi2,
            "t_end": args.t_end,
            "band_hz": [args.f_low, args.f_high],
        },
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            if "residual" in inj_all:
                rr = inj_all["residual"]["rows"]
                axes[0].plot(
                    [r["alpha_inj"] for r in rr],
                    [r["alpha_hat"] for r in rr],
                    "o-",
                    label="into residual",
                )
            if "noise" in inj_all:
                rn = inj_all["noise"]["rows"]
                axes[0].plot(
                    [r["alpha_inj"] for r in rn],
                    [r["alpha_hat"] for r in rn],
                    "s--",
                    label="into noise",
                )
            axes[0].plot(
                [0, max(alphas)],
                [0, max(alphas)],
                "k:",
                lw=0.8,
                label="perfect",
            )
            axes[0].axhline(real.alpha_hat, color="C3", ls="--", label="real α")
            axes[0].set_xlabel("α_inj")
            axes[0].set_ylabel("α_hat")
            axes[0].legend(fontsize=8)
            axes[0].set_title("α recovery")

            if "residual" in inj_all:
                axes[1].plot(
                    [r["alpha_inj"] for r in inj_all["residual"]["rows"]],
                    [r["delta_chi2"] for r in inj_all["residual"]["rows"]],
                    "o-",
                    label="residual",
                )
            if "noise" in inj_all:
                axes[1].plot(
                    [r["alpha_inj"] for r in inj_all["noise"]["rows"]],
                    [r["delta_chi2"] for r in inj_all["noise"]["rows"]],
                    "s--",
                    label="noise",
                )
            axes[1].axhline(args.gate_dchi2, color="k", ls="--", label="Gate P Δχ²")
            axes[1].axhline(
                real.delta_chi2, color="C3", ls=":", label="real Δχ²"
            )
            axes[1].set_xlabel("α_inj")
            axes[1].set_ylabel("Δχ²")
            axes[1].legend(fontsize=8)
            axes[1].set_title("Detection statistic")
            fig.suptitle(f"{args.event} pre-merger α injection (Gate B-P)")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
