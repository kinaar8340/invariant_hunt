#!/usr/bin/env python3
"""
Follow-up on Gate P-D passers: PE posterior draws + B-P injection + high-Δχ² notes.

Default passers: GW150914, GW170608, GW170814, GW170818

Usage:
  python scripts/premerger_followup_passers.py --plot
  python scripts/premerger_followup_passers.py --n-draws 8 --inject-events GW170814
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
from src.pe_waveform import load_pe_posterior_draws  # noqa: E402
from src.premerger_phase import (  # noqa: E402
    fit_premerger_phase_network,
    prepare_premerger_network,
    premerger_injection_recovery,
    residual_tau_correlation,
)
from src.premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END  # noqa: E402

DEFAULT_PASSERS = ["GW150914", "GW170608", "GW170814", "GW170818"]


def main() -> None:
    p = argparse.ArgumentParser(description="Follow-up PE draws + B-P on Gate P passers")
    p.add_argument(
        "--draw-events",
        default="GW170608,GW170814,GW170818",
        help="Events for PE posterior draws (default: new passers)",
    )
    p.add_argument(
        "--inject-events",
        default="GW170814",
        help="Events for B-P injection recovery (prefer moderate Δχ²)",
    )
    p.add_argument("--n-draws", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--approximant", default="IMRPhenomD")
    p.add_argument("--gate-dchi2", type=float, default=GATE_P_DELTA_CHI2)
    p.add_argument(
        "--alphas",
        default="0,2e-5,5e-5,1e-4,2e-4,5e-4",
    )
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    draw_events = [e.strip() for e in args.draw_events.split(",") if e.strip()]
    inject_events = [e.strip() for e in args.inject_events.split(",") if e.strip()]
    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    alphas = [float(x) for x in args.alphas.split(",") if x.strip()]
    inv = InvariantSet()

    print("=" * 72)
    print("FOLLOW-UP: PE draws on passers + B-P injection + residual diagnostics")
    print(f"  draw events:   {draw_events}")
    print(f"  inject events: {inject_events}")
    print("=" * 72)

    draw_payload: dict = {}
    for name in draw_events:
        print(f"\n### PE DRAWS — {name} (n={args.n_draws}) ###")
        try:
            draws = load_pe_posterior_draws(
                name,
                n_draws=args.n_draws,
                seed=args.seed,
                pe_dir=project_root / "data" / "pe",
                approximant=args.approximant,
            )
        except Exception as exc:
            print(f"  FAILED load: {exc}")
            draw_payload[name] = {"error": str(exc)}
            continue

        rows = []
        for i, params in enumerate(draws):
            try:
                event, dets = prepare_premerger_network(
                    name,
                    detectors,
                    project_root=project_root,
                    duration_pre_s=4.0,
                    approximant=args.approximant,
                    params=params,
                )
                fit = fit_premerger_phase_network(
                    dets,
                    event,
                    t_end=GATE_P_T_END,
                    gate_dchi2=args.gate_dchi2,
                    inv=inv,
                )
                rows.append(
                    {
                        "draw": i,
                        "mass1": params.mass1,
                        "mass2": params.mass2,
                        "distance_mpc": params.distance_mpc,
                        "alpha_hat": fit.alpha_hat,
                        "alpha_sigma": fit.alpha_sigma,
                        "delta_chi2": fit.delta_chi2,
                        "gate_p_pass": bool(fit.gate_p_pass),
                        "pe_snr": {d.detector: d.pe_snr_proxy for d in dets},
                    }
                )
                print(
                    f"  draw {i:02d}: m1+m2={params.mass1+params.mass2:.1f}  "
                    f"α={fit.alpha_hat:.3e}  Δχ²={fit.delta_chi2:.1f}  "
                    f"{'PASS' if fit.gate_p_pass else 'fail'}"
                )
            except Exception as exc:
                print(f"  draw {i:02d}: FAILED {exc}")
                rows.append({"draw": i, "error": str(exc), "gate_p_pass": False})

        ok = [r for r in rows if "error" not in r]
        n_pass = sum(1 for r in ok if r["gate_p_pass"])
        alphas_all = [r["alpha_hat"] for r in ok]
        alphas_pass = [r["alpha_hat"] for r in ok if r["gate_p_pass"]]
        signs = [float(np.sign(a)) for a in alphas_pass]
        sign_maj = (
            max(signs.count(1.0), signs.count(-1.0)) / len(signs) if signs else 0.0
        )
        dchi_med = float(np.median([r["delta_chi2"] for r in ok])) if ok else None
        print(
            f"  → Gate P {n_pass}/{len(ok)}  "
            f"median α(all)={np.median(alphas_all):.3e}  "
            f"sign_maj={sign_maj:.2f}  median Δχ²={dchi_med:.1f}"
        )
        draw_payload[name] = {
            "n_draws": len(ok),
            "n_pass": n_pass,
            "pass_frac": n_pass / max(len(ok), 1),
            "median_alpha_all": float(np.median(alphas_all)) if alphas_all else None,
            "median_alpha_pass": float(np.median(alphas_pass)) if alphas_pass else None,
            "sign_majority_frac": float(sign_maj),
            "median_delta_chi2": dchi_med,
            "rows": rows,
        }

    # Injection recovery
    inj_payload: dict = {}
    for name in inject_events:
        print(f"\n### B-P INJECTION — {name} ###")
        try:
            event, dets = prepare_premerger_network(
                name,
                detectors,
                project_root=project_root,
                duration_pre_s=4.0,
                approximant=args.approximant,
            )
            real = fit_premerger_phase_network(
                dets, event, gate_dchi2=args.gate_dchi2, inv=inv
            )
            print(
                f"  Real: α={real.alpha_hat:.3e}  Δχ²={real.delta_chi2:.2f}  "
                f"Gate P={'PASS' if real.gate_p_pass else 'fail'}"
            )
            corr = residual_tau_correlation(dets, inv)
            for det, v in corr["detectors"].items():
                print(
                    f"  {det} corr(r,τ)={v['corr_r_tau']:+.4f}  "
                    f"power_frac={v['power_frac_along_tau']:.4f}"
                )

            for into in ("noise", "residual"):
                print(f"  --- into {into} ---")
                res = premerger_injection_recovery(
                    dets,
                    event,
                    alpha_injs=alphas,
                    gate_dchi2=args.gate_dchi2,
                    inv=inv,
                    into=into,
                )
                for row in res["rows"]:
                    frac = row["recovered_frac"]
                    fs = f"{frac:.3f}" if frac == frac else "nan"
                    print(
                        f"    α_inj={row['alpha_inj']:.1e}  "
                        f"α_hat={row['alpha_hat']:.3e}  frac={fs}  "
                        f"Δχ²={row['delta_chi2']:.1f}  "
                        f"{'YES' if row['gate_p_pass'] else 'no'}"
                    )
                bg = res["background"]
                if bg:
                    print(
                        f"    bg α=0: Δχ²={bg['delta_chi2']:.2f}  "
                        f"pass={bg['gate_p_pass']}  thr={res['detection_threshold_alpha']}"
                    )
                inj_payload[f"{name}_{into}"] = {
                    "real_alpha": real.alpha_hat,
                    "real_delta_chi2": real.delta_chi2,
                    "real_gate_p": bool(real.gate_p_pass),
                    "correlation": corr,
                    "detection_threshold_alpha": res["detection_threshold_alpha"],
                    "background": bg,
                    "rows": res["rows"],
                }
        except Exception as exc:
            print(f"  FAILED: {exc}")
            inj_payload[name] = {"error": str(exc)}

    # High-Δχ² scrutiny table from draws
    print("\n" + "=" * 72)
    print("HIGH-Δχ² / FOLLOW-UP VERDICT")
    for name, dr in draw_payload.items():
        if "error" in dr:
            print(f"  {name}: draw load failed")
            continue
        flag = ""
        if dr["median_delta_chi2"] and dr["median_delta_chi2"] > 100:
            flag = " ⚠ high median Δχ² — PE mismatch risk"
        if dr["pass_frac"] < 0.5:
            flag = " ⚠ low pass fraction under PE draws"
        elif dr["pass_frac"] >= 0.8 and dr["sign_majority_frac"] >= 0.9:
            flag = " ✓ stable under PE draws"
        print(
            f"  {name}: pass={dr['n_pass']}/{dr['n_draws']}  "
            f"med α={dr['median_alpha_all']:.3e}  "
            f"med Δχ²={dr['median_delta_chi2']:.1f}{flag}"
        )
    for key, inj in inj_payload.items():
        if "error" in inj or "background" not in inj:
            continue
        bg = inj["background"] or {}
        thr = inj.get("detection_threshold_alpha")
        print(
            f"  B-P {key}: noise/res thr α={thr}  "
            f"bg_pass={bg.get('gate_p_pass')}  "
            f"real|α|={abs(inj.get('real_alpha', 0)):.2e}"
        )
    print("=" * 72)

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / "premerger_followup_passers.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.premerger_followup.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pe_posterior_draws": draw_payload,
        "injections": inj_payload,
        "gate_p": {"delta_chi2": args.gate_dchi2, "approximant": args.approximant},
        "note": (
            "PE draws on multi-event passers + B-P on selected event. "
            "High-Δχ² passers that fail PE draws should be demoted."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot and draw_payload:
        try:
            import matplotlib.pyplot as plt

            names = [n for n, d in draw_payload.items() if "rows" in d]
            if not names:
                return
            fig, axes = plt.subplots(1, len(names), figsize=(4 * len(names), 4), squeeze=False)
            for ax, name in zip(axes[0], names):
                dr = draw_payload[name]
                ok = [r for r in dr["rows"] if "error" not in r]
                cols = ["C2" if r["gate_p_pass"] else "C3" for r in ok]
                ax.scatter(
                    range(len(ok)),
                    [r["alpha_hat"] for r in ok],
                    c=cols,
                )
                ax.axhline(0, color="k", lw=0.5)
                ax.set_title(f"{name}\n{dr['n_pass']}/{dr['n_draws']} pass")
                ax.set_xlabel("draw")
                ax.set_ylabel("α_hat")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
