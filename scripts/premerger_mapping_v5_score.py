#!/usr/bin/env python3
"""
Execute pre-registered pre-merger mapping v5 (Hopf-lattice geometric Λ).

  Θ_link = 2π W_g / (2 W_g + 1)
  Λ = (Θ_link / π) · (M_f,ref / M_f)
  τ_v5 = τ_0 · Λ
  r ≈ α_0 · τ_v5

Locks frozen. Closed v1–v4 families not reopened. GW151012 systematics only.
See docs/PREREG_PREMERGER_MAPPING_V5.md.

Usage:
  python scripts/premerger_mapping_v5_score.py
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.invariants import (  # noqa: E402
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
)
from src.premerger_mapping_v4 import M_F_REF, REMNANT_MASS_CATALOG  # noqa: E402
from src.premerger_mapping_v5 import (  # noqa: E402
    evaluate_v5_campaign,
    predict_honesty_v5,
    score_event_v5,
    theta_link_locked,
)

OUTPUT_DIR = project_root / "outputs" / "mapping_v5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_EVENTS = [
    "GW150914",
    "GW170814",
    "GW170809",
    "GW151012",
    "GW170729",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Score pre-registered mapping v5")
    p.add_argument("--events", default=",".join(DEFAULT_EVENTS))
    p.add_argument(
        "--control",
        action="store_true",
        help="Event-independent Λ_ctrl = Θ_link/π (not SUCCESS path)",
    )
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    names = [e.strip() for e in args.events.split(",") if e.strip()]
    th_l = theta_link_locked(LOCKED_WG)
    print("=== Pre-merger mapping v5 score (Hopf-lattice Λ) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  Θ_link={th_l:.6f}  Θ_link/π={th_l/3.141592653589793:.6f}")
    if args.control:
        print("  form: Λ = Θ_link/π  (CONTROL — event-independent)")
    else:
        print(
            f"  form: Λ = (Θ_link/π)·(M_f,ref/M_f)  "
            f"M_f,ref={M_F_REF}  [PRIMARY]"
        )
    print("  prereg: docs/PREREG_PREMERGER_MAPPING_V5.md")
    print("  catalog M_f:", REMNANT_MASS_CATALOG)
    print("  v1–v4 families remain closed; GW151012 not design anchor")

    honesty = predict_honesty_v5()
    print("\n--- Pre-run honesty (Hopf Λ may fail Unify) ---")
    print(f"  Θ_link={honesty['theta_link']:.6f}  Λ_0={honesty['lambda_0']:.6f}")
    print(f"  Λ_809={honesty['lambda_809']:.4f}  Λ_914={honesty['lambda_914']:.4f}")
    print(
        f"  β ratio if shared α_0: {honesty['beta_ratio_if_shared_alpha0']:.3f}"
    )
    print(f"  empirical v1 α ratio 809/914: {honesty['empirical_alpha_ratio_v1']:.3f}")
    print(f"  {honesty['note']}")

    results: dict = {}
    rows: list[Any] = []
    for name in names:
        print(f"\n--- {name} ---")
        try:
            fit = score_event_v5(
                name,
                project_root=project_root,
                control=args.control,
                approximant=args.approximant,
            )
            results[name] = fit
            rows.append(fit.to_dict())
            print(
                f"  M_f={fit.m_f_solar:.2f}  Λ={fit.scale_factor:.4f}  "
                f"(Λ_0={fit.lambda_0:.4f})"
            )
            print(
                f"  α_0={fit.alpha_0_hat:.6e}±{fit.alpha_0_sigma:.3e}  "
                f"β_eff={fit.beta_eff:.6e}"
            )
            print(
                f"  Δχ²={fit.delta_chi2:.2f}  lnB={fit.ln_B_10:.2f}  "
                f"({fit.kass_raftery})"
            )
            print(
                f"  Gate P-v5={'PASS' if fit.gate_p_v5_pass else 'fail'}  "
                f"v1 α={fit.alpha_v1_hat}  v1 GateP={fit.gate_p_v1_pass}"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            rows.append({"event": name, "error": str(exc)})

    campaign = evaluate_v5_campaign(
        {k: v for k, v in results.items() if not isinstance(v, dict)}
    )
    print("\n" + "=" * 70)
    print(f"CAMPAIGN VERDICT: {campaign['verdict']}")
    print(f"  {campaign['reason']}")
    for n in campaign.get("notes", []):
        print(f"  · {n}")
    if campaign.get("hopf_lambda_family_closed"):
        print("  → Hopf-lattice geometric scaling family CLOSED under this pre-reg")
    print("=" * 70)

    payload = {
        "schema": "invariant_hunt.premerger_mapping_v5.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V5.md",
        "control_mode": args.control,
        "m_f_ref_solar": M_F_REF,
        "remnant_mass_catalog": REMNANT_MASS_CATALOG,
        "theta_link": th_l,
        "lambda_0": th_l / math.pi,
        "locks": {
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "honesty_pre_run": honesty,
        "results": rows,
        "campaign": campaign,
        "discipline": {
            "v1_band_not_refit": True,
            "locks_frozen": True,
            "v1_to_v4_families_still_closed": True,
            "gw151012_not_design_anchor": True,
            "lambda_formula_frozen_in_prereg": True,
            "formula": "Λ = (Θ_link/π)·(M_f,ref/M_f)",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"mapping_v5_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "mapping_v5_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
