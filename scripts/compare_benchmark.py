#!/usr/bin/env python3
"""
Head-to-head comparison scaffold: model prediction vs baseline on a public-style dataset.

For GW echoes this uses a synthetic baseline (no-echo ringdown) vs the positional
echo train, reporting χ²-style residuals against a mock "observation" that can
later be replaced by real LIGO/Virgo strain segments.

Usage:
  python scripts/compare_benchmark.py
  python scripts/compare_benchmark.py --inject-echoes  # mock data contains echoes
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

from src.invariants import InvariantSet  # noqa: E402
from src.positional import PositionalPhase, phase_to_frequency  # noqa: E402


def ringdown(t: np.ndarray, f0: float, tau: float, t0: float = 0.0) -> np.ndarray:
    x = t - t0
    out = np.zeros_like(t)
    m = x >= 0
    out[m] = np.exp(-x[m] / tau) * np.sin(2 * np.pi * f0 * x[m])
    return out


def model_echo_train(
    t: np.ndarray,
    inv: InvariantSet,
    mass_solar: float,
    scale_hz: float,
    n_echoes: int,
) -> np.ndarray:
    """Positional echo train on an arbitrary time grid."""
    f0 = phase_to_frequency(PositionalPhase(wg=inv.wg), scale_hz=scale_hz, wg=inv.wg)
    tau = 0.015 * (mass_solar / 30.0)
    h = ringdown(t, f0, tau)
    t_m = 4.925490947e-6 * mass_solar
    for n in range(1, n_echoes + 1):
        delay = t_m * (2.0 * np.pi / inv.wg) * n * (1.0 + inv.kappa)
        amp = 0.35 ** n
        phase = PositionalPhase(wg=inv.wg, lattice_index=n)
        h = h + amp * ringdown(t, f0, tau * 1.2, t0=delay) * np.cos(phase.braiding_angle)
    return h


def chi2(obs: np.ndarray, pred: np.ndarray, sigma: float) -> float:
    r = (obs - pred) / sigma
    return float(np.sum(r**2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mass", type=float, default=30.0)
    parser.add_argument("--scale-hz", type=float, default=250.0)
    parser.add_argument("--n-echoes", type=int, default=4)
    parser.add_argument("--inject-echoes", action="store_true",
                        help="Mock observation includes positional echoes")
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument("--out", type=str, default="outputs/benchmarks/compare.json")
    args = parser.parse_args()

    inv = InvariantSet()
    sample_rate = 4096.0
    duration = 0.25
    t = np.arange(0.0, duration, 1.0 / sample_rate)
    f0 = phase_to_frequency(PositionalPhase(wg=inv.wg), scale_hz=args.scale_hz, wg=inv.wg)
    tau = 0.015 * (args.mass / 30.0)

    rng = np.random.default_rng(42)
    noise = args.noise * rng.standard_normal(t.shape)

    baseline = ringdown(t, f0, tau)  # GR-like single ringdown (no echoes)
    toe_model = model_echo_train(
        t, inv, args.mass, args.scale_hz, args.n_echoes
    )

    if args.inject_echoes:
        truth = toe_model
        truth_label = "positional_echoes"
    else:
        truth = baseline
        truth_label = "no_echo_ringdown"

    obs = truth + noise
    sigma = args.noise if args.noise > 0 else 1.0

    chi2_baseline = chi2(obs, baseline, sigma)
    chi2_toe = chi2(obs, toe_model, sigma)
    n = len(t)
    # likelihood-ratio proxy: Δχ² = χ²_base - χ²_toe (positive favors TOE)
    delta = chi2_baseline - chi2_toe

    result = {
        "schema": "invariant_hunt.benchmark.v1",
        "truth": truth_label,
        "n_samples": n,
        "noise_sigma": args.noise,
        "chi2_baseline_no_echo": chi2_baseline,
        "chi2_toe_positional_echo": chi2_toe,
        "delta_chi2_base_minus_toe": delta,
        "prefers": "toe_positional" if delta > 0 else "baseline",
        "wg": inv.wg,
        "mass_solar": args.mass,
        "f0_hz": f0,
        "note": (
            "Synthetic benchmark only. Replace obs with calibrated public strain "
            "and baselines with published GR waveform models for real claims."
        ),
    }

    out = project_root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("Benchmark comparison (synthetic)")
    print(f"  truth model     : {truth_label}")
    print(f"  χ² baseline     : {chi2_baseline:.2f}")
    print(f"  χ² TOE echoes   : {chi2_toe:.2f}")
    print(f"  Δχ² (base-toe)  : {delta:.2f}  → prefers {result['prefers']}")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
