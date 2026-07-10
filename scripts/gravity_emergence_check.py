#!/usr/bin/env python3
"""
Phase 3 — Emergent gravity Gate GR-1 / GR-2 runner.

Usage:
  python scripts/gravity_emergence_check.py
  python scripts/gravity_emergence_check.py --gates GR-1,GR-2 --plot
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

from src.gravity_emergence import (  # noqa: E402
    G_CODATA,
    M_SUN_KG,
    GravityParams,
    gate_gr1_report,
    gate_gr2_report,
    g_n_schema,
    g_n_si_matched,
    gravity_full_report,
    newtonian_potential,
)
from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG  # noqa: E402

OUTPUT_DIR = project_root / "outputs" / "gravity"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def maybe_plot(out_base: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    lams = np.linspace(0.2, 2.0, 40)
    Gs = [g_n_schema(GravityParams(lambda_sigma=float(lam)))["G_schema"] for lam in lams]

    r_au = np.linspace(0.3, 5.0, 50) * 1.496e11
    Phis = [newtonian_potential(M_SUN_KG, float(r))["Phi"] for r in r_au]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax = axes[0]
    ax.plot(lams, Gs, color="C0")
    ax.set_xlabel(r"$\lambda_\sigma$")
    ax.set_ylabel(r"$G_{\mathrm{schema}}$")
    ax.set_title(r"$G_N$ schema vs $\lambda$ (locks frozen)")
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(r_au / 1.496e11, Phis, color="C1")
    ax2.set_xlabel("r [AU]")
    ax2.set_ylabel(r"$\Phi$ [J/kg]")
    ax2.set_title("Newtonian potential (Sun, matched G)")
    ax2.grid(True, alpha=0.3)

    fig.suptitle(
        f"Phase 3 gravity — W_g={LOCKED_WG:.3f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}"
    )
    fig.tight_layout()
    path = out_base.with_suffix(".png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 3 emergent gravity gates")
    p.add_argument("--gates", type=str, default="GR-1,GR-2")
    p.add_argument("--require", type=str, default="GR-1")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    want = {g.strip().upper() for g in args.gates.split(",") if g.strip()}
    require = {g.strip().upper() for g in args.require.split(",") if g.strip()}

    print("=== Phase 3 Emergent Gravity ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  G_CODATA = {G_CODATA:.6e}")

    schema = g_n_schema()
    matched = g_n_si_matched()
    print("\n--- G_N schema ---")
    print(f"  G_schema = {schema['G_schema']:.6e}  ({schema['formula']})")
    print(f"  G_SI_matched / G_CODATA = {matched['ratio_to_codata']:.6f}")
    print(f"  {matched['matching_note']}")

    results: dict[str, dict] = {}
    if "GR-1" in want:
        r = gate_gr1_report()
        results["GR-1"] = r
        print(f"\nGate GR-1: {'PASS' if r['pass'] else 'FAIL'}")
        for k, v in r["criteria"].items():
            print(f"  {k}: {v}")
        print(f"  Φ(1 AU) = {r['weak_field_1AU']['Phi']:.6e} J/kg")
        print(f"  g_sun surface = {r['solar_surface']['g_accel']:.4f} m/s²")

    if "GR-2" in want:
        r = gate_gr2_report()
        results["GR-2"] = r
        print(f"\nGate GR-2: {'PASS' if r['pass'] else 'FAIL'}")
        for k, v in r["criteria"].items():
            print(f"  {k}: {v}")
        print(
            f"  light deflection: {r['light_deflection']['delta_arcsec']:.4f}\" "
            f"(target {r['light_deflection']['target_arcsec']}\")"
        )
        print(
            f"  Mercury perihelion: {r['perihelion_mercury']['arcsec_per_century']:.2f}\" / cy "
            f"(target {r['perihelion_mercury']['target_arcsec_per_century']})"
        )
        print(
            f"  Shapiro 2GM/c³: {r['shapiro']['two_GM_over_c3_us']:.3f} µs "
            f"(target {r['shapiro']['target_us']} µs)"
        )

    payload = {
        "schema": "invariant_hunt.gravity_check.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "gates_requested": sorted(want),
        "gates_required": sorted(require),
        "G_schema": schema,
        "G_matched": matched,
        "results": {
            k: {"pass": v["pass"], "criteria": v["criteria"], "gate": v.get("gate")}
            for k, v in results.items()
        },
        "full": gravity_full_report() if want >= {"GR-1", "GR-2"} else None,
        "detail": results,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"gravity_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "gravity_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    if args.plot:
        plot_path = maybe_plot(out)
        if plot_path:
            print(f"  plot {plot_path}")

    ok = all(results[g]["pass"] for g in require if g in results)
    missing = require - set(results)
    if missing:
        print(f"  WARNING: required gates not run: {missing}")
        ok = False
    print(f"\nRequired {sorted(require)}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
