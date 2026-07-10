#!/usr/bin/env python3
"""
Synthetic injection recovery for the positional echo ladder.

Quantifies sensitivity of the PE-residual pipeline:
  - Build PE residual (or use pure pre-merger noise)
  - Inject echo train at scale A_inj relative to residual RMS
  - Fit a1 and measure Δχ²
  - Report recovery curve and approximate detection threshold

Usage:
  python scripts/injection_recovery.py --event GW150914 --plot
  python scripts/injection_recovery.py --into noise --n-amps 12
  python scripts/injection_recovery.py --into residual --amps 0,0.5,1,2,5
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

from src.echo_ladder import (  # noqa: E402
    baseline_ringdown,
    chi2,
    fit_two_amplitudes,
    primary_and_echo_basis,
)
from src.gw_events import get_event  # noqa: E402
from src.gwosc_data import load_event_segment, noise_sigma_premerger  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402


def get_background(
    event_name: str,
    detector: str,
    *,
    into: str,
    f_low: float,
    f_high: float,
) -> tuple[np.ndarray, np.ndarray, float, object]:
    """Return (t_post, background, sigma, event)."""
    event = get_event(event_name)
    seg = load_event_segment(
        event,
        detector=detector,
        cache_dir=project_root / "data" / "gwosc",
        f_low=f_low,
        f_high=f_high,
        duration_pre_s=0.25,
        duration_post_s=event.duration_post_s,
    )
    sigma = noise_sigma_premerger(seg)
    post = seg.t_rel >= 0.0
    t_post = seg.t_rel[post]

    if into == "noise":
        # scramble residual phase → noise-like with same spectrum
        rng = np.random.default_rng(42)
        background = sigma * rng.standard_normal(t_post.shape)
    elif into == "residual":
        from src.pe_waveform import fit_pe_to_strain, pe_params_for_event

        params = pe_params_for_event(event.name, pe_dir=project_root / "data" / "pe")
        fit = fit_pe_to_strain(
            seg.t_rel,
            seg.h,
            params,
            sample_rate=seg.sample_rate,
            sigma=sigma,
            f_low=f_low,
            f_high=f_high,
        )
        background = fit.residual[post].copy()
    else:
        raise ValueError(into)

    return t_post, background, sigma, event


def recover_one(
    t: np.ndarray,
    background: np.ndarray,
    event,
    inv: InvariantSet,
    *,
    a_inj: float,
    sigma: float,
    n_echoes: int,
    spacing: str,
    amp0: float,
) -> dict:
    """Inject a_inj * unit_echo_train and recover."""
    primary, echoes, steps = primary_and_echo_basis(
        t, event, inv, n_echoes=n_echoes, mode=spacing, amp0=amp0
    )
    # unit train has amp_prior relative scales; a_inj multiplies whole train
    # normalize so a_inj=1 means peak |echo_train| ~ sigma (detectability scale)
    peak = float(np.max(np.abs(echoes))) + 1e-60
    unit = echoes / peak * sigma  # peak ~ sigma when a_inj=1
    data = background + a_inj * unit

    a0_b, a1_b = fit_two_amplitudes(background, primary, unit, sigma)
    a0, a1 = fit_two_amplitudes(data, primary, unit, sigma)

    pred_base = a0 * primary  # leftover RD only on injected data
    # For fair nested comparison use same primary+echo basis on data
    pred_base = fit_two_amplitudes(data, primary, np.zeros_like(unit), sigma)[0] * primary
    # actually fit_two with zero echoes degenerates — use single amp
    from src.echo_ladder import fit_amplitude

    a0_only = fit_amplitude(data, primary, sigma)
    pred_base = a0_only * primary
    pred_toe = a0 * primary + a1 * unit

    chi_base = chi2(data, pred_base, sigma)
    chi_toe = chi2(data, pred_toe, sigma)
    chi_null = chi2(data, np.zeros_like(data), sigma)

    return {
        "a_inj": a_inj,
        "a1_recovered": a1,
        "a0_recovered": a0,
        "a1_on_background": a1_b,
        "delta_chi2": chi_base - chi_toe,
        "chi2_base": chi_base,
        "chi2_toe": chi_toe,
        "chi2_null": chi_null,
        "bias": a1 - a_inj,
        "recovered_frac": (a1 / a_inj) if abs(a_inj) > 1e-12 else float("nan"),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Echo ladder injection recovery")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detector", default="H1")
    p.add_argument("--into", choices=("residual", "noise"), default="residual",
                   help="Inject into PE residual or Gaussian noise")
    p.add_argument("--spacing", choices=("geometric", "phase_unit"), default="geometric")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--amps", type=str, default="",
                   help="Comma-separated injection scales (peak/σ units)")
    p.add_argument("--n-amps", type=int, default=10)
    p.add_argument("--a-max", type=float, default=5.0)
    p.add_argument("--f-low", type=float, default=50.0)
    p.add_argument("--f-high", type=float, default=300.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    # detection criterion for threshold estimate
    p.add_argument("--delta-chi2-threshold", type=float, default=4.0)
    args = p.parse_args()

    inv = InvariantSet()
    t, background, sigma, event = get_background(
        args.event,
        args.detector,
        into=args.into,
        f_low=args.f_low,
        f_high=args.f_high,
    )

    if args.amps:
        amps = [float(x) for x in args.amps.split(",") if x.strip()]
    else:
        amps = list(np.linspace(0.0, args.a_max, args.n_amps))

    print("=" * 60)
    print(f"Injection recovery — {event.name}/{args.detector} into {args.into}")
    print(f"  σ={sigma:.3e}  spacing={args.spacing}  n_echoes={args.n_echoes}")
    print(f"  a_inj unit: peak(|echo_train|) / σ  (a_inj=1 ⇒ peak ~ σ)")
    print("=" * 60)
    print(f"{'a_inj':>8}  {'a1_rec':>10}  {'frac':>8}  {'Δχ²':>10}  {'bias':>10}")

    rows = []
    for a in amps:
        r = recover_one(
            t,
            background,
            event,
            inv,
            a_inj=a,
            sigma=sigma,
            n_echoes=args.n_echoes,
            spacing=args.spacing,
            amp0=args.amp0,
        )
        rows.append(r)
        frac = r["recovered_frac"]
        frac_s = f"{frac:8.3f}" if frac == frac else f"{'nan':>8}"
        print(
            f"{r['a_inj']:8.3f}  {r['a1_recovered']:10.3f}  {frac_s}  "
            f"{r['delta_chi2']:10.3f}  {r['bias']:10.3f}"
        )

    # threshold: smallest a_inj>0 with Δχ² >= threshold and a1>0
    thr = None
    for r in rows:
        if r["a_inj"] > 0 and r["delta_chi2"] >= args.delta_chi2_threshold and r["a1_recovered"] > 0:
            thr = r["a_inj"]
            break

    # background-only a1 (a_inj=0 row)
    a1_bg = next((r["a1_recovered"] for r in rows if abs(r["a_inj"]) < 1e-15), None)

    print("-" * 60)
    if thr is not None:
        print(
            f"Approx detection threshold: a_inj ≥ {thr:.3f} "
            f"(Δχ² ≥ {args.delta_chi2_threshold})"
        )
    else:
        print(
            f"No injection in grid reached Δχ² ≥ {args.delta_chi2_threshold} "
            f"with a1>0 (try --a-max larger)."
        )
    if a1_bg is not None:
        print(f"Background-only a1 (a_inj=0): {a1_bg:.3e}")
    print(
        "Note: a_inj is in units of residual peak/σ for the unit train; "
        "map to physical strain via σ and template peak."
    )

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_{args.detector}_injection_{args.into}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.injection_recovery.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": event.name,
        "detector": args.detector,
        "into": args.into,
        "spacing": args.spacing,
        "n_echoes": args.n_echoes,
        "sigma": sigma,
        "delta_chi2_threshold": args.delta_chi2_threshold,
        "detection_threshold_a_inj": thr,
        "background_a1": a1_bg,
        "rows": rows,
        "falsify_criteria_ref": "docs/falsification_criteria.md",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            a_inj = [r["a_inj"] for r in rows]
            a1 = [r["a1_recovered"] for r in rows]
            dchi = [r["delta_chi2"] for r in rows]

            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            axes[0].plot(a_inj, a1, "o-", label="a1 recovered")
            axes[0].plot(a_inj, a_inj, "k--", lw=0.8, label="perfect recovery")
            axes[0].set_xlabel("a_inj (peak/σ)")
            axes[0].set_ylabel("a1 recovered")
            axes[0].legend(fontsize=8)
            axes[0].set_title("Amplitude recovery")

            axes[1].plot(a_inj, dchi, "o-", color="C1")
            axes[1].axhline(
                args.delta_chi2_threshold, color="k", ls="--", lw=0.8, label="threshold"
            )
            if thr is not None:
                axes[1].axvline(thr, color="C3", ls=":", label=f"thr≈{thr:.2f}")
            axes[1].set_xlabel("a_inj (peak/σ)")
            axes[1].set_ylabel("Δχ² (base−toe)")
            axes[1].legend(fontsize=8)
            axes[1].set_title("Detection statistic")
            fig.suptitle(f"{event.name} injection into {args.into}")
            fig.tight_layout()
            plot_path = out.with_suffix(".png")
            fig.savefig(plot_path, dpi=150)
            print(f"Wrote {plot_path}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
