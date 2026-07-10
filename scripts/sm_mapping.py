#!/usr/bin/env python3
"""
Phase 2.1 — Lattice mode → SM boson/fermion mapping.

Usage:
  python scripts/sm_mapping.py --mode bosons_fermions
  python scripts/sm_mapping.py --mode bosons_fermions --plot
  python scripts/sm_mapping.py --mode table
  python scripts/sm_mapping.py --json
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

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG, WG_BASE  # noqa: E402
from src.sm_mapping import (  # noqa: E402
    default_lattice_mode_maps,
    expand_charge_components,
    gate_sm1_report,
    sm_content,
)

OUTPUT_DIR = project_root / "outputs" / "sm_mapping"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def print_table(n_generations: int = 3) -> None:
    fields = sm_content(n_generations=n_generations)
    print(f"{'name':18} {'su3':5} {'su2':4} {'Y':8} {'spin':5} {'chi':6} {'gen':4} lattice_mode")
    print("-" * 100)
    for f in fields:
        gen = "" if f.generation is None else str(f.generation)
        print(
            f"{f.name:18} {f.su3:5} {f.su2:4d} {f.Y:8.4f} {f.spin:5.1f} {f.chirality:6} "
            f"{gen:4} {f.lattice_mode}"
        )


def print_charges() -> None:
    print("\nElectric charges Q = T3 + Y/2 (generation 1):")
    for f in sm_content(n_generations=1):
        for c in expand_charge_components(f):
            print(f"  {c.label:12}  T3={c.T3:+.2f}  Y={c.Y:+.4f}  Q={c.Q:+.4f}")


def print_mode_maps() -> None:
    print("\nLattice mode maps (locks frozen):")
    for m in default_lattice_mode_maps():
        print(f"  [{m.mode_class}] → {m.sm_targets}")
        print(f"      {m.description}")


def maybe_plot(report: dict, out: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not available; skip plot")
        return None

    fields = report["fields"]
    fermions = [f for f in fields if f["statistics"] == "fermion"]
    gens = sorted({f["generation"] for f in fermions if f["generation"] is not None})
    stems = ["Q_L", "u_R", "d_R", "L_L", "e_R"]
    # Hypercharge matrix gen × stem
    Ymat = np.zeros((len(gens), len(stems)))
    for i, g in enumerate(gens):
        for j, stem in enumerate(stems):
            for f in fermions:
                if f["generation"] == g and f["name"].split("^")[0] == stem:
                    Ymat[i, j] = f["Y"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax = axes[0]
    im = ax.imshow(Ymat, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(stems)))
    ax.set_xticklabels(stems, rotation=45, ha="right")
    ax.set_yticks(range(len(gens)))
    ax.set_yticklabels([f"gen {g}" for g in gens])
    ax.set_title("Fermion hypercharge Y by generation")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax2 = axes[1]
    bosons = [f for f in fields if f["statistics"] == "boson"]
    names = [f["name"] for f in bosons]
    spins = [f["spin"] for f in bosons]
    ax2.bar(names, spins, color=["C0", "C1", "C2", "C3"][: len(names)])
    ax2.set_ylabel("spin")
    ax2.set_title("Gauge + Higgs (spin)")
    ax2.set_ylim(0, 1.2)
    fig.suptitle(
        f"SM mapping scaffold — W_g={LOCKED_WG:.4f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}"
    )
    fig.tight_layout()
    plot_path = out.with_suffix(".png")
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    return plot_path


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2.1 SM lattice mode mapping")
    p.add_argument(
        "--mode",
        choices=["bosons_fermions", "table", "charges", "maps", "all"],
        default="bosons_fermions",
    )
    p.add_argument("--generations", type=int, default=3)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--json", action="store_true", help="Write Gate SM-1 JSON report")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    print("=== Phase 2.1 SM mapping ===")
    print(f"  locks: W_g={LOCKED_WG:.6f} (base {WG_BASE}), κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  mode={args.mode}  generations={args.generations}")

    if args.mode in ("bosons_fermions", "table", "all"):
        print_table(args.generations)
    if args.mode in ("bosons_fermions", "charges", "all"):
        print_charges()
    if args.mode in ("bosons_fermions", "maps", "all"):
        print_mode_maps()

    report = gate_sm1_report(n_generations=args.generations)
    print(f"\nGate SM-1: {'PASS' if report['pass'] else 'FAIL'}")
    for k, v in report["criteria"].items():
        print(f"  {k}: {v}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"sm_mapping_{ts}.json")
    if args.json or args.plot or True:
        out.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(report, indent=2, default=str)
        out.write_text(text)
        latest = OUTPUT_DIR / "sm_mapping_latest.json"
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
