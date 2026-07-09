#!/usr/bin/env python3
"""
Forward simulation: locked invariants → testable GW echo/burst signal.

Implements one concrete prediction from the GW-related papers (echo delay +
spectral peak) under the positional 350/π interpretation.

Usage:
  python scripts/forward_gw_signal.py
  python scripts/forward_gw_signal.py --mass 30 --sites 5 --scale-hz 250
  python scripts/forward_gw_signal.py --from-meta outputs/meta_optimize/foo.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.invariants import InvariantSet, LOCKED_WG  # noqa: E402
from src.positional import burst_loci, phase_to_frequency, PositionalPhase  # noqa: E402
from src.predictions import (  # noqa: E402
    gw_burst_spectrum,
    gw_echo_delay,
    timing_offset_series,
    write_prediction_bundle,
)


def synthesize_waveform(
    inv: InvariantSet,
    *,
    mass_solar: float,
    duration_s: float = 0.25,
    sample_rate: float = 4096.0,
    scale_hz: float = 250.0,
    n_echoes: int = 4,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Simple damped-echo train at positional delays (not full NR).

    Returns time array, strain proxy, and echo metadata.
    """
    t = np.arange(0.0, duration_s, 1.0 / sample_rate)
    h = np.zeros_like(t)
    echoes = []

    # primary ringdown-like burst at t=0
    f0 = phase_to_frequency(PositionalPhase(wg=inv.wg), scale_hz=scale_hz, wg=inv.wg)
    tau = 0.015 * (mass_solar / 30.0)
    h += np.exp(-t / tau) * np.sin(2 * np.pi * f0 * t)

    for n in range(1, n_echoes + 1):
        rec = gw_echo_delay(inv, mass_solar=mass_solar, lattice_index=n)
        delay = rec.value
        amp = 0.35 ** n
        window = np.exp(-np.maximum(t - delay, 0.0) / (tau * 1.2))
        window[t < delay] = 0.0
        # slight phase from lattice site
        phase = PositionalPhase(wg=inv.wg, lattice_index=n)
        h += amp * window * np.sin(2 * np.pi * f0 * t + phase.braiding_angle)
        echoes.append({"n": n, "delay_s": delay, "amp": amp, "freq_hz": f0})

    return t, h, echoes


def main() -> None:
    parser = argparse.ArgumentParser(description="Forward GW signal from invariants")
    parser.add_argument("--mass", type=float, default=30.0, help="Remnant mass (M_sun)")
    parser.add_argument("--sites", type=int, default=5)
    parser.add_argument("--scale-hz", type=float, default=250.0)
    parser.add_argument("--from-meta", type=str, default="",
                        help="Load best_params from meta_optimize JSON")
    parser.add_argument("--out-dir", type=str, default="outputs/predictions")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    if args.from_meta:
        meta = json.loads(Path(args.from_meta).read_text(encoding="utf-8"))
        params = meta.get("best_params", {})
        inv = InvariantSet(
            wg_base=float(params.get("wg_base", 350.0)),
            kappa=float(params.get("kappa", 0.85)),
            braiding_target=float(params.get("braiding_target", 0.8145)),
        )
        print(f"Loaded invariants from {args.from_meta}: Wg={inv.wg:.4f}")
    else:
        inv = InvariantSet()
        print(f"Using canonical lock Wg={LOCKED_WG:.4f}")

    records = [
        gw_echo_delay(inv, mass_solar=args.mass, lattice_index=n)
        for n in range(1, args.sites + 1)
    ]
    records.append(gw_burst_spectrum(inv, scale_hz=args.scale_hz))
    records.extend(
        timing_offset_series(n_sites=args.sites, base_period_s=1.0, inv=inv)
    )

    out_dir = project_root / args.out_dir
    bundle_path = write_prediction_bundle(records, out_dir / "gw_prediction_bundle.json")
    print(f"Wrote prediction bundle → {bundle_path}")

    loci = burst_loci(args.sites, wg=inv.wg, kappa=inv.kappa)
    loci_path = out_dir / "burst_loci.json"
    loci_path.write_text(json.dumps(loci, indent=2), encoding="utf-8")
    print(f"Wrote burst loci → {loci_path}")

    t, h, echoes = synthesize_waveform(
        inv, mass_solar=args.mass, scale_hz=args.scale_hz, n_echoes=args.sites
    )
    np.savez(out_dir / "gw_echo_waveform.npz", t=t, h=h)
    (out_dir / "echo_metadata.json").write_text(
        json.dumps(echoes, indent=2), encoding="utf-8"
    )
    print(f"Wrote waveform → {out_dir / 'gw_echo_waveform.npz'}")
    for e in echoes:
        print(f"  echo n={e['n']}: delay={e['delay_s']:.6e} s  amp={e['amp']:.3f}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(t, h, lw=0.8)
            ax.set_xlabel("t [s]")
            ax.set_ylabel("h (proxy)")
            ax.set_title(f"Positional echo train — Wg={inv.wg:.4f}, M={args.mass} M☉")
            fig.tight_layout()
            fig.savefig(out_dir / "gw_echo_waveform.png", dpi=150)
            print(f"Wrote plot → {out_dir / 'gw_echo_waveform.png'}")
        except ImportError:
            print("matplotlib not available; skip plot")


if __name__ == "__main__":
    main()
