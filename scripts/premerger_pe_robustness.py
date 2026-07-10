#!/usr/bin/env python3
"""
PE approximant / subtraction robustness for pre-merger Gate P.

Re-runs the whitened network phase fit under:
  1. Multiple IMR approximants (IMRPhenomD, SEOBNRv4_opt, IMRPhenomXAS, …)
  2. Small PE parameter jitter (± mass, distance)

A physical α should stay Gate-P-positive with stable sign across robust PE
subtractions. Collapse under approximant change → PE residual systematics.

Usage:
  python scripts/premerger_pe_robustness.py --event GW150914 --plot
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
from src.pe_waveform import PEParams, pe_params_for_event  # noqa: E402
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    prepare_premerger_network,
)
from src.premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END  # noqa: E402

DEFAULT_APPROXIMANTS = [
    "IMRPhenomD",
    "SEOBNRv4_opt",
    "IMRPhenomXAS",
    "IMRPhenomXP",
]


def _jitter_params(base: PEParams, scale_m: float, scale_d: float) -> PEParams:
    return PEParams(
        event=base.event,
        mass1=base.mass1 * scale_m,
        mass2=base.mass2 * scale_m,
        distance_mpc=base.distance_mpc * scale_d,
        spin1z=base.spin1z,
        spin2z=base.spin2z,
        ra=base.ra,
        dec=base.dec,
        costheta_jn=base.costheta_jn,
        approximant=base.approximant,
        posterior_dataset=base.posterior_dataset,
        n_samples=base.n_samples,
        source=base.source + f"|jitter_m={scale_m}_d={scale_d}",
    )


def main() -> None:
    p = argparse.ArgumentParser(description="PE approximant robustness for Gate P")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument(
        "--approximants",
        default=",".join(DEFAULT_APPROXIMANTS),
        help="Comma-separated TD approximants",
    )
    p.add_argument("--duration-pre", type=float, default=4.0)
    p.add_argument("--t-end", type=float, default=GATE_P_T_END)
    p.add_argument("--f-low", type=float, default=20.0)
    p.add_argument("--f-high", type=float, default=100.0)
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument("--skip-jitter", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    approximants = [a.strip() for a in args.approximants.split(",") if a.strip()]
    inv = InvariantSet()
    base_params = pe_params_for_event(
        args.event, pe_dir=project_root / "data" / "pe"
    )

    print("=" * 70)
    print(f"PE ROBUSTNESS — pre-merger Gate P — {args.event}")
    print(f"  approximants: {approximants}")
    print(f"  Gate P: Δχ²≥{args.gate_dchi2}, |α|>2σ, H1/L1 sign consistent")
    print("=" * 70)

    approx_rows = []
    for approx in approximants:
        print(f"\n--- approximant: {approx} ---")
        try:
            event, dets = prepare_premerger_network(
                args.event,
                detectors,
                project_root=project_root,
                duration_pre_s=args.duration_pre,
                f_low=args.f_low,
                f_high=args.f_high,
                approximant=approx,
                params=base_params,
            )
            for d in dets:
                print(f"  {d.detector}: PE SNR≈{d.pe_snr_proxy:.1f}")
            fit = fit_premerger_phase_network(
                dets,
                event,
                t_end=args.t_end,
                f_low=args.f_low,
                f_high=args.f_high,
                gate_dchi2=args.gate_dchi2,
                inv=inv,
            )
            print(
                f"  NETWORK α={fit.alpha_hat:.3e}±{fit.alpha_sigma:.3e}  "
                f"Δχ²={fit.delta_chi2:.2f}  Gate P={'PASS' if fit.gate_p_pass else 'fail'}"
            )
            for n in fit.notes:
                if "sign" in n.lower() or n.startswith("H1") or n.startswith("L1"):
                    print(f"    · {n}")
            approx_rows.append(
                {
                    "approximant": approx,
                    "alpha_hat": fit.alpha_hat,
                    "alpha_sigma": fit.alpha_sigma,
                    "delta_chi2": fit.delta_chi2,
                    "gate_p_pass": fit.gate_p_pass,
                    "pe_snr": {
                        d.detector: d.pe_snr_proxy for d in dets
                    },
                    "error": None,
                }
            )
        except Exception as exc:
            print(f"  FAILED: {exc}")
            approx_rows.append(
                {
                    "approximant": approx,
                    "error": str(exc),
                    "gate_p_pass": False,
                }
            )

    # PE parameter jitter with default IMRPhenomD
    jitter_rows = []
    if not args.skip_jitter:
        print("\n--- PE parameter jitter (IMRPhenomD) ---")
        jitters = [
            ("nominal", 1.0, 1.0),
            ("m+3%", 1.03, 1.0),
            ("m-3%", 0.97, 1.0),
            ("d+15%", 1.0, 1.15),
            ("d-15%", 1.0, 0.85),
            ("m+3%_d+15%", 1.03, 1.15),
        ]
        for label, sm, sd in jitters:
            try:
                jp = _jitter_params(base_params, sm, sd)
                event, dets = prepare_premerger_network(
                    args.event,
                    detectors,
                    project_root=project_root,
                    duration_pre_s=args.duration_pre,
                    f_low=args.f_low,
                    f_high=args.f_high,
                    approximant="IMRPhenomD",
                    params=jp,
                )
                fit = fit_premerger_phase_network(
                    dets,
                    event,
                    t_end=args.t_end,
                    f_low=args.f_low,
                    f_high=args.f_high,
                    gate_dchi2=args.gate_dchi2,
                    inv=inv,
                )
                print(
                    f"  {label:<14} α={fit.alpha_hat:.3e}  Δχ²={fit.delta_chi2:7.2f}  "
                    f"{'PASS' if fit.gate_p_pass else 'fail'}"
                )
                jitter_rows.append(
                    {
                        "label": label,
                        "scale_mass": sm,
                        "scale_distance": sd,
                        "alpha_hat": fit.alpha_hat,
                        "delta_chi2": fit.delta_chi2,
                        "gate_p_pass": fit.gate_p_pass,
                        "error": None,
                    }
                )
            except Exception as exc:
                print(f"  {label:<14} FAILED: {exc}")
                jitter_rows.append(
                    {"label": label, "error": str(exc), "gate_p_pass": False}
                )

    # Summary verdict
    ok_approx = [r for r in approx_rows if r.get("error") is None]
    n_pass = sum(1 for r in ok_approx if r.get("gate_p_pass"))
    signs = [
        np.sign(r["alpha_hat"])
        for r in ok_approx
        if r.get("gate_p_pass") and abs(r.get("alpha_hat", 0)) > 0
    ]
    sign_stable = len(signs) < 2 or (max(signs) * min(signs) > 0)
    alphas = [r["alpha_hat"] for r in ok_approx if r.get("gate_p_pass")]
    alpha_spread = (
        float(np.std(alphas) / (np.mean(np.abs(alphas)) + 1e-30))
        if len(alphas) >= 2
        else float("nan")
    )

    ok_jit = [r for r in jitter_rows if r.get("error") is None]
    n_jit_pass = sum(1 for r in ok_jit if r.get("gate_p_pass"))

    robust = (
        n_pass >= max(2, len(ok_approx) // 2 + 1)
        and sign_stable
        and (args.skip_jitter or n_jit_pass >= max(2, len(ok_jit) // 2 + 1))
    )

    print("\n" + "=" * 70)
    print("ROBUSTNESS SUMMARY")
    print(f"  Approximants Gate P pass: {n_pass}/{len(ok_approx)}")
    print(f"  Sign stable among passes: {sign_stable}")
    if alphas:
        print(
            f"  α among passes: mean={np.mean(alphas):.3e}  "
            f"std/|mean|={alpha_spread:.2f}"
        )
    if not args.skip_jitter:
        print(f"  PE jitter Gate P pass: {n_jit_pass}/{len(ok_jit)}")
    print(
        f"  Overall PE-robust?: {'YES (provisional)' if robust else 'NO / weak'}"
    )
    print(
        "  (Requires majority of approximants pass Gate P with common sign; "
        "not a multi-event claim.)"
    )
    print("=" * 70)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{args.event}_premerger_pe_robustness.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_pe_robustness.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": args.event,
        "approximants": approx_rows,
        "pe_jitter": jitter_rows,
        "n_approx_pass": n_pass,
        "n_approx_total": len(ok_approx),
        "sign_stable": bool(sign_stable),
        "alpha_rel_spread": alpha_spread,
        "n_jitter_pass": n_jit_pass,
        "pe_robust": bool(robust),
        "gate_p": {
            "delta_chi2": args.gate_dchi2,
            "t_end": args.t_end,
            "band_hz": [args.f_low, args.f_high],
        },
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot and ok_approx:
        try:
            import matplotlib.pyplot as plt

            labels = [r["approximant"] for r in ok_approx]
            dchi = [r["delta_chi2"] for r in ok_approx]
            al = [r["alpha_hat"] for r in ok_approx]
            colors = ["C2" if r["gate_p_pass"] else "C3" for r in ok_approx]
            x = np.arange(len(labels))

            fig, axes = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True)
            axes[0].bar(x, dchi, color=colors)
            axes[0].axhline(args.gate_dchi2, color="k", ls="--")
            axes[0].set_ylabel("Δχ²")
            axes[0].set_title(f"{args.event} Gate P vs PE approximant")
            axes[1].bar(x, al, color=colors)
            axes[1].axhline(0, color="k", lw=0.5)
            axes[1].set_ylabel("α_hat")
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(labels, rotation=20, ha="right")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
