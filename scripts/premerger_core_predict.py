#!/usr/bin/env python3
"""
Lock pre-merger core (GW150914 + GW170814) and emit forward predictions.

From the two clean anchors, define a universal α band and pre-register
success/fail criteria for the next qualifying BBH.

Usage:
  python scripts/premerger_core_predict.py
  python scripts/premerger_core_predict.py --predict-event GW170823
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gw_events import get_event  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    prepare_premerger_network,
)
from src.premerger_theory import GATE_P_DELTA_CHI2, PremergerPhaseModel  # noqa: E402

# Locked after GW170608 scrutiny (MILESTONE_GW170608_SCRUTINY.md)
CORE_EVENTS = ("GW150914", "GW170814")
# Empirically measured network α (IMRPhenomD medians)
CORE_ALPHA = {
    "GW150914": 6.928e-5,
    "GW170814": 7.451e-5,
}


def main() -> None:
    p = argparse.ArgumentParser(description="Core α band + forward prediction")
    p.add_argument("--core", default=",".join(CORE_EVENTS))
    p.add_argument(
        "--predict-event",
        default="",
        help="Optional held-out / new event to score against core band",
    )
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--n-sigma-band", type=float, default=3.0)
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    core_names = [e.strip() for e in args.core.split(",") if e.strip()]
    alphas = [CORE_ALPHA[n] for n in core_names if n in CORE_ALPHA]
    # If predicting, also measure live for core if missing
    inv = InvariantSet()
    measured = {}
    for name in core_names:
        if name in CORE_ALPHA:
            measured[name] = {
                "alpha_hat": CORE_ALPHA[name],
                "source": "cached_median_PE",
            }
            continue
        event, dets = prepare_premerger_network(
            name,
            ["H1", "L1"],
            project_root=project_root,
            approximant=args.approximant,
        )
        fit = fit_premerger_phase_network(dets, event, inv=inv)
        measured[name] = {
            "alpha_hat": fit.alpha_hat,
            "alpha_sigma": fit.alpha_sigma,
            "delta_chi2": fit.delta_chi2,
            "gate_p_pass": fit.gate_p_pass,
            "source": "live_fit",
        }
        alphas.append(fit.alpha_hat)

    a = np.array(alphas, dtype=float)
    a_mean = float(np.mean(a))
    a_std = float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
    # Use max(sample std, 20% of mean) as conservative width
    a_width = max(a_std, 0.20 * abs(a_mean))
    lo = a_mean - args.n_sigma_band * a_width
    hi = a_mean + args.n_sigma_band * a_width

    model = PremergerPhaseModel.from_invariants(inv)

    print("=" * 70)
    print("PRE-MERGER CORE LOCK + FORWARD PREDICTION")
    print(f"  Core events: {core_names}")
    print(f"  Template: Δφ = α · W_g · Φ_orb · cos(φ_b)")
    print(f"  K = W_g cos(φ_b) = {model.coupling_kernel():.4f}")
    print("-" * 70)
    for n, m in measured.items():
        print(f"  {n}: α = {m['alpha_hat']:.3e}  ({m['source']})")
    print(f"  mean α = {a_mean:.3e}  sample_std = {a_std:.3e}")
    print(
        f"  Prediction band ({args.n_sigma_band}×width): "
        f"[{lo:.3e}, {hi:.3e}]"
    )
    print("-" * 70)
    print("Pre-registered criteria for next qualifying BBH:")
    print("  Quality cuts: H1+L1 present; network Gate P rules;")
    print("    both detectors same sign if both >2σ; IMRPhenomD median PE.")
    print(
        f"  SUCCESS: Gate P PASS and α_hat ∈ [{lo:.2e}, {hi:.2e}] "
        f"(same sign as core, +)"
    )
    print(
        f"  FALSIFY: Gate P PASS with |α_hat| > 0 and α_hat outside band "
        f"at >{args.n_sigma_band}σ of core width, OR Gate P PASS with "
        f"negative α at >3σ_α."
    )
    print(
        "  NULL (not falsifying): Gate P fail (sign inconsistency or weak α) "
        "— same as current non-core events."
    )
    print("=" * 70)

    pred_result = None
    if args.predict_event:
        name = args.predict_event
        print(f"\n--- Score held-out / new event: {name} ---")
        event, dets = prepare_premerger_network(
            name,
            ["H1", "L1"],
            project_root=project_root,
            approximant=args.approximant,
        )
        fit = fit_premerger_phase_network(dets, event, inv=inv)
        a_hat = fit.alpha_hat
        in_band = lo <= a_hat <= hi
        same_sign = a_hat > 0
        if fit.gate_p_pass and in_band and same_sign:
            verdict = "SUCCESS (matches core prediction)"
        elif fit.gate_p_pass and (not in_band or not same_sign):
            verdict = "FALSIFY / revise (Gate P pass outside band or wrong sign)"
        else:
            verdict = "NULL (Gate P fail — not a core-quality event)"
        print(
            f"  α={a_hat:.3e}±{fit.alpha_sigma:.3e}  Δχ²={fit.delta_chi2:.2f}  "
            f"Gate P={'PASS' if fit.gate_p_pass else 'fail'}"
        )
        print(f"  in_band={in_band}  verdict: {verdict}")
        pred_result = {
            "event": name,
            "alpha_hat": a_hat,
            "alpha_sigma": fit.alpha_sigma,
            "delta_chi2": fit.delta_chi2,
            "gate_p_pass": bool(fit.gate_p_pass),
            "in_band": bool(in_band),
            "verdict": verdict,
        }

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "predictions" / "premerger_core_prediction.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_core_predict.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "core_events": core_names,
        "measured": measured,
        "alpha_mean": a_mean,
        "alpha_std": a_std,
        "alpha_width": a_width,
        "prediction_band": [lo, hi],
        "n_sigma_band": args.n_sigma_band,
        "formula": "Δφ = α · W_g · Φ_orb · cos(φ_b)",
        "locks": model.to_dict(),
        "demoted": {
            "GW170608": "high corr(r,τ) + approximant Δχ² swing + mass sign flip",
            "GW170818": "PE draws only 4/8",
        },
        "held_out": pred_result,
        "falsify_if": (
            f"Next Gate-P-passing BBH with α outside [{lo:.2e}, {hi:.2e}] "
            f"or significantly negative → revise pre-merger mapping "
            f"(not necessarily core locks)."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
