#!/usr/bin/env python3
"""
Pre-merger Bayes factor: (GR + topological α) vs pure GR.

Pre-registered Gaussian prior α ~ N(0, σ_p²) with σ_p = 1e-3.
Locks W_g, κ, φ_b fixed. Does not re-fit demoted α band.

Usage:
  python scripts/premerger_bayes_factor.py --event GW150914
  python scripts/premerger_bayes_factor.py --events GW170809,GW170729,GW151012
  python scripts/premerger_bayes_factor.py --event GW150914 --calibrate
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
from src.premerger_bayes import (  # noqa: E402
    ALPHA_PRIOR_SIGMA,
    bayes_factor_for_event,
    bayes_factor_network,
    injection_bayes_calibration,
)
from src.premerger_phase import prepare_premerger_network  # noqa: E402

OUTPUT_DIR = project_root / "outputs" / "bayes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Pre-merger topo vs GR Bayes factor")
    p.add_argument("--event", type=str, default="")
    p.add_argument(
        "--events",
        type=str,
        default="",
        help="Comma-separated events (overrides --event)",
    )
    p.add_argument("--prior-sigma", type=float, default=ALPHA_PRIOR_SIGMA)
    p.add_argument("--approximant", type=str, default="IMRPhenomD")
    p.add_argument(
        "--calibrate",
        action="store_true",
        help="White-noise injection calibration (α=0 and α=1e-4)",
    )
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    if args.events:
        names = [e.strip() for e in args.events.split(",") if e.strip()]
    elif args.event:
        names = [args.event.strip()]
    else:
        names = ["GW150914"]

    print("=== Pre-merger Bayes factor B_10 = Z(topo)/Z(GR) ===")
    print(f"  locks: W_g={LOCKED_WG:.6f}, κ={DEFAULT_KAPPA}, φ_b={DEFAULT_BRAIDING}")
    print(f"  prior: α ~ N(0, {args.prior_sigma:.3e}²)  [pre-registered]")
    print("  H0 = pure GR residual | H1 = GR + α·τ (locked template)")
    print("  Band not re-fit (demoted universal claim stays demoted)")

    results = []
    for name in names:
        print(f"\n--- {name} ---")
        try:
            bf = bayes_factor_for_event(
                name,
                project_root=project_root,
                alpha_prior_sigma=args.prior_sigma,
                approximant=args.approximant,
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append({"event": name, "error": str(exc)})
            continue
        d = bf.to_dict()
        results.append(d)
        print(f"  α_MLE = {bf.alpha_hat_mle:.6e} ± {bf.alpha_sigma_mle:.3e}")
        print(f"  α_MAP = {bf.alpha_hat_map:.6e} ± {bf.alpha_sigma_post:.3e}")
        print(f"  Δχ²   = {bf.delta_chi2:.4f}")
        print(f"  ln B_10 = {bf.ln_B_10:.4f}   B_10 = {bf.B_10:.6g}")
        print(f"  BIC ln B ≈ {bf.ln_B_10_bic:.4f}   SD ln B = {bf.ln_B_10_savage_dickey:.4f}")
        print(f"  Kass–Raftery: {bf.kass_raftery}")
        print(f"  Gate P (legacy): {bf.gate_p_pass}")

        if args.calibrate:
            event, dets = prepare_premerger_network(
                name,
                ["H1", "L1"],
                project_root=project_root,
                approximant=args.approximant,
            )
            print("  calibration (white noise):")
            for a_inj in (0.0, 1e-4, 5e-4):
                cal = injection_bayes_calibration(
                    dets,
                    event,
                    alpha_inj=a_inj,
                    alpha_prior_sigma=args.prior_sigma,
                    seed=42,
                )
                print(
                    f"    α_inj={a_inj:.1e} → α_hat={cal['alpha_hat_mle']:.3e}  "
                    f"lnB={cal['ln_B_10']:.3f}  ({cal['kass_raftery']})"
                )
            d["calibration"] = [
                injection_bayes_calibration(
                    dets, event, alpha_inj=a, alpha_prior_sigma=args.prior_sigma, seed=42
                )
                for a in (0.0, 1e-4, 5e-4)
            ]

    payload = {
        "schema": "invariant_hunt.premerger_bayes.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "alpha_prior_sigma": args.prior_sigma,
        "locks": {
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "models": {
            "H0": "pure GR residual (PE subtracted)",
            "H1": "GR + α·τ, τ=−K Φ_orb H[h], K=W_g cos φ_b",
        },
        "discipline": {
            "band_not_refit": True,
            "locks_frozen": True,
            "complements_delta_chi2": True,
        },
        "results": results,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = args.out or (OUTPUT_DIR / f"premerger_bayes_{ts}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out.write_text(text)
    latest = OUTPUT_DIR / "premerger_bayes_latest.json"
    latest.write_text(text)
    print(f"\n  wrote {out}")
    print(f"  wrote {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
