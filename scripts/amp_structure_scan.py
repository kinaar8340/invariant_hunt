#!/usr/bin/env python3
"""
Scan amplitude-structure mappings under whitened H1+L1 network gates.

Keeps core locks fixed (W_g, κ, braiding attractor). Only relative step
weights change. For each structure × event: Δχ², MF SNR, Gate C weak/strict.

Usage:
  python scripts/amp_structure_scan.py --plot
  python scripts/amp_structure_scan.py --events GW150914,GW170104,GW151226
  python scripts/amp_structure_scan.py --structures geometric,braiding,flux_kappa
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

from src.amp_structure import (  # noqa: E402
    AMP_STRUCTURES,
    AmpStructure,
    structure_description,
)
from src.invariants import InvariantSet  # noqa: E402
from src.network_likelihood import (  # noqa: E402
    fit_network_coherent,
    prepare_network,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Amplitude structure × multi-event scan")
    p.add_argument(
        "--events",
        default="GW150914,GW170104,GW151226",
    )
    p.add_argument(
        "--structures",
        default=",".join(AMP_STRUCTURES),
    )
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amp0", type=float, default=0.35)
    p.add_argument("--gate-dchi2", type=float, default=6.0)
    p.add_argument("--gate-snr", type=float, default=2.0)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    events = [e.strip() for e in args.events.split(",") if e.strip()]
    structures: list[AmpStructure] = [
        s.strip() for s in args.structures.split(",") if s.strip()  # type: ignore
    ]
    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    inv = InvariantSet()

    rows = []
    # Cache prepared detectors per event (expensive)
    prepared: dict[str, tuple] = {}

    print("=" * 72)
    print("AMPLITUDE-STRUCTURE SCAN (whitened network, s=1, locks fixed)")
    print(f"  structures: {structures}")
    print(f"  events:     {events}")
    print(f"  Gate C strict: Δχ²≥{args.gate_dchi2}, SNR≥{args.gate_snr}")
    print("=" * 72)

    for name in events:
        if name not in prepared:
            print(f"\nPreparing {name}…")
            prepared[name] = prepare_network(
                name, detectors, project_root=project_root
            )
        event, params, dets = prepared[name]
        print(
            f"  {name}: M_f={event.mass_final_solar}  "
            f"band=[{event.f_low_hz},{event.f_high_hz}]  "
            f"PE H1≈{dets[0].pe_snr_proxy:.1f}"
        )

        for struct in structures:
            nom = fit_network_coherent(
                dets,
                event,
                inv,
                n_echoes=args.n_echoes,
                amp0=args.amp0,
                delay_scale=1.0,
                f_low=event.f_low_hz,
                f_high=event.f_high_hz,
                amp_structure=struct,
            )
            weak = nom.delta_chi2 >= 4.0 and nom.mf_snr >= args.gate_snr
            strict = nom.delta_chi2 >= args.gate_dchi2 and nom.mf_snr >= args.gate_snr
            row = {
                "event": name,
                "amp_structure": struct,
                "delta_chi2": nom.delta_chi2,
                "mf_snr": nom.mf_snr,
                "amp": nom.amp,
                "phase": nom.phase,
                "gate_c_weak": weak,
                "gate_c_strict": strict,
                "mass_final": event.mass_final_solar,
                "weights": [s.amp_prior for s in nom.steps],
                "delays_ms": [s.delay_s * 1e3 for s in nom.steps],
            }
            rows.append(row)
            print(
                f"    {struct:<16} Δχ²={nom.delta_chi2:7.3f}  SNR={nom.mf_snr:5.3f}  "
                f"strict={'Y' if strict else 'n'}  weak={'Y' if weak else 'n'}"
            )

    # Summary table
    print("\n" + "=" * 72)
    print(f"{'structure':<16} " + " ".join(f"{e:>12}" for e in events) + "  strict#")
    for struct in structures:
        cells = []
        n_strict = 0
        for name in events:
            r = next(x for x in rows if x["event"] == name and x["amp_structure"] == struct)
            cells.append(f"{r['delta_chi2']:5.2f}/{r['mf_snr']:4.2f}")
            if r["gate_c_strict"]:
                n_strict += 1
        print(f"{struct:<16} " + " ".join(f"{c:>12}" for c in cells) + f"  {n_strict}/{len(events)}")

    # Best structure by # strict, then mean Δχ²
    by_struct: dict[str, list] = {s: [] for s in structures}
    for r in rows:
        by_struct[r["amp_structure"]].append(r)
    ranking = []
    for s, rs in by_struct.items():
        n_s = sum(1 for r in rs if r["gate_c_strict"])
        mean_d = sum(r["delta_chi2"] for r in rs) / max(len(rs), 1)
        ranking.append((n_s, mean_d, s))
    ranking.sort(reverse=True)
    best = ranking[0][2] if ranking else "geometric"
    print("-" * 72)
    print(f"Best by Gate C strict count then mean Δχ²: {best}")
    print(f"  description: {structure_description(best)['formula']}")
    print(
        f"Gate D (strict on ≥3 events) for best: "
        f"{'PASS' if ranking[0][0] >= 3 else 'FAIL'} ({ranking[0][0]}/{len(events)})"
    )
    print(
        "Note: comparing structures is exploratory; do not LEE-correct across "
        "structures unless pre-registered. Core locks unchanged."
    )
    print("=" * 72)

    out = Path(args.out) if args.out else (
        project_root / "outputs" / "benchmarks" / "amp_structure_scan.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.amp_structure_scan.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "events": events,
        "structures": structures,
        "structure_docs": {s: structure_description(s) for s in structures},
        "invariants_fixed": {"wg": inv.wg, "kappa": inv.kappa},
        "gate_c_strict": {"delta_chi2": args.gate_dchi2, "mf_snr": args.gate_snr},
        "rows": rows,
        "ranking": [
            {"amp_structure": s, "n_strict": n, "mean_delta_chi2": m}
            for n, m, s in ranking
        ],
        "best_structure": best,
        "gate_d_best": ranking[0][0] >= 3 if ranking else False,
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            n_e, n_s = len(events), len(structures)
            mat = np.zeros((n_s, n_e))
            for i, s in enumerate(structures):
                for j, e in enumerate(events):
                    r = next(
                        x for x in rows if x["event"] == e and x["amp_structure"] == s
                    )
                    mat[i, j] = r["delta_chi2"]

            fig, ax = plt.subplots(figsize=(8, 4.5))
            im = ax.imshow(mat, aspect="auto", cmap="viridis")
            ax.set_xticks(range(n_e))
            ax.set_xticklabels(events)
            ax.set_yticks(range(n_s))
            ax.set_yticklabels(structures)
            for i in range(n_s):
                for j in range(n_e):
                    r = next(
                        x
                        for x in rows
                        if x["event"] == events[j] and x["amp_structure"] == structures[i]
                    )
                    mark = "*" if r["gate_c_strict"] else ""
                    ax.text(
                        j,
                        i,
                        f"{mat[i, j]:.1f}{mark}",
                        ha="center",
                        va="center",
                        color="w",
                        fontsize=9,
                    )
            ax.set_title("Δχ² by amp structure × event (* = Gate C strict)")
            fig.colorbar(im, ax=ax, label="Δχ²")
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
