#!/usr/bin/env python3
"""
Unified integration status for Phases 1–3 + pre-merger freeze pointer.

Usage:
  python scripts/integration_status.py
  python scripts/integration_status.py --run-gates
  python scripts/integration_status.py --run-gates --gravity-nx 24
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

from src.invariants import (  # noqa: E402
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
)

OUTPUT_DIR = project_root / "outputs" / "integration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pre-registered α band (MILESTONE_PREMERGER_PREDICTIVE_FREEZE)
ALPHA_BAND = (2.88e-5, 1.15e-4)
CORE_EVENTS = ("GW150914", "GW170814")


def locks_block() -> dict:
    return {
        "W_g": LOCKED_WG,
        "wg_base": WG_BASE,
        "kappa": DEFAULT_KAPPA,
        "phi_b": DEFAULT_BRAIDING,
        "premerger_alpha_band": list(ALPHA_BAND),
        "premerger_core_events": list(CORE_EVENTS),
        "frozen": True,
    }


def run_gates(*, gravity_nx: int = 24) -> dict:
    """Execute gate reporters (may take a few seconds)."""
    from src.action_principle import action_principle_report
    from src.gauged_meta_sweep import run_locks_fixed_monte_carlo
    from src.gravity_emergence import gate_gr1_report, gate_gr2_report, gate_gr3_report
    from src.sm_mapping import gate_sm1_report, gate_sm2_report, gate_sm3_report
    from src.sm_yukawa import gate_sm2_mass_report

    ap = action_principle_report(n_stability=16, seed=0)
    hs = run_locks_fixed_monte_carlo(n_samples=16, seed=0)
    sm1 = gate_sm1_report()
    sm2s = gate_sm2_report()
    sm2m = gate_sm2_mass_report(n_trials=8, seed=0, optimize=True)
    sm3 = gate_sm3_report()
    gr1 = gate_gr1_report()
    gr2 = gate_gr2_report()
    gr3 = gate_gr3_report(nx=gravity_nx, seed=0)

    gates = {
        "A-P": {"pass": ap["gate_A_P"]["pass"], "phase": "1.1"},
        "H-S": {"pass": hs["gate_H_S"]["pass"], "phase": "1.2"},
        "SM-1": {"pass": sm1["pass"], "phase": "2.1"},
        "SM-2-structure": {"pass": sm2s["pass"], "phase": "2.2"},
        "SM-2-mass": {
            "pass": sm2m["pass"],
            "grade": sm2m.get("grade"),
            "phase": "2.2",
        },
        "SM-3": {"pass": sm3["pass"], "phase": "2.3"},
        "GR-1": {"pass": gr1["pass"], "phase": "3.1-3.2"},
        "GR-2": {"pass": gr2["pass"], "phase": "3.3"},
        "GR-3": {"pass": gr3["pass"], "phase": "3.4"},
    }
    all_pass = all(g["pass"] for g in gates.values())
    return {
        "gates": gates,
        "all_pass": all_pass,
        "n_gates": len(gates),
        "n_pass": sum(1 for g in gates.values() if g["pass"]),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Phases 1–3 integration status")
    p.add_argument(
        "--run-gates",
        action="store_true",
        help="Execute gate modules (SM-2 mass uses short Optuna trials)",
    )
    p.add_argument("--gravity-nx", type=int, default=24)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    print("=== invariant_hunt integration status ===")
    locks = locks_block()
    print(
        f"  locks: W_g={locks['W_g']:.6f}, κ={locks['kappa']}, "
        f"φ_b={locks['phi_b']}"
    )
    print(
        f"  pre-merger freeze: core={locks['premerger_core_events']}  "
        f"α band=[{ALPHA_BAND[0]:.2e}, {ALPHA_BAND[1]:.2e}]"
    )

    phases = {
        "1": {
            "status": "complete",
            "content": "Action principle + holonomy/gauge",
            "gates": ["A-P", "H-S"],
            "docs": [
                "docs/MILESTONE_ACTION_PRINCIPLE.md",
                "docs/MILESTONE_GAUGED_META_SWEEP.md",
                "docs/MILESTONE_RELATIVISTIC_COMPLETION.md",
            ],
        },
        "2": {
            "status": "complete",
            "content": "SM representations, Yukawa, RG",
            "gates": ["SM-1", "SM-2", "SM-3"],
            "docs": [
                "docs/MILESTONE_SM_PARTICLE_MAPPING.md",
                "docs/MILESTONE_SM_YUKAWA.md",
                "docs/MILESTONE_SM_RG.md",
            ],
        },
        "3": {
            "status": "complete",
            "content": "Emergent gravity + SI bridge + lattice metric PDE",
            "gates": ["GR-1", "GR-2", "GR-3"],
            "docs": [
                "docs/GRAVITY_EMERGENCE.md",
                "docs/MILESTONE_PHASE3_CLOSEOUT.md",
            ],
        },
    }
    for ph, info in phases.items():
        print(f"  Phase {ph}: {info['status']} — {info['content']}")

    print(
        "\n  Predictive test (unchanged):\n"
        "    python scripts/premerger_core_predict.py\n"
        "    python scripts/premerger_core_predict.py --predict-event <NEW_BBH>"
    )

    gate_block = None
    if args.run_gates:
        print("\n--- Running gates ---")
        gate_block = run_gates(gravity_nx=args.gravity_nx)
        for name, g in gate_block["gates"].items():
            extra = f"  grade={g['grade']}" if "grade" in g else ""
            print(f"  {name}: {'PASS' if g['pass'] else 'FAIL'}{extra}")
        print(
            f"\n  Summary: {gate_block['n_pass']}/{gate_block['n_gates']} PASS  "
            f"all_pass={gate_block['all_pass']}"
        )

    payload = {
        "schema": "invariant_hunt.integration_status.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "locks": locks,
        "phases": phases,
        "standing": (
            "Provisional unified scaffolding (SM + gravity) under locked core. "
            "No full unification claim. Pre-merger freeze active."
        ),
        "gates": gate_block,
        "closeout_doc": "docs/MILESTONE_PHASE3_CLOSEOUT.md",
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"integration_status_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "integration_status_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    if gate_block is not None and not gate_block["all_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
