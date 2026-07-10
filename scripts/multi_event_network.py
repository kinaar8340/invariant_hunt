#!/usr/bin/env python3
"""
Run whitened H1+L1 network + Gate C strict across multiple public BBHs.

Usage:
  python scripts/multi_event_network.py --events GW150914,GW170104,GW151226 --plot
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent


def main() -> None:
    p = argparse.ArgumentParser(description="Multi-event whitened network Gate C")
    p.add_argument(
        "--events",
        default="GW150914,GW170104,GW151226",
        help="Comma-separated catalog events",
    )
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--no-scan", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--gate-a-thr", type=float, default=4.0)
    args = p.parse_args()

    events = [e.strip() for e in args.events.split(",") if e.strip()]
    rows = []
    for name in events:
        print("\n" + "#" * 60)
        print(f"# {name}")
        print("#" * 60)
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "network_whiten_scan.py"),
            "--event",
            name,
            "--detectors",
            args.detectors,
            "--gate-a-thr",
            str(args.gate_a_thr),
        ]
        if args.no_scan:
            cmd.append("--no-scan")
        if args.plot:
            cmd.append("--plot")
        subprocess.check_call(cmd)

        tag = f"{name}_{args.detectors.replace(',', '-')}_whitened_network"
        jpath = project_root / "outputs" / "benchmarks" / f"{tag}.json"
        if not jpath.exists():
            # fallback naming
            jpath = project_root / "outputs" / "benchmarks" / f"{name}_H1-L1_whitened_network.json"
        data = json.loads(jpath.read_text(encoding="utf-8"))
        nom = data["nominal"]
        rows.append(
            {
                "event": name,
                "delta_chi2": nom["delta_chi2"],
                "mf_snr": nom["mf_snr"],
                "amp": nom["amp"],
                "gate_c_weak": data.get("gate_c_weak_pass"),
                "gate_c_strict": data.get("gate_c_strict_pass"),
                "band_hz": data.get("f_band_hz"),
                "mass_final": data["event"]["mass_final_solar"],
                "json": str(jpath),
            }
        )

    print("\n" + "=" * 60)
    print("MULTI-EVENT SUMMARY (whitened H1+L1, s=1, coherent map)")
    print(
        f"{'event':<12} {'Δχ²':>8} {'SNR':>7} {'weak':>6} {'strict':>7} "
        f"{'M_f':>6} {'band':>12}"
    )
    for r in rows:
        band = r["band_hz"] or []
        band_s = f"{band[0]:.0f}-{band[1]:.0f}" if len(band) == 2 else "?"
        print(
            f"{r['event']:<12} {r['delta_chi2']:8.3f} {r['mf_snr']:7.3f} "
            f"{'Y' if r['gate_c_weak'] else 'n':>6} "
            f"{'Y' if r['gate_c_strict'] else 'n':>7} "
            f"{r['mass_final']:6.1f} {band_s:>12}"
        )
    n_strict = sum(1 for r in rows if r["gate_c_strict"])
    n_weak = sum(1 for r in rows if r["gate_c_weak"])
    print("-" * 60)
    print(f"Gate C weak pass:   {n_weak}/{len(rows)}")
    print(f"Gate C strict pass: {n_strict}/{len(rows)}")
    print(
        "Gate D (multi-event): requires Gate C strict on ≥3 events — "
        f"{'PASS' if n_strict >= 3 else 'FAIL'}"
    )
    print("=" * 60)

    out = project_root / "outputs" / "benchmarks" / "multi_event_network_summary.json"
    out.write_text(
        json.dumps(
            {
                "schema": "invariant_hunt.multi_event_network.v1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "rows": rows,
                "n_gate_c_weak": n_weak,
                "n_gate_c_strict": n_strict,
                "gate_d_pass": n_strict >= 3,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
