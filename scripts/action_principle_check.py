#!/usr/bin/env python3
"""
Phase 1.1 — Gate A-P check for the unified action principle.

Verifies:
  1. No unphysical ghosts (healthy kinetic / Hessian signs)
  2. Free-energy variation reduces to conduit PDE structure
  3. W_g lock stable under multi-amplitude holonomy / gauge jitter
  4. Mean-field holonomy eigenvalue restoring (−κ < 0)
  5. Holonomy+braiding Hessian positive definite (quantitative)
  6. Optional: PDE stability suite (restoring + driven) with energy diagnostics

Usage:
  python scripts/action_principle_check.py
  python scripts/action_principle_check.py --pde-smoke
  python scripts/action_principle_check.py --pde-smoke --nx 16 --nt 2000
  python scripts/action_principle_check.py --latex
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.action_principle import (  # noqa: E402
    ActionParameters,
    action_principle_report,
    latex_action_principle,
    pde_stability_suite,
)
from src.invariants import DEFAULT_KAPPA, LOCKED_WG, WG_BASE  # noqa: E402

OUTPUT_DIR = project_root / "outputs" / "action_principle"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1.1 action principle Gate A-P")
    parser.add_argument("--n-stability", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--pde-smoke",
        action="store_true",
        help="Run PDE stability suite (restoring + driven) with energy diagnostics",
    )
    parser.add_argument("--nx", type=int, default=16, help="PDE grid size per side")
    parser.add_argument(
        "--nt",
        type=int,
        default=2000,
        help="PDE timesteps (default 2000; was 200 in the weak smoke)",
    )
    parser.add_argument(
        "--driven-flux",
        type=float,
        default=0.02,
        help="Gauge flux for driven PDE case",
    )
    parser.add_argument(
        "--gauge-flux",
        type=float,
        default=None,
        help="(deprecated alias) if set without suite, run single-flux note only",
    )
    parser.add_argument("--latex", action="store_true", help="Print LaTeX action fragment")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="JSON output path (default: outputs/action_principle/…)",
    )
    args = parser.parse_args()

    if args.latex:
        print(latex_action_principle())
        return 0

    params = ActionParameters()  # frozen locks defaults

    print("=== Phase 1.1 Action Principle — Gate A-P ===")
    print(f"  locks: W_g={LOCKED_WG:.6f} (base {WG_BASE}), κ={DEFAULT_KAPPA}")
    print(f"  ActionParameters: W_g={params.wg:.6f}, κ={params.kappa}, φ_b={params.braiding}")

    try:
        report = action_principle_report(
            params,
            n_stability=args.n_stability,
            seed=args.seed,
            include_pde=False,  # suite added below for clearer printing
            pde_nx=args.nx,
            pde_nt=args.nt,
        )
    except Exception as exc:
        print(f"ERROR: action_principle_report failed: {exc}")
        traceback.print_exc()
        return 2

    gate = report["gate_A_P"]

    print("\n--- Sector densities (symbolic) ---")
    for name, expr in report["sectors"].items():
        print(f"  {name}: {expr}")

    print("\n--- Ghost check ---")
    gh = report["ghost_check"]
    print(f"  healthy: {gh['healthy']}")
    for k, v in gh["checks"].items():
        print(f"    {k}: {v}")

    print("\n--- Conduit reduction ---")
    red = report["conduit_reduction"]
    print(f"  matches structure: {red['matches_conduit_structure']}")

    print("\n--- W_g stability under multi-amplitude jitter ---")
    st = report["wg_stability"]
    print(f"  residual max: {st['wg_residual_max']:.3e}")
    print(f"  ghost-free fraction: {st['ghost_free_fraction']:.3f}")
    print(f"  primary pass: {st['pass']}")
    for scale_name, scale_res in (st.get("multi_amplitude") or {}).items():
        print(
            f"    {scale_name}: ghost-free={scale_res['ghost_free_fraction']:.3f} "
            f"wg_res={scale_res['wg_residual_max']:.1e} pass={scale_res['pass']}"
        )

    print("\n--- Hessian metrics (holonomy + braiding) ---")
    hess = report["hessian_metrics"]
    print(f"  eigenvalues: κ={hess['kappa']:.4f}, W_g={hess['wg']:.4f}")
    print(f"  condition number: {hess['condition_number']:.4f}")
    print(f"  positive definite: {hess['positive_definite']}")

    print("\n--- Mean-field linearization ---")
    lin = report["mean_field_linearization"]
    print(
        f"  eigenvalue: {lin['mean_field_eigenvalue']:.4f}  "
        f"restoring={lin['restoring']}  "
        f"fixed_point≈{lin['fixed_point_approx']:.4f}"
    )

    print("\n--- Quantitative summary ---")
    for k, v in report.get("quantitative_summary", {}).items():
        print(f"  {k}: {v}")

    if args.pde_smoke:
        print("\n--- PDE stability suite (restoring + driven) ---")
        print(f"  nx={args.nx}  nt={args.nt}  driven_flux={args.driven_flux}")
        if args.gauge_flux is not None:
            print(
                f"  note: --gauge-flux={args.gauge_flux} ignored for suite; "
                f"use --driven-flux (default {args.driven_flux})"
            )
        try:
            suite = pde_stability_suite(
                params,
                nx=args.nx,
                nt=args.nt,
                seed=args.seed,
                driven_flux=args.driven_flux,
            )
        except Exception as exc:
            print(f"  ERROR: PDE suite failed: {exc}")
            traceback.print_exc()
            suite = {
                "pass": False,
                "error": str(exc),
                "criteria": {"restoring_pass": False, "driven_pass": False},
            }

        report["pde_stability"] = suite
        # Merge PDE into gate criteria
        gate = dict(report["gate_A_P"])
        crit = dict(gate.get("criteria", {}))
        crit["pde_stability"] = bool(suite.get("pass"))
        rest = suite.get("restoring") or {}
        crit["energy_dissipation"] = bool(
            rest.get("dissipating") or rest.get("dynamics_ok")
        )
        gate["criteria"] = crit
        gate["pass"] = all(crit.values())
        report["gate_A_P"] = gate

        if "restoring" in suite:
            r = suite["restoring"]
            d = suite["driven"]
            print(
                f"  restoring: mean {r['initial']['mean_theta']:.4f}→"
                f"{r['final']['mean_theta']:.4f}  "
                f"dE/dt={r['energy_dissipation_rate']:.3e}  "
                f"pass={r['pass']}"
            )
            print(
                f"  driven:    mean {d['initial']['mean_theta']:.4f}→"
                f"{d['final']['mean_theta']:.4f}  "
                f"max|F|={d['max_abs_force_global']:.3e}  "
                f"pass={d['pass']}"
            )
            print(f"  suite pass: {suite['pass']}")
            # Drop bulky histories from saved JSON for readability
            for key in ("restoring", "driven"):
                block = suite.get(key)
                if isinstance(block, dict):
                    for hist in (
                        "mean_history",
                        "energy_history",
                        "times",
                        "max_abs_force_history",
                    ):
                        if hist in block and len(block[hist]) > 20:
                            block[hist + "_len"] = len(block[hist])
                            block[hist + "_head"] = block[hist][:3]
                            block[hist + "_tail"] = block[hist][-3:]
                            del block[hist]

    print("\n=== Gate A-P ===")
    print(f"  PASS: {report['gate_A_P']['pass']}")
    for k, v in report["gate_A_P"]["criteria"].items():
        print(f"    {k}: {v}")
    thr = report["gate_A_P"].get("thresholds") or {}
    if thr:
        print("  thresholds:")
        for k, v in thr.items():
            print(f"    {k}: {v}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"action_principle_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    latest = OUTPUT_DIR / "action_principle_latest.json"
    text = json.dumps(report, indent=2, default=str)
    out.write_text(text)
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    return 0 if report["gate_A_P"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
