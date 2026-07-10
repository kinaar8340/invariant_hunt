#!/usr/bin/env python3
"""
Evaluate analytic Hopf/flux echo expectations for catalog events.

Answers: given locked invariants + observer sync, should echo-like GW
signatures be detectable in LIGO BBH residuals?

Usage:
  python scripts/evaluate_echo_expectation.py
  python scripts/evaluate_echo_expectation.py --events GW150914,GW170104,GW151226
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

from src.echo_theory import (  # noqa: E402
    DEFAULT_SNR_MAIN,
    ModelParams,
    amp_ratio_sync,
    campaign_consistency_statement,
    delta_t_burst,
    expect_echoes,
    f_echo_physical_hz,
    f_lattice,
    sync_suppression_factor,
)
from src.gw_events import CATALOG  # noqa: E402
from src.invariants import LOCKED_WG  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Analytic echo expectation")
    p.add_argument(
        "--events",
        default="GW150914,GW170104,GW151226",
        help="Comma-separated catalog names",
    )
    p.add_argument("--snr-threshold", type=float, default=2.0)
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    events = [e.strip() for e in args.events.split(",") if e.strip()]
    params = ModelParams()

    print("=" * 70)
    print("ANALYTIC INVARIANT → ECHO SIGNAL (Hopf / flux model)")
    print(f"  W_g = {params.wg:.4f}  (350/π = {LOCKED_WG:.4f})")
    print(f"  κ = {params.kappa}  Δω = {params.delta_omega}  Θ̄ = {params.theta_bar}")
    print(f"  θ_crit = π(1+κ) = {params.kappa and 3.1415926535*(1+params.kappa):.4f}")
    print(f"  Δt_burst = (θ_crit−Θ̄)/Δω = {delta_t_burst(params):.1f} lattice units")
    print(f"  f_lat = Δω/W_g = {f_lattice(params):.6e}")
    print(f"  sync factor 1/(κ Δt) = {sync_suppression_factor(params):.6e}")
    print(f"  h_echo/h_main ≲ {amp_ratio_sync(params):.6e}  (with sync)")
    print("=" * 70)

    rows = []
    print(
        f"\n{'event':<12} {'M_f':>6} {'f_echo Hz':>10} {'δt₁ ms':>8} "
        f"{'SNR_main':>9} {'SNR_echo':>10} {'det?':>6}"
    )
    for name in events:
        snr_main = DEFAULT_SNR_MAIN.get(name)
        exp = expect_echoes(
            name, snr_main=snr_main, params=params, snr_threshold=args.snr_threshold
        )
        snr_e = exp.snr_echo_sync if exp.snr_echo_sync is not None else float("nan")
        det = "YES" if exp.detectable_sync_at_snr2 else "no"
        print(
            f"{exp.event:<12} {exp.mass_final_solar:6.1f} {exp.f_echo_hz:10.2f} "
            f"{exp.geometric_delay_n1_ms:8.3f} "
            f"{(exp.snr_main or 0):9.1f} {snr_e:10.3e} {det:>6}"
        )
        rows.append(exp.to_dict())

    print("\n" + "-" * 70)
    print("Detectability (observer-sync branch):")
    n_det = sum(1 for r in rows if r["detectable_sync_at_snr2"])
    print(f"  Events with SNR_echo ≥ {args.snr_threshold}: {n_det}/{len(rows)}")
    print("\nConsistency with empirical campaign:")
    print(" ", campaign_consistency_statement())
    print("-" * 70)

    # Mass scale where sync-suppressed echoes reach thr for fixed SNR_main=25
    # SNR_echo = SNR_main * A0 / (κ Δt)  independent of mass in this amplitude model
    # Frequency does scale with mass
    print("\nFrequency vs mass (analytic f_phys ∝ 1/M):")
    for m in (5.0, 20.0, 30.0, 60.0, 100.0):
        print(f"  M={m:6.1f} M_sun  f_echo ≈ {f_echo_physical_hz(m, params):8.2f} Hz")

    print("\nImplications for gated search design:")
    print("  1. Do NOT expect Gate C strict passes from O(1) relative echo templates.")
    print("  2. Primary paper search target is a *frequency* template f_burst(M),")
    print("     with amplitude ≲ few×10⁻⁶ of ringdown — needs matched filtering,")
    print("     not residual ladder fits at a_inj ~ 0.1–1.")
    print("  3. Campaign nulls support the sync-suppressed branch of the theory.")
    print("=" * 70)

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "predictions" / "echo_expectation_analytic.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.echo_expectation.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model": params.to_dict(),
        "formulas": {
            "theta_crit": "π(1+κ)",
            "delta_t_burst": "(θ_crit − Θ̄)/Δω",
            "f_lattice": "Δω/W_g",
            "f_phys": "(Δω/W_g) / (GM/c³)",
            "sync_suppression": "1/(κ Δt_burst)",
            "amp_ratio_sync": "A0/(κ Δt_burst)",
            "note_units": (
                "f_phys uses c³/GM geometric time (paper text writes c²/GM; "
                "corrected for dimensional consistency)."
            ),
        },
        "events": rows,
        "campaign_consistency": campaign_consistency_statement(),
        "default_snr_main": DEFAULT_SNR_MAIN,
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
