#!/usr/bin/env python3
"""
Run lightweight CI checks (locks + schema) and optional pytest subset.

Usage:
  python scripts/ci_check.py
  python scripts/ci_check.py --pytest
  python scripts/ci_check.py --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ci_checks import run_ci_suite  # noqa: E402

# Default lightweight pytest selection (no PE / pycbc / torch data)
CI_TEST_PATHS = [
    "tests/test_ci_locks_schema.py",
    "tests/test_invariants.py",
    "tests/test_positional.py",
    "tests/test_config.py",
    "tests/test_echo_theory.py",
    "tests/test_echo_ladder.py",
    "tests/test_action_principle.py",
    "tests/test_sm_mapping.py",
    "tests/test_sm_rg.py",
    "tests/test_sm_yukawa.py",
    "tests/test_gravity_emergence.py",
    "tests/test_premerger_theory.py",
    "tests/test_premerger_bayes.py",
    "tests/test_premerger_mapping_v2.py",
    "tests/test_premerger_mapping_v3.py",
    "tests/test_premerger_mapping_v4.py",
    "tests/test_premerger_mapping_v5.py",
    "tests/test_amp_structure.py",
    "tests/test_coherent_echo.py",
    "tests/test_whiten.py",
    "tests/test_gauged_meta_sweep.py",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Lightweight CI: locks + schema")
    p.add_argument("--pytest", action="store_true", help="Also run CI pytest subset")
    p.add_argument("--json", action="store_true", help="Print CI suite JSON only")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write suite JSON to path",
    )
    args = p.parse_args()

    report = run_ci_suite()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=str))

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=== CI suite (locks + schema) ===")
        print(f"  overall: {'PASS' if report['pass'] else 'FAIL'}")
        print(f"  locks: {'PASS' if report['locks']['pass'] else 'FAIL'}")
        if report["locks"]["issues"]:
            for i in report["locks"]["issues"]:
                print(f"    · {i}")
        print(f"  schemas: {'PASS' if report['schemas']['pass'] else 'FAIL'}")
        if report["schemas"]["issues"]:
            for i in report["schemas"]["issues"]:
                print(f"    · {i}")
        print(
            f"  prediction_bundle: "
            f"{'PASS' if report['prediction_bundle']['pass'] else 'FAIL'}"
        )
        if report["prediction_bundle"]["issues"]:
            for i in report["prediction_bundle"]["issues"]:
                print(f"    · {i}")
        locks = report["locks"]["locks"]
        print(
            f"  frozen: W_g={locks['W_g']:.6f}, κ={locks['kappa']}, "
            f"φ_b={locks['phi_b']}"
        )

    rc = 0 if report["pass"] else 1

    if args.pytest:
        print("\n=== pytest CI subset ===")
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *CI_TEST_PATHS,
            "-q",
            "--tb=short",
        ]
        print(" ", " ".join(cmd))
        pr = subprocess.run(cmd, cwd=project_root)
        if pr.returncode != 0:
            rc = pr.returncode

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
