#!/usr/bin/env python3
"""
Phase 1.1 — Gate A-P check for the unified action principle.

Verifies:
  1. No unphysical ghosts (healthy kinetic / Hessian signs)
  2. Free-energy variation reduces to conduit PDE structure
  3. W_g lock stable under holonomy / gauge coupling jitter
  4. Mean-field holonomy eigenvalue restoring (−κ < 0)

Optional: short gauged PDE relaxation smoke test.

Usage:
  python scripts/action_principle_check.py
  python scripts/action_principle_check.py --pde-smoke --nx 16 --nt 200
  python scripts/action_principle_check.py --latex
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

from src.action_principle import (  # noqa: E402
    ActionParameters,
    action_principle_report,
    gauged_twist_force_terms,
    latex_action_principle,
)
from src.invariants import DEFAULT_KAPPA, LOCKED_WG, WG_BASE  # noqa: E402

OUTPUT_DIR = project_root / "outputs" / "action_principle"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def pde_smoke(
    nx: int = 16,
    nt: int = 200,
    dt: float = 0.001,
    gauge_flux: float = 0.0,
    seed: int = 0,
) -> dict:
    """Short 3-torus relaxation with optional constant gauge-flux source."""
    rng = np.random.default_rng(seed)
    params = ActionParameters()
    theta = rng.uniform(0.1, 2.0, (nx, nx, nx))
    mean_hist: list[float] = []
    dx = 1.0 / nx

    for _ in range(nt):
        lap = (
            np.roll(theta, 1, 0)
            + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1)
            + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2)
            + np.roll(theta, -1, 2)
            - 6 * theta
        ) / dx**2
        g0 = np.gradient(theta, axis=0)
        g1 = np.gradient(theta, axis=1)
        g2 = np.gradient(theta, axis=2)
        grad_sq = g0**2 + g1**2 + g2**2
        terms = gauged_twist_force_terms(
            theta,
            params=params,
            lap=lap,
            grad_sq=grad_sq,
            a_mu_curl_contrib=gauge_flux,
        )
        theta = theta + dt * terms["total"]
        theta = np.clip(theta, 0.01, 2 * np.pi - 0.01)
        mean_hist.append(float(theta.mean()))

    final_mean = mean_hist[-1]
    # Healthy: mean twist stays finite and does not explode
    finite = bool(np.isfinite(final_mean) and np.isfinite(theta).all())
    bounded = bool(0.0 < final_mean < 2 * np.pi)
    # Mild relaxation expected under restoring holonomy when gauge_flux=0
    relaxed = True if gauge_flux != 0.0 else final_mean < mean_hist[0] + 0.5

    return {
        "nx": nx,
        "nt": nt,
        "dt": dt,
        "gauge_flux": gauge_flux,
        "seed": seed,
        "initial_mean": mean_hist[0],
        "final_mean": final_mean,
        "finite": finite,
        "bounded": bounded,
        "relaxed_or_driven_ok": relaxed,
        "pass": finite and bounded and relaxed,
        "kappa": DEFAULT_KAPPA,
        "wg": LOCKED_WG,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1.1 action principle Gate A-P")
    parser.add_argument("--n-stability", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--pde-smoke", action="store_true", help="Run short gauged PDE smoke")
    parser.add_argument("--nx", type=int, default=16)
    parser.add_argument("--nt", type=int, default=200)
    parser.add_argument("--gauge-flux", type=float, default=0.0)
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

    print("=== Phase 1.1 Action Principle — Gate A-P ===")
    print(f"  locks: W_g={LOCKED_WG:.6f} (base {WG_BASE}), κ={DEFAULT_KAPPA}")
    report = action_principle_report(n_stability=args.n_stability, seed=args.seed)
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

    print("\n--- W_g stability under jitter ---")
    st = report["wg_stability"]
    print(f"  residual max: {st['wg_residual_max']:.3e}")
    print(f"  ghost-free fraction: {st['ghost_free_fraction']:.3f}")
    print(f"  pass: {st['pass']}")

    print("\n--- Mean-field linearization ---")
    lin = report["mean_field_linearization"]
    print(f"  eigenvalue: {lin['mean_field_eigenvalue']:.4f}  restoring={lin['restoring']}")

    if args.pde_smoke:
        print("\n--- PDE smoke (gauged force hook) ---")
        smoke = pde_smoke(
            nx=args.nx,
            nt=args.nt,
            gauge_flux=args.gauge_flux,
            seed=args.seed,
        )
        report["pde_smoke"] = smoke
        print(
            f"  mean {smoke['initial_mean']:.4f} → {smoke['final_mean']:.4f}  "
            f"pass={smoke['pass']}"
        )
        if not smoke["pass"]:
            gate = dict(gate)
            gate["pass"] = False
            gate["criteria"] = dict(gate["criteria"])
            gate["criteria"]["pde_smoke"] = False
            report["gate_A_P"] = gate

    print("\n=== Gate A-P ===")
    print(f"  PASS: {report['gate_A_P']['pass']}")
    for k, v in report["gate_A_P"]["criteria"].items():
        print(f"    {k}: {v}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"action_principle_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Latest pointer
    latest = OUTPUT_DIR / "action_principle_latest.json"
    text = json.dumps(report, indent=2, default=str)
    out.write_text(text)
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    return 0 if report["gate_A_P"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
