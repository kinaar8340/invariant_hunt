#!/usr/bin/env python3
"""
Execute pre-registered pre-merger mapping v2 (p=1 fixed).

  β = α_0 (M_tot / 60 M_⊙)^1
  τ_v2 = τ_0 × (M_tot/60)
  r ≈ α_0 · τ_v2

Locks frozen. Does not re-fit demoted v1 band.
See docs/PREREG_PREMERGER_MAPPING_V2.md.

Usage:
  python scripts/premerger_mapping_v2_score.py
  python scripts/premerger_mapping_v2_score.py --events GW150914,GW170814,GW170809,GW151012
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
from src.premerger_mapping_v2 import (  # noqa: E402
    MASS_POWER_DEFAULT,
    M_REF_SOLAR,
    evaluate_v2_campaign,
    predict_beta_ratio_gw170809_vs_150914,
    score_event_v2,
)

OUTPUT_DIR = project_root / "outputs" / "mapping_v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_EVENTS = [
    "GW150914",
    "GW170814",
    "GW170809",
    "GW151012",
    "GW170729",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Score pre-registered mapping v2 (p=1)")
    p.add_argument(
        "--events",
        default=",".join(DEFAULT_EVENTS),
        help="Comma-separated events",
    )
    p.add_argument("--mass-power", type=float, default=MASS_POWER_DEFAULT)
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    if abs(args.mass_power - 1.0) > 1e-12:
        print(
            "WARNING: primary pre-reg is p=1 fixed; "
            f"you set p={args.mass_power} (sensitivity only)"
        )

    names = [e.strip() for e in args.events.split(",") if e.strip()]
    print("=== Pre-merger mapping v2 score (pre-registered) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  form: β = α_0 (M_tot/{M_REF_SOLAR})^p  with p={args.mass_power}")
    print("  prereg: docs/PREREG_PREMERGER_MAPPING_V2.md")
    print("  v1 band NOT re-fit; GW151012 is systematics check only")

    honesty = predict_beta_ratio_gw170809_vs_150914(p=args.mass_power)
    print("\n--- Pre-run honesty (mass-only may fail) ---")
    print(f"  mass β ratio if shared α_0: {honesty['beta_ratio_if_shared_alpha0']:.3f}")
    print(f"  empirical v1 α ratio 809/914: {honesty['empirical_alpha_ratio_v1']:.3f}")
    print(f"  {honesty['note']}")

    results: dict = {}
    rows = []
    for name in names:
        print(f"\n--- {name} ---")
        try:
            fit = score_event_v2(
                name,
                project_root=project_root,
                mass_power=args.mass_power,
                approximant=args.approximant,
            )
            results[name] = fit
            rows.append(fit.to_dict())
            print(f"  M_tot={fit.m_tot_solar:.2f}  scale={fit.scale_factor:.4f}")
            print(
                f"  α_0={fit.alpha_0_hat:.6e}±{fit.alpha_0_sigma:.3e}  "
                f"β_eff={fit.beta_eff:.6e}"
            )
            print(
                f"  Δχ²={fit.delta_chi2:.2f}  lnB={fit.ln_B_10:.2f}  "
                f"({fit.kass_raftery})"
            )
            print(
                f"  Gate P-v2={'PASS' if fit.gate_p_v2_pass else 'fail'}  "
                f"v1 α={fit.alpha_v1_hat}  v1 GateP={fit.gate_p_v1_pass}"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            rows.append({"event": name, "error": str(exc)})

    campaign = evaluate_v2_campaign(
        {k: v for k, v in results.items() if not isinstance(v, dict)}
    )
    print("\n" + "=" * 70)
    print(f"CAMPAIGN VERDICT: {campaign['verdict']}")
    print(f"  {campaign['reason']}")
    for n in campaign.get("notes", []):
        print(f"  · {n}")
    print("=" * 70)

    payload = {
        "schema": "invariant_hunt.premerger_mapping_v2.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V2.md",
        "mass_power": args.mass_power,
        "m_ref_solar": M_REF_SOLAR,
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
            "gw151012_not_design_anchor": True,
            "p_fixed_a_priori": abs(args.mass_power - 1.0) < 1e-12,
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"mapping_v2_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "mapping_v2_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")
    return 0 if campaign["verdict"] in ("SUCCESS", "NULL", "FALSIFY", "INCONCLUSIVE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
