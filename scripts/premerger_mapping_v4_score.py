#!/usr/bin/env python3
"""
Execute pre-registered pre-merger mapping v4 (remnant mass p=1).

  β = α_0 (M_f / M_f,ref)^1
  τ_v4 = τ_0 · (M_f / M_f,ref)

Locks frozen. Closed bulk PE families not reopened. GW151012 systematics only.
See docs/PREREG_PREMERGER_MAPPING_V4.md.

Usage:
  python scripts/premerger_mapping_v4_score.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG  # noqa: E402
from src.premerger_mapping_v4 import (  # noqa: E402
    MASS_POWER_DEFAULT,
    M_F_REF,
    REMNANT_MASS_CATALOG,
    evaluate_v4_campaign,
    predict_honesty_v4,
    score_event_v4,
)

OUTPUT_DIR = project_root / "outputs" / "mapping_v4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_EVENTS = [
    "GW150914",
    "GW170814",
    "GW170809",
    "GW151012",
    "GW170729",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Score pre-registered mapping v4")
    p.add_argument("--events", default=",".join(DEFAULT_EVENTS))
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
    print("=== Pre-merger mapping v4 score (remnant mass) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  form: β = α_0 (M_f/{M_F_REF})^p  with p={args.mass_power}")
    print("  prereg: docs/PREREG_PREMERGER_MAPPING_V4.md")
    print("  catalog M_f:", REMNANT_MASS_CATALOG)
    print("  v2/v3 bulk PE families remain closed; GW151012 not design anchor")

    honesty = predict_honesty_v4(p=args.mass_power)
    print("\n--- Pre-run honesty (remnant may fail Unify / wrong way) ---")
    print(f"  M_f 809={honesty['m_f_809']}  M_f 914={honesty['m_f_914']}")
    print(f"  remnant β ratio if shared α_0 (p={args.mass_power}): "
          f"{honesty['beta_ratio_if_shared_alpha0']:.3f}")
    print(f"  remnant p=1 / p=2: {honesty['beta_ratio_p1']:.3f} / "
          f"{honesty['beta_ratio_p2']:.3f}")
    print(f"  empirical v1 α ratio 809/914: {honesty['empirical_alpha_ratio_v1']:.3f}")
    print(f"  {honesty['note']}")

    results: dict = {}
    rows: list[Any] = []
    for name in names:
        print(f"\n--- {name} ---")
        try:
            fit = score_event_v4(
                name,
                project_root=project_root,
                mass_power=args.mass_power,
                approximant=args.approximant,
            )
            results[name] = fit
            rows.append(fit.to_dict())
            print(f"  M_f={fit.m_f_solar:.2f}  S={fit.scale_factor:.4f}")
            print(
                f"  α_0={fit.alpha_0_hat:.6e}±{fit.alpha_0_sigma:.3e}  "
                f"β_eff={fit.beta_eff:.6e}"
            )
            print(
                f"  Δχ²={fit.delta_chi2:.2f}  lnB={fit.ln_B_10:.2f}  "
                f"({fit.kass_raftery})"
            )
            print(
                f"  Gate P-v4={'PASS' if fit.gate_p_v4_pass else 'fail'}  "
                f"v1 α={fit.alpha_v1_hat}  v1 GateP={fit.gate_p_v1_pass}"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            rows.append({"event": name, "error": str(exc)})

    campaign = evaluate_v4_campaign(
        {k: v for k, v in results.items() if not isinstance(v, dict)}
    )
    print("\n" + "=" * 70)
    print(f"CAMPAIGN VERDICT: {campaign['verdict']}")
    print(f"  {campaign['reason']}")
    for n in campaign.get("notes", []):
        print(f"  · {n}")
    if campaign.get("remnant_mass_family_closed"):
        print("  → remnant-mass scaling family CLOSED under this pre-reg")
    print("=" * 70)

    payload = {
        "schema": "invariant_hunt.premerger_mapping_v4.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V4.md",
        "mass_power": args.mass_power,
        "m_f_ref_solar": M_F_REF,
        "remnant_mass_catalog": REMNANT_MASS_CATALOG,
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
            "v2_v3_bulk_pe_still_closed": True,
            "gw151012_not_design_anchor": True,
            "p_fixed_a_priori": abs(args.mass_power - 1.0) < 1e-12,
            "catalog_m_f_source": "src/gw_events.py PublicGWEvent.mass_final_solar",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"mapping_v4_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "mapping_v4_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
