#!/usr/bin/env python3
"""
Mass-scaled multi-event Gate P-D for pre-merger phase coupling.

Fits α on each event, then tests whether a shared physical coupling
  β = α · (M_f / M_ref)^p
is more consistent across events than raw α (p scanned).

This is exploratory after PE robustness; does not change core locks.

Usage:
  python scripts/premerger_mass_scale.py --events GW150914,GW170104,GW151226
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
)
from src.premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Mass-scaled multi-event Gate P")
    p.add_argument(
        "--events",
        default="GW150914,GW170104,GW151226",
    )
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--m-ref", type=float, default=30.0, help="Reference mass (M_sun)")
    p.add_argument("--p-min", type=float, default=-2.0)
    p.add_argument("--p-max", type=float, default=2.0)
    p.add_argument("--n-p", type=int, default=21)
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    events = [e.strip() for e in args.events.split(",") if e.strip()]
    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()

    print("=" * 70)
    print("MASS-SCALED PRE-MERGER α (exploratory Gate P-D)")
    print(f"  β = α · (M_f / {args.m_ref})^p")
    print("=" * 70)

    rows = []
    for name in events:
        print(f"\n--- {name} ---")
        event, dets = prepare_premerger_network(
            name,
            detectors,
            project_root=project_root,
            duration_pre_s=4.0,
            approximant=args.approximant,
        )
        fit = fit_premerger_phase_network(
            dets,
            event,
            t_end=GATE_P_T_END,
            gate_dchi2=args.gate_dchi2,
            inv=inv,
        )
        print(
            f"  α={fit.alpha_hat:.3e}±{fit.alpha_sigma:.3e}  "
            f"Δχ²={fit.delta_chi2:.2f}  Gate P={'PASS' if fit.gate_p_pass else 'fail'}  "
            f"M_f={event.mass_final_solar}"
        )
        rows.append(
            {
                "event": name,
                "mass_final": event.mass_final_solar,
                "alpha_hat": fit.alpha_hat,
                "alpha_sigma": fit.alpha_sigma,
                "delta_chi2": fit.delta_chi2,
                "gate_p_pass": fit.gate_p_pass,
            }
        )

    # Only use events that pass Gate P for shared-β consistency
    pass_rows = [r for r in rows if r["gate_p_pass"]]
    p_grid = list(np.linspace(args.p_min, args.p_max, args.n_p))
    best = None
    scan = []
    for p_exp in p_grid:
        betas = []
        for r in pass_rows:
            scale = (r["mass_final"] / args.m_ref) ** p_exp
            betas.append(r["alpha_hat"] * scale)
        if len(betas) < 2:
            score = float("nan")
            sign_ok = False
        else:
            # consistency: relative std of β and same sign
            mu = float(np.mean(betas))
            score = float(np.std(betas) / (abs(mu) + 1e-30))
            sign_ok = bool(max(np.sign(betas)) * min(np.sign(betas)) > 0)
        entry = {
            "p": float(p_exp),
            "betas": betas,
            "rel_std": score,
            "sign_consistent": sign_ok,
            "n_events": len(betas),
        }
        scan.append(entry)
        if len(betas) >= 2 and sign_ok:
            if best is None or score < best["rel_std"]:
                best = entry

    print("\n" + "-" * 70)
    print(f"Events passing Gate P: {len(pass_rows)}/{len(rows)}")
    if best:
        print(
            f"Best mass scaling among passes: p={best['p']:.2f}  "
            f"rel_std(β)={best['rel_std']:.3f}  sign_ok={best['sign_consistent']}"
        )
        print(f"  β values: {best['betas']}")
    else:
        print(
            "No p with ≥2 Gate-P events and consistent β sign — "
            "mass scaling cannot rescue P-D with current passes."
        )
    print("-" * 70)

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / "premerger_mass_scale.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_mass_scale.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "m_ref": args.m_ref,
        "approximant": args.approximant,
        "events": rows,
        "p_scan": scan,
        "best": best,
        "note": (
            "Only events that already pass Gate P enter the β consistency test. "
            "If <2 pass, mass scaling cannot yield Gate P-D."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
