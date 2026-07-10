#!/usr/bin/env python3
"""
Phase 2.2 — Topological Yukawa ansatz: spectrum + PDG χ² + Gate SM-2 mass.

Usage:
  python scripts/sm_yukawa_ansatz.py
  python scripts/sm_yukawa_ansatz.py --sweep --trials 64 --plot
  python scripts/sm_yukawa_ansatz.py --no-optimize   # evaluate default params only
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
from src.sm_yukawa import (  # noqa: E402
    PDG_CKM,
    PDG_MASSES_GEV,
    evaluate_yukawa,
    gate_sm2_mass_report,
    optimize_yukawa,
)

OUTPUT_DIR = project_root / "outputs" / "sm_yukawa"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def print_mass_table(ev: dict) -> None:
    masses = ev["spectrum"]["masses_GeV"]
    print(f"\n{'name':6} {'pred [GeV]':>14} {'PDG [GeV]':>14} {'ratio':>10}")
    print("-" * 50)
    for name, m_pdg in PDG_MASSES_GEV.items():
        m_pr = masses[name]
        ratio = m_pr / m_pdg if m_pdg else float("nan")
        print(f"{name:6} {m_pr:14.6e} {m_pdg:14.6e} {ratio:10.3f}")


def print_ckm_table(ev: dict) -> None:
    ckm = ev["spectrum"]["ckm_abs"]
    print(f"\n{'|V|':6} {'pred':>12} {'PDG':>12}")
    print("-" * 34)
    for k, v_pdg in PDG_CKM.items():
        print(f"{k:6} {ckm.get(k, 0.0):12.5f} {v_pdg:12.5f}")


def maybe_plot(report: dict, out_base: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    masses = report["spectrum"]["masses_GeV"]
    names = list(PDG_MASSES_GEV.keys())
    pred = np.array([masses[n] for n in names])
    pdg = np.array([PDG_MASSES_GEV[n] for n in names])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax = axes[0]
    x = np.arange(len(names))
    ax.semilogy(x, pdg, "o", label="PDG", markersize=8)
    ax.semilogy(x, pred, "s", label="ansatz", markersize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("mass [GeV]")
    ax.set_title("Charged fermion masses")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    ax2 = axes[1]
    ckm_keys = list(PDG_CKM.keys())
    pred_c = [report["spectrum"]["ckm_abs"].get(k, 0) for k in ckm_keys]
    pdg_c = [PDG_CKM[k] for k in ckm_keys]
    x2 = np.arange(len(ckm_keys))
    w = 0.35
    ax2.bar(x2 - w / 2, pdg_c, w, label="PDG")
    ax2.bar(x2 + w / 2, pred_c, w, label="ansatz")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(ckm_keys, rotation=45, ha="right")
    ax2.set_ylabel("|V|")
    ax2.set_title("CKM magnitudes")
    ax2.legend()
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle(
        f"Topological Yukawa — Gate SM-2 {report.get('grade', '')}  "
        f"(W_g={LOCKED_WG:.3f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING})"
    )
    fig.tight_layout()
    path = out_base.with_suffix(".png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2.2 topological Yukawa ansatz")
    p.add_argument("--sweep", action="store_true", help="Run Optuna/random optimization")
    p.add_argument("--trials", type=int, default=64)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-optimize", action="store_true", help="Evaluate default params only")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    print("=== Phase 2.2 Topological Yukawa / Gate SM-2 mass ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")

    optimize = args.sweep or not args.no_optimize
    if args.no_optimize:
        optimize = False

    if optimize:
        print(f"  optimizing Yukawa params (trials={args.trials}, seed={args.seed}) …")
        report = gate_sm2_mass_report(
            n_trials=args.trials, seed=args.seed, optimize=True
        )
    else:
        print("  evaluating default Yukawa params (no sweep)")
        report = gate_sm2_mass_report(optimize=False)

    ev_like = {
        "spectrum": report["spectrum"],
        "chi2_mass": report["chi2_mass"],
        "chi2_ckm": report["chi2_ckm"],
    }
    # spectrum nested differently in gate report
    print_mass_table(
        {
            "spectrum": {
                "masses_GeV": report["spectrum"]["masses_GeV"],
            }
        }
    )
    print_ckm_table(
        {
            "spectrum": {
                "ckm_abs": report["spectrum"]["ckm_abs"],
            }
        }
    )

    print(f"\nχ²_mass / dof = {report['chi2_mass']['chi2_per_dof']:.4f}  "
          f"(thr pass {report['thresholds']['chi2_mass_per_dof_pass']})")
    print(f"χ²_CKM  / dof = {report['chi2_ckm']['chi2_per_dof']:.4f}  "
          f"(thr pass {report['thresholds']['chi2_ckm_per_dof_pass']})")
    print(f"χ²_total      = {report['chi2_total']:.4f}")
    print(f"\nGate SM-2: {'PASS' if report['pass'] else 'FAIL'}  grade={report['grade']}")
    for k, v in report["criteria"].items():
        print(f"  {k}: {v}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"sm_yukawa_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "sm_yukawa_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    if args.plot:
        plot_path = maybe_plot(report, out)
        if plot_path:
            print(f"  plot {plot_path}")

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
