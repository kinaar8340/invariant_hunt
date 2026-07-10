#!/usr/bin/env python3
"""
Execute pre-registered pre-merger mapping v3.

Primary P-v3a:  β = α_0 (ρ_ref / ρ_net)^1   (inverse SNR, q=1 fixed)
Secondary P-v3b: β = α_0 (d_L / d_ref)^1    (distance, s=1) if P-v3a fails

Locks frozen. Mass scaling closed. GW151012 systematics only.
See docs/PREREG_PREMERGER_MAPPING_V3.md.

Usage:
  python scripts/premerger_mapping_v3_score.py
  python scripts/premerger_mapping_v3_score.py --mode inv_snr
  python scripts/premerger_mapping_v3_score.py --mode both   # a then b if a fails
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
from src.premerger_mapping_v3 import (  # noqa: E402
    DISTANCE_POWER_DEFAULT,
    INV_SNR_POWER_DEFAULT,
    NETWORK_SNR_GWTC1,
    RHO_REF,
    evaluate_v3_campaign,
    evaluate_v3_family,
    predict_honesty_v3,
    score_event_v3,
)

OUTPUT_DIR = project_root / "outputs" / "mapping_v3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_EVENTS = [
    "GW150914",
    "GW170814",
    "GW170809",
    "GW151012",
    "GW170729",
]


def _score_family(
    names: list[str],
    *,
    scale_mode: str,
    scale_power: float,
    approximant: str,
) -> tuple[dict, list, dict]:
    results: dict = {}
    rows = []
    print(f"\n=== Family: {scale_mode} power={scale_power} ===")
    for name in names:
        print(f"\n--- {name} ---")
        try:
            fit = score_event_v3(
                name,
                project_root=project_root,
                scale_mode=scale_mode,  # type: ignore[arg-type]
                scale_power=scale_power,
                approximant=approximant,
            )
            results[name] = fit
            rows.append(fit.to_dict())
            print(
                f"  scale_value={fit.scale_value:.4g}  ref={fit.scale_ref:.4g}  "
                f"S={fit.scale_factor:.4f}"
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
                f"  Gate P-v3={'PASS' if fit.gate_p_v3_pass else 'fail'}  "
                f"v1 α={fit.alpha_v1_hat}  v1 GateP={fit.gate_p_v1_pass}"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            rows.append({"event": name, "error": str(exc)})

    campaign = evaluate_v3_campaign(
        {k: v for k, v in results.items()},
        scale_mode=scale_mode,  # type: ignore[arg-type]
        scale_power=scale_power,
    )
    print("\n" + "-" * 70)
    print(f"  VERDICT ({scale_mode}): {campaign['verdict']}")
    print(f"  {campaign['reason']}")
    for n in campaign.get("notes", []):
        print(f"  · {n}")
    print("-" * 70)
    return results, rows, campaign


def main() -> int:
    p = argparse.ArgumentParser(description="Score pre-registered mapping v3")
    p.add_argument(
        "--events",
        default=",".join(DEFAULT_EVENTS),
        help="Comma-separated events",
    )
    p.add_argument(
        "--mode",
        choices=("inv_snr", "distance", "both"),
        default="both",
        help="P-v3a inv_snr, P-v3b distance, or both (b only if a fails)",
    )
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument(
        "--force-distance",
        action="store_true",
        help="Run distance family even if inv_snr SUCCESS",
    )
    args = p.parse_args()

    names = [e.strip() for e in args.events.split(",") if e.strip()]
    print("=== Pre-merger mapping v3 score (pre-registered) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  prereg: docs/PREREG_PREMERGER_MAPPING_V3.md")
    print(f"  ρ_ref={RHO_REF}  frozen SNR table: {NETWORK_SNR_GWTC1}")
    print("  mass scaling CLOSED (v2 FALSIFY); GW151012 not design anchor")

    honesty = predict_honesty_v3()
    print("\n--- Pre-run honesty (mild powers may fail Unify) ---")
    print(f"  empirical v1 α ratio 809/914: {honesty['empirical_alpha_ratio_v1']:.3f}")
    print(f"  inv-SNR q=1 pred ratio: {honesty['inv_snr_q1_ratio']:.3f}")
    print(f"  inv-SNR q=2 pred ratio: {honesty['inv_snr_q2_ratio']:.3f} (sensitivity only)")
    print(f"  distance s=1 pred ratio: {honesty['distance_s1_ratio']:.3f}")
    print(f"  distance s=2 pred ratio: {honesty['distance_s2_ratio']:.3f} (sensitivity only)")
    print(
        f"  distance s=3 (NOT registered): "
        f"{honesty['distance_s3_ratio_not_registered']:.3f}"
    )
    print(f"  {honesty['note']}")

    payload_results: dict[str, Any] = {}
    camp_a = None
    camp_b = None

    run_a = args.mode in ("inv_snr", "both")
    run_b = args.mode == "distance"

    if run_a:
        _res_a, rows_a, camp_a = _score_family(
            names,
            scale_mode="inv_snr",
            scale_power=INV_SNR_POWER_DEFAULT,
            approximant=args.approximant,
        )
        payload_results["inv_snr"] = {
            "scale_power": INV_SNR_POWER_DEFAULT,
            "results": rows_a,
            "campaign": camp_a,
        }
        if args.mode == "both":
            if camp_a["verdict"] != "SUCCESS" or args.force_distance:
                run_b = True
            else:
                print("\n  P-v3a SUCCESS — skipping P-v3b (use --force-distance to run)")

    if run_b:
        _res_b, rows_b, camp_b = _score_family(
            names,
            scale_mode="distance",
            scale_power=DISTANCE_POWER_DEFAULT,
            approximant=args.approximant,
        )
        payload_results["distance"] = {
            "scale_power": DISTANCE_POWER_DEFAULT,
            "results": rows_b,
            "campaign": camp_b,
        }

    if camp_a is None and camp_b is not None:
        family = {
            "family_verdict": camp_b["verdict"],
            "reason": f"P-v3b only: {camp_b['reason']}",
            "p_v3a": None,
            "p_v3b": camp_b,
            "bulk_pe_power_family_closed": False,
        }
    elif camp_a is not None:
        family = evaluate_v3_family(camp_a, camp_b)
    else:
        family = {
            "family_verdict": "INCONCLUSIVE",
            "reason": "No family scored",
            "bulk_pe_power_family_closed": False,
        }

    print("\n" + "=" * 70)
    print(f"FAMILY VERDICT: {family['family_verdict']}")
    print(f"  {family['reason']}")
    if family.get("bulk_pe_power_family_closed"):
        print("  → bulk PE-power mapping family CLOSED under this pre-reg")
    print("=" * 70)

    payload = {
        "schema": "invariant_hunt.premerger_mapping_v3.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V3.md",
        "locks": {
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "rho_ref": RHO_REF,
        "network_snr_table": NETWORK_SNR_GWTC1,
        "honesty_pre_run": honesty,
        "families": payload_results,
        "family_campaign": family,
        "discipline": {
            "v1_band_not_refit": True,
            "locks_frozen": True,
            "mass_scaling_closed": True,
            "gw151012_not_design_anchor": True,
            "d_L_cubed_not_registered": True,
            "q_fixed_a_priori": True,
            "s_fixed_a_priori": True,
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"mapping_v3_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "mapping_v3_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
