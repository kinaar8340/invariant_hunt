#!/usr/bin/env python3
"""
Phase 2 gate runner: SM-1, SM-2 (structure and/or mass), SM-3.

Usage:
  python scripts/sm_gate_check.py
  python scripts/sm_gate_check.py --gates SM-1
  python scripts/sm_gate_check.py --gates SM-1,SM-2,SM-3 --yukawa --trials 48
  python scripts/sm_gate_check.py --gates SM-2 --yukawa --require SM-2
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

from src.sm_mapping import (  # noqa: E402
    gate_sm1_report,
    gate_sm2_report,
    gate_sm3_report,
    sm_full_report,
)
from src.sm_yukawa import gate_sm2_mass_report  # noqa: E402

OUTPUT_DIR = project_root / "outputs" / "sm_mapping"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 2 SM gate checks")
    p.add_argument(
        "--gates",
        type=str,
        default="SM-1,SM-2,SM-3",
        help="Comma-separated gates: SM-1, SM-2, SM-3",
    )
    p.add_argument("--out", type=Path, default=None)
    p.add_argument(
        "--require",
        type=str,
        default="SM-1",
        help="Comma-separated gates that must pass for exit 0 (default SM-1)",
    )
    p.add_argument(
        "--yukawa",
        action="store_true",
        help="Upgrade SM-2 to mass/mixing χ² (Phase 2.2)",
    )
    p.add_argument("--trials", type=int, default=48, help="Yukawa Optuna trials")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    want = {g.strip().upper() for g in args.gates.split(",") if g.strip()}
    require = {g.strip().upper() for g in args.require.split(",") if g.strip()}

    print("=== Phase 2 SM gate check ===")
    results: dict[str, dict] = {}

    if "SM-1" in want:
        r = gate_sm1_report()
        results["SM-1"] = r
        print(f"\nGate SM-1 (representations): {'PASS' if r['pass'] else 'FAIL'}")
        for k, v in r["criteria"].items():
            print(f"  {k}: {v}")

    if "SM-2" in want:
        if args.yukawa:
            print(f"\nGate SM-2 mass/mixing (trials={args.trials}) …")
            r = gate_sm2_mass_report(
                n_trials=args.trials, seed=args.seed, optimize=True
            )
            results["SM-2"] = r
            print(
                f"Gate SM-2 (Yukawa/mass): {'PASS' if r['pass'] else 'FAIL'}  "
                f"grade={r['grade']}"
            )
            for k, v in r["criteria"].items():
                print(f"  {k}: {v}")
            print(f"  χ²_mass/dof={r['chi2_mass']['chi2_per_dof']:.4f}")
            print(f"  χ²_CKM/dof={r['chi2_ckm']['chi2_per_dof']:.4f}")
        else:
            r = gate_sm2_report()
            results["SM-2"] = r
            print(
                f"\nGate SM-2 (3 gen structure scaffold): "
                f"{'PASS' if r['pass'] else 'FAIL'}"
            )
            print(f"  note: {r['note']}")
            print("  tip: pass --yukawa for Phase 2.2 mass/mixing upgrade")
            if r["structure"].get("errors"):
                for e in r["structure"]["errors"]:
                    print(f"  error: {e}")

    if "SM-3" in want:
        r = gate_sm3_report()
        results["SM-3"] = r
        print(f"\nGate SM-3 (anomaly + RG): {'PASS' if r['pass'] else 'FAIL'}")
        print(f"  note: {r['note']}")
        for g in r["anomaly"]["generations"]:
            print(f"  gen {g['generation']}: pass={g['pass']} traces={g['traces']}")
        rg = r.get("rg_flow", {})
        print(f"  rg_implemented: {rg.get('implemented')}  rg_pass: {rg.get('pass')}")
        if rg.get("detail"):
            for k, v in rg["detail"].items():
                print(f"    rg.{k}: {v}")

    bundle = {
        "schema": "invariant_hunt.sm_gate_check.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "gates_requested": sorted(want),
        "gates_required": sorted(require),
        "yukawa": args.yukawa,
        "results": {
            k: {
                "pass": v["pass"],
                "gate": v.get("gate"),
                "phase": v.get("phase"),
                **({"criteria": v["criteria"]} if "criteria" in v else {}),
                **({"grade": v["grade"]} if "grade" in v else {}),
            }
            for k, v in results.items()
        },
        "full": sm_full_report() if want >= {"SM-1", "SM-2", "SM-3"} and not args.yukawa else None,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"sm_gate_check_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(bundle)
    if "SM-1" in results:
        payload["SM-1_detail"] = {
            "pass": results["SM-1"]["pass"],
            "criteria": results["SM-1"]["criteria"],
            "n_fields": results["SM-1"].get("n_fields"),
        }
    if args.yukawa and "SM-2" in results:
        payload["SM-2_yukawa_detail"] = {
            "pass": results["SM-2"]["pass"],
            "grade": results["SM-2"].get("grade"),
            "chi2_mass_per_dof": results["SM-2"]["chi2_mass"]["chi2_per_dof"],
            "chi2_ckm_per_dof": results["SM-2"]["chi2_ckm"]["chi2_per_dof"],
            "masses_GeV": results["SM-2"]["spectrum"]["masses_GeV"],
            "ckm_abs": results["SM-2"]["spectrum"]["ckm_abs"],
        }
    if "SM-3" in results:
        payload["SM-3_detail"] = {
            "pass": results["SM-3"]["pass"],
            "anomaly_pass": results["SM-3"]["anomaly"]["pass"],
            "rg_flow": results["SM-3"].get("rg_flow"),
        }
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "sm_gate_check_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")

    ok = all(results[g]["pass"] for g in require if g in results)
    missing = require - set(results)
    if missing:
        print(f"  WARNING: required gates not run: {missing}")
        ok = False
    print(f"\nRequired {sorted(require)}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
