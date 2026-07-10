#!/usr/bin/env python3
"""
Injection recovery for the whitened H1+L1 network echo pipeline (Gate B-net).

Injects a coherent complex echo train into whitened PE residuals (or Gaussian
noise) and measures recovered Δχ² / network MF SNR vs a_inj.

Usage:
  python scripts/network_injection_recovery.py --event GW150914 --plot
  python scripts/network_injection_recovery.py --into noise --plot
  python scripts/network_injection_recovery.py --amps 0,0.5,1,1.5,2,3 --gate-dchi2 6
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
from src.network_likelihood import (  # noqa: E402
    network_injection_recovery,
    prepare_network,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Whitened network injection recovery")
    p.add_argument("--event", default="GW150914")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--into", choices=("residual", "noise"), default="residual")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--spacing", choices=("geometric", "phase_unit"), default="geometric")
    p.add_argument("--amps", type=str, default="",
                   help="Comma-separated a_inj values (network RMS units)")
    p.add_argument("--n-amps", type=int, default=10)
    p.add_argument("--a-max", type=float, default=3.0)
    p.add_argument("--phase", type=float, default=0.0, help="Injection phase (rad)")
    p.add_argument("--gate-dchi2", type=float, default=6.0,
                   help="Strict Gate C Δχ² (default 6 for 2-dof)")
    p.add_argument("--gate-snr", type=float, default=2.0)
    p.add_argument("--f-low", type=float, default=None)
    p.add_argument("--f-high", type=float, default=None)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()

    print(f"Preparing whitened network for injection: {args.event} / {detectors}")
    event, _params, dets = prepare_network(
        args.event,
        detectors,
        project_root=project_root,
        f_low=args.f_low,
        f_high=args.f_high,
    )
    f_low = float(args.f_low if args.f_low is not None else event.f_low_hz)
    f_high = float(args.f_high if args.f_high is not None else event.f_high_hz)
    for d in dets:
        print(
            f"  {d.detector}: PE SNR≈{d.pe_snr_proxy:.1f}  "
            f"resid_std={np.std(d.residual_w):.3f}"
        )

    if args.amps:
        a_injs = [float(x) for x in args.amps.split(",") if x.strip()]
    else:
        a_injs = list(np.linspace(0.0, args.a_max, args.n_amps))

    print("=" * 60)
    print(
        f"Network injection recovery — into {args.into}  "
        f"gate Δχ²≥{args.gate_dchi2}, SNR≥{args.gate_snr}"
    )
    print(f"{'a_inj':>8}  {'Δχ²':>10}  {'MF SNR':>8}  {'pass':>6}  {'φ_rec':>8}")

    result = network_injection_recovery(
        dets,
        event,
        inv,
        a_injs=a_injs,
        n_echoes=args.n_echoes,
        mode=args.spacing,
        amp0=args.amp0,
        f_low=f_low,
        f_high=f_high,
        phase=args.phase,
        into=args.into,
        gate_delta_chi2=args.gate_dchi2,
        gate_mf_snr=args.gate_snr,
    )

    for row in result["rows"]:
        print(
            f"{row['a_inj']:8.3f}  {row['delta_chi2']:10.3f}  {row['mf_snr']:8.3f}  "
            f"{'YES' if row['passes_gate_c_strict'] else 'no':>6}  {row['phase']:8.3f}"
        )

    print("-" * 60)
    thr = result["detection_threshold_a_inj"]
    if thr is not None:
        print(f"Approx a_inj threshold for Gate C strict: {thr:.3f}")
    else:
        print("No a_inj in grid reached Gate C strict (raise --a-max).")
    if result["background"]:
        bg = result["background"]
        print(
            f"Background (a_inj=0): Δχ²={bg['delta_chi2']:.3f}  "
            f"SNR={bg['mf_snr']:.3f}"
        )
        # Compare to real-data nominal excess
        print(
            "If real-data Δχ²≈4 sits below the a_inj that yields Δχ²≥6, "
            "the marginal excess is in a weakly detectable regime only."
        )
    print("=" * 60)

    tag = f"{event.name}_{'-'.join(detectors)}_network_injection_{args.into}"
    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / f"{tag}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **result,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": event.name,
        "invariants": {"wg": inv.wg, "kappa": inv.kappa},
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            a = [r["a_inj"] for r in result["rows"]]
            dchi = [r["delta_chi2"] for r in result["rows"]]
            snr = [r["mf_snr"] for r in result["rows"]]

            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            axes[0].plot(a, dchi, "o-")
            axes[0].axhline(args.gate_dchi2, color="C3", ls="--",
                            label=f"Δχ²={args.gate_dchi2}")
            axes[0].axhline(4.0, color="C1", ls=":", label="Δχ²=4 (weak)")
            if thr is not None:
                axes[0].axvline(thr, color="0.4", ls=":", label=f"thr≈{thr:.2f}")
            axes[0].set_xlabel("a_inj (network RMS units)")
            axes[0].set_ylabel("Δχ²")
            axes[0].legend(fontsize=8)
            axes[0].set_title("Detection statistic")

            axes[1].plot(a, snr, "o-", color="C2")
            axes[1].axhline(args.gate_snr, color="C3", ls="--", label=f"SNR={args.gate_snr}")
            axes[1].set_xlabel("a_inj (network RMS units)")
            axes[1].set_ylabel("network MF SNR")
            axes[1].legend(fontsize=8)
            axes[1].set_title("Matched-filter SNR")
            fig.suptitle(f"{event.name} network injection into {args.into}")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
