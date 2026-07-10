#!/usr/bin/env python3
"""
Expanded multi-event Gate P + PE posterior draws (not form tweaks).

1. Run sign-consistent network Gate P on the expanded BBH set
2. For GW150914 (and optional events), re-fit α under random PE posterior draws

Usage:
  python scripts/premerger_expand_events.py --plot
  python scripts/premerger_expand_events.py --events GW150914,GW170814,GW170823
  python scripts/premerger_expand_events.py --n-draws 12 --draw-events GW150914
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

from src.gw_events import GATE_P_EVENTS  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.pe_waveform import load_pe_posterior_draws  # noqa: E402
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    prepare_premerger_network,
)
from src.premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END  # noqa: E402


def run_event(
    name: str,
    detectors: list[str],
    *,
    inv: InvariantSet,
    approximant: str,
    gate_dchi2: float,
    t_end: float,
    f_low: float,
    f_high: float,
    params=None,
) -> dict:
    event, dets = prepare_premerger_network(
        name,
        detectors,
        project_root=project_root,
        duration_pre_s=4.0,
        f_low=f_low,
        f_high=f_high,
        approximant=approximant,
        params=params,
    )
    fit = fit_premerger_phase_network(
        dets,
        event,
        t_end=t_end,
        f_low=f_low,
        f_high=f_high,
        gate_dchi2=gate_dchi2,
        inv=inv,
    )
    return {
        "event": name,
        "mass_final": event.mass_final_solar,
        "alpha_hat": fit.alpha_hat,
        "alpha_sigma": fit.alpha_sigma,
        "delta_chi2": fit.delta_chi2,
        "gate_p_pass": bool(fit.gate_p_pass),
        "pe_snr": {d.detector: d.pe_snr_proxy for d in dets},
        "notes": fit.notes,
        "approximant": approximant,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Expanded Gate P + PE posterior draws")
    p.add_argument(
        "--events",
        default=",".join(GATE_P_EVENTS),
        help="Comma-separated BBH events",
    )
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument("--t-end", type=float, default=GATE_P_T_END)
    p.add_argument("--f-low", type=float, default=20.0)
    p.add_argument("--f-high", type=float, default=100.0)
    p.add_argument(
        "--draw-events",
        default="GW150914",
        help="Events for PE posterior draws (comma-separated)",
    )
    p.add_argument("--n-draws", type=int, default=12)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--skip-draws", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    events = [e.strip() for e in args.events.split(",") if e.strip()]
    draw_events = [e.strip() for e in args.draw_events.split(",") if e.strip()]
    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()

    print("=" * 72)
    print("EXPANDED MULTI-EVENT GATE P (sign-consistent network)")
    print(f"  events: {events}")
    print("=" * 72)

    multi_rows = []
    for name in events:
        print(f"\n--- {name} ---")
        try:
            row = run_event(
                name,
                detectors,
                inv=inv,
                approximant=args.approximant,
                gate_dchi2=args.gate_dchi2,
                t_end=args.t_end,
                f_low=args.f_low,
                f_high=args.f_high,
            )
            multi_rows.append(row)
            print(
                f"  α={row['alpha_hat']:.3e}±{row['alpha_sigma']:.3e}  "
                f"Δχ²={row['delta_chi2']:.2f}  "
                f"Gate P={'PASS' if row['gate_p_pass'] else 'fail'}  "
                f"M_f={row['mass_final']}"
            )
            for n in row["notes"]:
                if "sign" in n.lower() or n.startswith("H1") or n.startswith("L1"):
                    print(f"    · {n}")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            multi_rows.append(
                {"event": name, "error": str(exc), "gate_p_pass": False}
            )

    pass_rows = [r for r in multi_rows if r.get("gate_p_pass")]
    alphas_pass = [r["alpha_hat"] for r in pass_rows]
    same_sign = len(alphas_pass) >= 2 and (
        max(np.sign(alphas_pass)) * min(np.sign(alphas_pass)) > 0
    )
    gate_pd = len(pass_rows) >= 2 and same_sign

    print("\n" + "=" * 72)
    print("GATE P-D SUMMARY")
    print(f"{'event':<12} {'α_hat':>12} {'Δχ²':>8} {'pass':>6} {'M_f':>6}")
    for r in multi_rows:
        if r.get("error"):
            print(f"{r['event']:<12}  ERROR")
            continue
        print(
            f"{r['event']:<12} {r['alpha_hat']:12.3e} {r['delta_chi2']:8.2f} "
            f"{'YES' if r['gate_p_pass'] else 'no':>6} {r['mass_final']:6.1f}"
        )
    print("-" * 72)
    print(f"Gate P pass: {len(pass_rows)}/{len([r for r in multi_rows if 'error' not in r])}")
    print(f"Gate P-D (≥2 pass, same sign): {'PASS' if gate_pd else 'FAIL'}")
    if pass_rows:
        print(
            f"  passing α signs: "
            + ", ".join(f"{r['event']}={np.sign(r['alpha_hat']):+.0f}" for r in pass_rows)
        )
    print("=" * 72)

    # PE posterior draws
    draw_payload = {}
    if not args.skip_draws:
        print("\n" + "=" * 72)
        print("PE POSTERIOR DRAWS (replace medians)")
        for name in draw_events:
            print(f"\n--- {name}: {args.n_draws} posterior draws ---")
            try:
                draws = load_pe_posterior_draws(
                    name,
                    n_draws=args.n_draws,
                    seed=args.seed,
                    pe_dir=project_root / "data" / "pe",
                    approximant=args.approximant,
                )
            except Exception as exc:
                print(f"  FAILED to load draws: {exc}")
                draw_payload[name] = {"error": str(exc)}
                continue
            draw_rows = []
            for i, params in enumerate(draws):
                try:
                    row = run_event(
                        name,
                        detectors,
                        inv=inv,
                        approximant=args.approximant,
                        gate_dchi2=args.gate_dchi2,
                        t_end=args.t_end,
                        f_low=args.f_low,
                        f_high=args.f_high,
                        params=params,
                    )
                    draw_rows.append(
                        {
                            "draw": i,
                            "mass1": params.mass1,
                            "mass2": params.mass2,
                            "distance_mpc": params.distance_mpc,
                            "alpha_hat": row["alpha_hat"],
                            "delta_chi2": row["delta_chi2"],
                            "gate_p_pass": row["gate_p_pass"],
                        }
                    )
                    print(
                        f"  draw {i:02d}: m1={params.mass1:.1f} m2={params.mass2:.1f}  "
                        f"α={row['alpha_hat']:.3e}  Δχ²={row['delta_chi2']:.1f}  "
                        f"{'PASS' if row['gate_p_pass'] else 'fail'}"
                    )
                except Exception as exc:
                    print(f"  draw {i:02d}: FAILED {exc}")
                    draw_rows.append({"draw": i, "error": str(exc), "gate_p_pass": False})
            ok = [r for r in draw_rows if r.get("error") is None]
            n_pass = sum(1 for r in ok if r["gate_p_pass"])
            alphas = [r["alpha_hat"] for r in ok if r["gate_p_pass"]]
            signs = [np.sign(a) for a in alphas]
            sign_frac = (
                max(signs.count(1), signs.count(-1)) / len(signs) if signs else 0.0
            )
            print(
                f"  draws Gate P: {n_pass}/{len(ok)}  "
                f"median α (all)={np.median([r['alpha_hat'] for r in ok]):.3e}  "
                f"sign_majority={sign_frac:.2f}"
            )
            draw_payload[name] = {
                "n_draws": len(ok),
                "n_pass": n_pass,
                "pass_frac": n_pass / max(len(ok), 1),
                "median_alpha_all": float(np.median([r["alpha_hat"] for r in ok])),
                "median_alpha_pass": float(np.median(alphas)) if alphas else None,
                "sign_majority_frac": float(sign_frac),
                "rows": draw_rows,
            }

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / "premerger_expand_events.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_expand.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "multi_event": multi_rows,
        "n_gate_p_pass": len(pass_rows),
        "gate_p_d_pass": bool(gate_pd),
        "pe_posterior_draws": draw_payload,
        "gate_p": {
            "delta_chi2": args.gate_dchi2,
            "t_end": args.t_end,
            "band_hz": [args.f_low, args.f_high],
            "approximant": args.approximant,
        },
        "note": (
            "Expanded GWTC-1 BBH set with H1/L1 sign-consistent Gate P. "
            "PE draws replace medians for selected events."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")

    if args.plot and multi_rows:
        try:
            import matplotlib.pyplot as plt

            ok = [r for r in multi_rows if "error" not in r]
            labels = [r["event"] for r in ok]
            dchi = [r["delta_chi2"] for r in ok]
            al = [r["alpha_hat"] for r in ok]
            colors = ["C2" if r["gate_p_pass"] else "C3" for r in ok]
            x = np.arange(len(ok))
            fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
            axes[0].bar(x, dchi, color=colors)
            axes[0].axhline(args.gate_dchi2, color="k", ls="--")
            axes[0].set_ylabel("Δχ²")
            axes[0].set_title(
                f"Expanded Gate P  pass={len(pass_rows)}/{len(ok)}  "
                f"P-D={'PASS' if gate_pd else 'FAIL'}"
            )
            axes[1].bar(x, al, color=colors)
            axes[1].axhline(0, color="k", lw=0.5)
            axes[1].set_ylabel("α_hat")
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(labels, rotation=25, ha="right")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")

            # PE draw plot for first draw event
            if draw_payload:
                name0 = next(iter(draw_payload))
                dr = draw_payload[name0]
                if "rows" in dr:
                    okd = [r for r in dr["rows"] if "error" not in r]
                    fig2, ax = plt.subplots(figsize=(7, 4))
                    cols = ["C2" if r["gate_p_pass"] else "C3" for r in okd]
                    ax.scatter(
                        [r["mass1"] + r["mass2"] for r in okd],
                        [r["alpha_hat"] for r in okd],
                        c=cols,
                    )
                    ax.axhline(0, color="k", lw=0.5)
                    ax.set_xlabel("m1+m2 (detector frame)")
                    ax.set_ylabel("α_hat")
                    ax.set_title(
                        f"{name0} PE posterior draws  "
                        f"pass={dr['n_pass']}/{dr['n_draws']}"
                    )
                    fig2.tight_layout()
                    fig2.savefig(
                        out.with_name(out.stem + f"_{name0}_draws.png"), dpi=150
                    )
                    print(f"Wrote {out.with_name(out.stem + f'_{name0}_draws.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
