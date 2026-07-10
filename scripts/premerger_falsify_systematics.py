#!/usr/bin/env python3
"""
Gate S-1: PE/systematics deep-dive on pre-merger FALSIFY (or any) events.

Highest-priority follow-up after held-out FALSIFY + large B_10:
  multi-approximant, PE jitter, posterior draws, corr(r,τ), time cuts, ln B_10.

Usage:
  python scripts/premerger_falsify_systematics.py --event GW170809
  python scripts/premerger_falsify_systematics.py --events GW170809,GW151012 --n-draws 10
  python scripts/premerger_falsify_systematics.py --event GW170809 --skip-draws --plot
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG  # noqa: E402
from src.premerger_systematics import (  # noqa: E402
    DEFAULT_APPROXIMANTS,
    deep_dive_event,
)

OUTPUT_DIR = project_root / "outputs" / "systematics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Gate S-1 PE systematics deep-dive")
    p.add_argument("--event", type=str, default="")
    p.add_argument("--events", type=str, default="")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument(
        "--approximants",
        default=",".join(DEFAULT_APPROXIMANTS),
    )
    p.add_argument("--n-draws", type=int, default=12)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--skip-draws", action="store_true")
    p.add_argument("--skip-jitter", action="store_true")
    p.add_argument("--duration-pre", type=float, default=4.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    if args.events:
        names = [e.strip() for e in args.events.split(",") if e.strip()]
    elif args.event:
        names = [args.event.strip()]
    else:
        names = ["GW170809"]

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    approximants = [a.strip() for a in args.approximants.split(",") if a.strip()]

    print("=== Gate S-1: PE/systematics deep-dive (FALSIFY follow-up) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print("  band not re-fit; core locks frozen")
    print(f"  events: {names}")
    print(f"  approximants: {approximants}")

    reports = []
    for name in names:
        print(f"\n{'=' * 70}\nEVENT {name}\n{'=' * 70}")
        rep = deep_dive_event(
            name,
            project_root=project_root,
            detectors=detectors,
            approximants=approximants,
            n_draws=args.n_draws,
            seed=args.seed,
            skip_draws=args.skip_draws,
            skip_jitter=args.skip_jitter,
            duration_pre_s=args.duration_pre,
        )
        reports.append(rep)

        print("\n--- Approximants ---")
        for r in rep["approximants"]:
            if r.get("error"):
                print(f"  {r['approximant']:<16} FAILED: {r['error']}")
                continue
            lnB = r.get("ln_B_10")
            lnB_s = f"{lnB:.2f}" if lnB is not None else "n/a"
            print(
                f"  {r['approximant']:<16} α={r['alpha_hat']:+.3e}±{r['alpha_sigma']:.2e}  "
                f"Δχ²={r['delta_chi2']:8.2f}  lnB={lnB_s:>8}  "
                f"GateP={'PASS' if r['gate_p_pass'] else 'fail'}"
            )
            if r.get("corr_r_tau"):
                c = r["corr_r_tau"]
                print(
                    f"    {'':16} corr(r,τ) H1={c.get('H1', float('nan')):.3f}  "
                    f"L1={c.get('L1', float('nan')):.3f}"
                )

        if rep["pe_jitter"]:
            print("\n--- PE jitter ---")
            for r in rep["pe_jitter"]:
                if r.get("error"):
                    print(f"  {r['label']:<14} FAILED: {r['error']}")
                    continue
                print(
                    f"  {r['label']:<14} α={r['alpha_hat']:+.3e}  "
                    f"Δχ²={r['delta_chi2']:7.2f}  "
                    f"{'PASS' if r['gate_p_pass'] else 'fail'}"
                )

        if rep.get("posterior_draws"):
            d = rep["posterior_draws"]
            print("\n--- PE posterior draws ---")
            print(
                f"  Gate P pass: {d['n_gate_p_pass']}/{d['n_ok']}  "
                f"frac={d['pass_frac']:.2f}"
            )
            if d["alpha_mean"] is not None:
                print(
                    f"  α: mean={d['alpha_mean']:+.3e}  std={d['alpha_std']:.3e}  "
                    f"median={d['alpha_median']:+.3e}  "
                    f"frac(+)= {d['frac_positive']:.2f}"
                )

        g = rep["gate_S1"]
        print(f"\n=== Gate S-1: {g['verdict']} ===")
        print(f"  flags: {g['flags'] or '(none)'}")
        print(f"  {g['interpretation']}")

    payload = {
        "schema": "invariant_hunt.premerger_falsify_systematics.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "events": reports,
        "summary": {
            r["event"]: r["gate_S1"]["verdict"] for r in reports
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"falsify_systematics_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "falsify_systematics_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    if args.plot and reports:
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            for rep in reports:
                ok = [r for r in rep["approximants"] if r.get("error") is None]
                if not ok:
                    continue
                labels = [r["approximant"] for r in ok]
                dchi = [r["delta_chi2"] for r in ok]
                al = [r["alpha_hat"] for r in ok]
                colors = ["C2" if r["gate_p_pass"] else "C3" for r in ok]
                x = np.arange(len(labels))
                fig, axes = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True)
                axes[0].bar(x, dchi, color=colors)
                axes[0].axhline(6.0, color="k", ls="--")
                axes[0].set_ylabel("Δχ²")
                axes[0].set_title(
                    f"{rep['event']} Gate S-1 — {rep['gate_S1']['verdict']}"
                )
                axes[1].bar(x, al, color=colors)
                axes[1].axhline(0, color="k", lw=0.5)
                axes[1].axhline(1.15e-4, color="C0", ls=":", label="band max")
                axes[1].axhline(2.88e-5, color="C0", ls=":")
                axes[1].set_ylabel("α_hat")
                axes[1].set_xticks(x)
                axes[1].set_xticklabels(labels, rotation=20, ha="right")
                axes[1].legend(fontsize=8)
                fig.tight_layout()
                plot_path = OUTPUT_DIR / f"{rep['event']}_falsify_systematics.png"
                fig.savefig(plot_path, dpi=150)
                plt.close(fig)
                print(f"  plot {plot_path}")
        except ImportError:
            print("matplotlib not available")

    # Exit 0 always (diagnostic); verdict is in JSON
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
