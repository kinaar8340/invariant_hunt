#!/usr/bin/env python3
"""
Pre-merger topological phase scan (Gate P).

Template:
  Δφ(t) = α · W_g · Φ_orb(t) · cos(φ_b)

Locks fixed; fit α on whitened inspiral residual after PE IMR subtraction.

Usage:
  python scripts/premerger_phase_scan.py --event GW150914 --plot
  python scripts/premerger_phase_scan.py --events GW150914,GW170104,GW151226
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

from src.invariants import InvariantSet  # noqa: E402
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    fit_premerger_phase_single,
    prepare_premerger_network,
)
from src.premerger_theory import (  # noqa: E402
    GATE_P_DELTA_CHI2,
    GATE_P_T_END,
    premerger_predictions,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Pre-merger topological phase Gate P")
    p.add_argument("--event", default="", help="Single event (or use --events)")
    p.add_argument(
        "--events",
        default="",
        help="Comma-separated events for multi-event summary",
    )
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--duration-pre", type=float, default=4.0)
    p.add_argument("--t-end", type=float, default=GATE_P_T_END)
    p.add_argument("--f-low", type=float, default=20.0)
    p.add_argument("--f-high", type=float, default=100.0)
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    if args.events:
        event_names = [e.strip() for e in args.events.split(",") if e.strip()]
    elif args.event:
        event_names = [args.event]
    else:
        event_names = ["GW150914"]

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()
    results = []

    print("=" * 70)
    print("PRE-MERGER TOPOLOGICAL PHASE (Gate P)")
    print("  Δφ = α · W_g · Φ_orb · cos(φ_b)   locks fixed, α free")
    print(f"  inspiral: t < {args.t_end} s, band [{args.f_low}, {args.f_high}] Hz")
    print(f"  Gate P: Δχ² ≥ {args.gate_dchi2} and |α| > 2σ")
    print("=" * 70)

    for name in event_names:
        print(f"\n--- {name} ---")
        pred = premerger_predictions(
            # mass from catalog after load
            60.0,
            alpha=1e-4,
            model=None,
        )
        event, dets = prepare_premerger_network(
            name,
            detectors,
            project_root=project_root,
            duration_pre_s=args.duration_pre,
            duration_post_s=0.05,
            f_low=args.f_low,
            f_high=args.f_high,
        )
        pred = premerger_predictions(event.mass_final_solar, alpha=1e-4)
        print(
            f"  M_f={event.mass_final_solar}  "
            f"K=W_g cos(φ_b)={inv.wg * np.cos(inv.braiding_target*2*np.pi):.3f}  "
            f"pre={args.duration_pre}s"
        )
        for d in dets:
            print(f"  {d.detector}: PE SNR≈{d.pe_snr_proxy:.1f}")

        # per-detector
        per_det = []
        for d in dets:
            fit = fit_premerger_phase_single(
                d,
                event,
                t_end=args.t_end,
                f_low=args.f_low,
                f_high=args.f_high,
                gate_dchi2=args.gate_dchi2,
                inv=inv,
            )
            per_det.append(fit.to_dict())
            print(
                f"  {d.detector}: α={fit.alpha_hat:.3e}±{fit.alpha_sigma:.3e}  "
                f"Δχ²={fit.delta_chi2:.3f}  Gate P={'PASS' if fit.gate_p_pass else 'fail'}"
            )

        # network shared α
        net = fit_premerger_phase_network(
            dets,
            event,
            t_end=args.t_end,
            f_low=args.f_low,
            f_high=args.f_high,
            gate_dchi2=args.gate_dchi2,
            inv=inv,
        )
        print(
            f"  NETWORK: α={net.alpha_hat:.3e}±{net.alpha_sigma:.3e}  "
            f"Δχ²={net.delta_chi2:.3f}  Gate P={'PASS' if net.gate_p_pass else 'fail'}"
        )
        for n in net.notes:
            print(f"    · {n}")

        results.append(
            {
                "event": name,
                "mass_final": event.mass_final_solar,
                "predictions": pred,
                "per_detector": per_det,
                "network": net.to_dict(),
            }
        )

        if args.plot and len(event_names) == 1:
            try:
                import matplotlib.pyplot as plt
                from src.premerger_theory import (
                    orbital_phase_from_strain,
                    phase_basis_template,
                    PremergerPhaseModel,
                )

                d0 = dets[0]
                mask = d0.t_rel < args.t_end
                t_ms = d0.t_rel[mask] * 1e3
                model = PremergerPhaseModel.from_invariants(inv)
                phi = orbital_phase_from_strain(
                    d0.pe_template_w, d0.sample_rate, t_rel=d0.t_rel, t_ref=0.0
                )
                tau = phase_basis_template(d0.pe_template_w, phi, model)

                fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
                axes[0].plot(t_ms, d0.residual_w[mask], lw=0.6, color="0.4", label="resid")
                axes[0].plot(
                    t_ms,
                    net.alpha_hat * tau[mask],
                    lw=1.0,
                    label=f"α·τ (α={net.alpha_hat:.2e})",
                )
                axes[0].set_ylabel("whitened")
                axes[0].legend(fontsize=8)
                axes[0].set_title(
                    f"{name} pre-merger phase  Δχ²={net.delta_chi2:.2f}  "
                    f"Gate P={'PASS' if net.gate_p_pass else 'fail'}"
                )
                axes[1].plot(t_ms, phi[mask], lw=0.8)
                axes[1].set_ylabel("Φ_orb")
                axes[2].plot(t_ms, tau[mask], lw=0.8, color="C3")
                axes[2].set_ylabel("τ = ∂h/∂α")
                axes[2].set_xlabel("t − t_merger [ms]")
                fig.tight_layout()
                plot_path = (
                    project_root
                    / "outputs"
                    / "benchmarks"
                    / f"{name}_premerger_phase.png"
                )
                plot_path.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(plot_path, dpi=150)
                print(f"  Wrote {plot_path}")
            except ImportError:
                print("  matplotlib not available")

    # multi-event summary
    print("\n" + "=" * 70)
    print("GATE P SUMMARY (network shared α)")
    print(f"{'event':<12} {'α_hat':>12} {'σ_α':>12} {'Δχ²':>8} {'pass':>6}")
    n_pass = 0
    alphas_pass = []
    for r in results:
        n = r["network"]
        ok = n["gate_p_pass"]
        n_pass += int(ok)
        if ok:
            alphas_pass.append(n["alpha_hat"])
        print(
            f"{r['event']:<12} {n['alpha_hat']:12.3e} {n['alpha_sigma']:12.3e} "
            f"{n['delta_chi2']:8.3f} {'YES' if ok else 'no':>6}"
        )
    print("-" * 70)
    print(f"Gate P pass: {n_pass}/{len(results)}")
    same_sign = len(alphas_pass) >= 2 and (
        max(np.sign(alphas_pass)) * min(np.sign(alphas_pass)) > 0
    )
    gate_pd = n_pass >= 2 and same_sign
    print(
        "Multi-event Gate P-D (≥2 pass, same α sign): "
        f"{'PASS' if gate_pd else 'FAIL'}"
    )
    if n_pass >= 2 and not same_sign:
        print("  (sign mismatch across events — not coherent multi-event support)")
    print(
        "Note: Post-merger echo ladders remain constrained (sync branch). "
        "This is a new observable channel."
    )
    print("=" * 70)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / (
            f"{event_names[0]}_premerger_phase.json"
            if len(event_names) == 1
            else "premerger_phase_multi.json"
        )
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_phase.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "formula": "Δφ(t) = α · W_g · Φ_orb(t) · cos(φ_b)",
        "locks_fixed": {"wg": inv.wg, "kappa": inv.kappa, "phi_b": inv.braiding_target},
        "gate_p": {
            "delta_chi2": args.gate_dchi2,
            "alpha_significance": "abs(α) > 2 σ_α",
            "inspiral": f"t < {args.t_end} s",
            "band_hz": [args.f_low, args.f_high],
        },
        "results": results,
        "n_gate_p_pass": n_pass,
        "gate_p_d_pass": gate_pd if len(results) > 1 else None,
        "caution": (
            "Large Δχ² with H1/L1 or multi-event sign flips is more often PE "
            "residual systematics than a confirmed topological phase. Require "
            "injection recovery and sign consistency before claims."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
