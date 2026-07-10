#!/usr/bin/env python3
"""
Map the positional echo-delay ladder onto a public GW event.

Prints the ladder for the event remnant mass, writes a prediction bundle,
and optionally runs the full public-strain benchmark.

Usage:
  python scripts/map_event_echoes.py --event GW150914
  python scripts/map_event_echoes.py --event GW150914 --benchmark --plot
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.echo_ladder import build_ladder, ladder_prediction_records  # noqa: E402
from src.gw_events import get_event  # noqa: E402
from src.invariants import InvariantSet, LOCKED_WG  # noqa: E402
from src.predictions import write_prediction_bundle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Map echo ladder to public GW event")
    parser.add_argument("--event", type=str, default="GW150914")
    parser.add_argument("--n-echoes", type=int, default=5)
    parser.add_argument(
        "--spacing",
        choices=("geometric", "phase_unit"),
        default="geometric",
    )
    parser.add_argument("--benchmark", action="store_true",
                        help="Also run compare_benchmark on GWOSC strain")
    parser.add_argument("--detector", type=str, default="H1")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    event = get_event(args.event)
    inv = InvariantSet()

    print("=" * 60)
    print(f"Event: {event.name}")
    print(f"  GPS merger     : {event.gps}")
    print(f"  M_final        : {event.mass_final_solar} M_sun")
    print(f"  t_M = GM/c³    : {event.t_m:.6e} s")
    print(f"  f_ring (approx): {event.f_ring_hz} Hz")
    print(f"  W_g lock       : {LOCKED_WG:.4f}")
    print(f"  κ              : {inv.kappa}")
    print(f"  spacing mode   : {args.spacing}")
    print("=" * 60)

    steps = build_ladder(event, inv, n_echoes=args.n_echoes, mode=args.spacing)
    print("Positional echo-delay ladder (post-merger):")
    print(f"{'n':>4}  {'δt [ms]':>12}  {'± [ms]':>10}  {'amp_prior':>10}  {'φ_braid':>10}")
    for s in steps:
        print(
            f"{s.n:4d}  {s.delay_s*1e3:12.4f}  {s.uncertainty_s*1e3:10.4f}  "
            f"{s.amp_prior:10.4f}  {s.braiding_angle:10.4f}"
        )

    # Also show phase_unit ladder for transparency
    if args.spacing == "geometric":
        print("\n(For reference — phase_unit spacing, usually sub-sample:)")
        for s in build_ladder(event, inv, n_echoes=args.n_echoes, mode="phase_unit"):
            print(f"  n={s.n}: δt={s.delay_s*1e6:.3f} µs")

    recs = ladder_prediction_records(
        event, inv, n_echoes=args.n_echoes, mode=args.spacing
    )
    out_dir = project_root / "outputs" / "predictions"
    bundle = write_prediction_bundle(
        recs, out_dir / f"{event.name}_echo_ladder_{args.spacing}.json"
    )
    ladder_json = out_dir / f"{event.name}_ladder_table_{args.spacing}.json"
    ladder_json.write_text(
        json.dumps(
            {
                "event": event.to_dict(),
                "wg": inv.wg,
                "kappa": inv.kappa,
                "spacing": args.spacing,
                "steps": [s.to_dict() for s in steps],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {bundle}")
    print(f"Wrote {ladder_json}")

    if args.benchmark:
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "compare_benchmark.py"),
            "--event",
            event.name,
            "--detector",
            args.detector,
            "--n-echoes",
            str(args.n_echoes),
            "--spacing",
            args.spacing,
        ]
        if args.plot:
            cmd.append("--plot")
        print("\nRunning public-strain benchmark…")
        subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
