#!/usr/bin/env python3
"""
Phase 2.3 — SM one-loop gauge RG flow + Gate SM-3.

Usage:
  python scripts/sm_rg_flow.py
  python scripts/sm_rg_flow.py --plot
  python scripts/sm_rg_flow.py --mu-max 1e16 --points 100
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
from src.sm_rg import (  # noqa: E402
    MZ_GEV,
    gate_sm3_full_report,
    rg_trajectory,
    sm_rg_summary_table,
)

OUTPUT_DIR = project_root / "outputs" / "sm_rg"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def print_table(rows: list[dict]) -> None:
    print(
        f"{'μ [GeV]':>12} {'α1':>10} {'α2':>10} {'α3':>10} "
        f"{'α_em':>10} {'sin²θW':>10} {'α_s':>10}"
    )
    print("-" * 78)
    for r in rows:
        mu = r["mu_GeV"]
        mu_s = f"{mu:.3e}" if mu >= 1e4 else f"{mu:.1f}"
        print(
            f"{mu_s:>12} {r['alpha1']:10.5f} {r['alpha2']:10.5f} {r['alpha3']:10.5f} "
            f"{r['alpha_em']:10.5f} {r['sin2_theta_w']:10.5f} {r['alpha_s']:10.5f}"
        )


def maybe_plot(traj: dict, out_base: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    rows = traj["trajectory"]
    mu = np.array([r["mu_GeV"] for r in rows])
    inv1 = np.array([r["inv1"] for r in rows])
    inv2 = np.array([r["inv2"] for r in rows])
    inv3 = np.array([r["inv3"] for r in rows])
    a3 = np.array([r["alpha3"] for r in rows])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax = axes[0]
    ax.semilogx(mu, inv1, label=r"$\alpha_1^{-1}$")
    ax.semilogx(mu, inv2, label=r"$\alpha_2^{-1}$")
    ax.semilogx(mu, inv3, label=r"$\alpha_3^{-1}$")
    ax.axvline(MZ_GEV, color="k", ls="--", alpha=0.4, label=r"$M_Z$")
    ax.set_xlabel(r"$\mu$ [GeV]")
    ax.set_ylabel(r"$\alpha_i^{-1}$")
    ax.set_title("One-loop SM gauge couplings (GUT-normalized)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.semilogx(mu, a3, color="C2")
    ax2.axvline(MZ_GEV, color="k", ls="--", alpha=0.4)
    ax2.set_xlabel(r"$\mu$ [GeV]")
    ax2.set_ylabel(r"$\alpha_3(\mu)$")
    ax2.set_title(r"Asymptotic freedom ($\alpha_s$)")
    ax2.grid(True, alpha=0.3)

    fig.suptitle(
        f"Phase 2.3 SM RG — locks W_g={LOCKED_WG:.3f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}"
    )
    fig.tight_layout()
    path = out_base.with_suffix(".png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2.3 SM one-loop gauge RG")
    p.add_argument("--mu-max", type=float, default=1e16)
    p.add_argument("--points", type=int, default=80)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    print("=== Phase 2.3 SM gauge RG (one-loop) + Gate SM-3 ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  μ ∈ [{MZ_GEV}, {args.mu_max:g}] GeV  points={args.points}")

    print("\n--- Multi-scale table ---")
    print_table(sm_rg_summary_table())

    traj = rg_trajectory(mu_max=args.mu_max, n_points=args.points)
    print("\n--- Evolution health ---")
    print(f"  asymptotic freedom α_s: {traj['asymptotic_freedom_alpha_s']}")
    print(f"  Landau-free in window:  {traj['landau_free_in_window']}")
    rt = traj["round_trip"]
    print(
        f"  round-trip Δα_s={rt['delta_alpha_s']:.3e}  "
        f"Δsin²θW={rt['delta_sin2w']:.3e}  "
        f"Δα_em/α={rt['delta_alpha_em_rel']:.3e}"
    )

    report = gate_sm3_full_report(n_points=args.points, mu_max=args.mu_max)
    print(f"\nGate SM-3: {'PASS' if report['pass'] else 'FAIL'}")
    for k, v in report["criteria"].items():
        print(f"  {k}: {v}")
    for k, v in report["rg_criteria_detail"].items():
        print(f"  rg.{k}: {v}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"sm_rg_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gate_SM3": report,
        "trajectory_meta": {
            k: traj[k]
            for k in traj
            if k != "trajectory"
        },
        "trajectory": traj["trajectory"],
        "summary_table": sm_rg_summary_table(),
    }
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "sm_rg_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    if args.plot:
        plot_path = maybe_plot(traj, out)
        if plot_path:
            print(f"  plot {plot_path}")

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
