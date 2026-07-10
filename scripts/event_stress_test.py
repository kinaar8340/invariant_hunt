#!/usr/bin/env python3
"""
Stress-test an outlier event (default GW151226):

  1. Whitened H1+L1 network at catalog band (already in multi_event)
  2. Network injection recovery (Gate B-net)
  3. Band systematics: narrower bands around f_ring

Usage:
  python scripts/event_stress_test.py --event GW151226 --plot
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

from src.gw_events import get_event  # noqa: E402
from src.invariants import InvariantSet  # noqa: E402
from src.network_likelihood import (  # noqa: E402
    fit_network_coherent,
    network_delay_scan,
    network_injection_recovery,
    prepare_network,
)


def band_grid(f_ring: float, f_nyquist: float = 2048.0) -> list[tuple[float, float, str]]:
    """Narrower / alternate bands around ringdown."""
    fr = float(f_ring)
    bands = [
        (50.0, min(900.0, f_nyquist), "catalog_wide"),
        (50.0, min(fr * 1.5, f_nyquist), "50_to_1.5fring"),
        (max(30.0, fr * 0.5), min(fr * 1.5, f_nyquist), "0.5_1.5_fring"),
        (max(30.0, fr * 0.7), min(fr * 1.3, f_nyquist), "0.7_1.3_fring"),
        (max(30.0, fr - 150.0), min(fr + 150.0, f_nyquist), "fring_pm150"),
        (50.0, 300.0, "gw150914_band"),  # deliberately off for light BBH
    ]
    # unique by (lo, hi)
    seen = set()
    out = []
    for lo, hi, name in bands:
        if hi <= lo + 20:
            continue
        key = (round(lo, 1), round(hi, 1))
        if key in seen:
            continue
        seen.add(key)
        out.append((lo, hi, name))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Event stress test: injections + bands")
    p.add_argument("--event", default="GW151226")
    p.add_argument("--detectors", default="H1,L1")
    p.add_argument("--gate-dchi2", type=float, default=6.0)
    p.add_argument("--gate-snr", type=float, default=2.0)
    p.add_argument("--n-echoes", type=int, default=5)
    p.add_argument("--amps", type=str, default="0,0.25,0.33,0.5,1.0,2.0")
    p.add_argument("--skip-injections", action="store_true")
    p.add_argument("--skip-scan", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    detectors = [d.strip() for d in args.detectors.split(",") if d.strip()]
    event = get_event(args.event)
    inv = InvariantSet()
    a_injs = [float(x) for x in args.amps.split(",") if x.strip()]

    print("=" * 60)
    print(f"STRESS TEST — {event.name}")
    print(f"  M_final={event.mass_final_solar}  f_ring≈{event.f_ring_hz} Hz")
    print(f"  catalog band [{event.f_low_hz}, {event.f_high_hz}] Hz")
    print(f"  Gate C strict: Δχ²≥{args.gate_dchi2}, SNR≥{args.gate_snr}")
    print("=" * 60)

    band_rows = []
    for f_low, f_high, bname in band_grid(event.f_ring_hz):
        print(f"\n--- band {bname}: [{f_low:.0f}, {f_high:.0f}] Hz ---")
        try:
            _ev, _params, dets = prepare_network(
                event.name,
                detectors,
                project_root=project_root,
                f_low=f_low,
                f_high=f_high,
            )
        except Exception as exc:
            print(f"  SKIP prepare failed: {exc}")
            band_rows.append(
                {
                    "band": bname,
                    "f_low": f_low,
                    "f_high": f_high,
                    "error": str(exc),
                }
            )
            continue

        for d in dets:
            print(f"  {d.detector}: PE SNR≈{d.pe_snr_proxy:.1f}  resid_std={np.std(d.residual_w):.3f}")

        nom = fit_network_coherent(
            dets,
            event,
            inv,
            n_echoes=args.n_echoes,
            delay_scale=1.0,
            f_low=f_low,
            f_high=f_high,
        )
        strict = nom.delta_chi2 >= args.gate_dchi2 and nom.mf_snr >= args.gate_snr
        weak = nom.delta_chi2 >= 4.0 and nom.mf_snr >= 2.0
        print(
            f"  s=1: Δχ²={nom.delta_chi2:.3f}  SNR={nom.mf_snr:.3f}  "
            f"strict={'PASS' if strict else 'fail'}  weak={'PASS' if weak else 'fail'}"
        )

        scan_info = None
        if not args.skip_scan:
            scan = network_delay_scan(
                dets,
                event,
                inv,
                n_echoes=args.n_echoes,
                scan_min=0.80,
                scan_max=1.20,
                n_scales=21,
                gate_a_threshold=args.gate_dchi2,  # LEE against strict thr
                f_low=f_low,
                f_high=f_high,
            )
            print(
                f"  scan best s={scan['best']['delay_scale']:.3f}  "
                f"Δχ²={scan['best']['delta_chi2']:.3f}  "
                f"LEE thr={scan['lee_threshold_corrected']:.2f}  "
                f"LEE={'PASS' if scan['passes_gate_a_best_lee'] else 'fail'}"
            )
            scan_info = {
                "best_s": scan["best"]["delay_scale"],
                "best_delta_chi2": scan["best"]["delta_chi2"],
                "best_mf_snr": scan["best"]["mf_snr"],
                "lee_threshold": scan["lee_threshold_corrected"],
                "passes_lee": scan["passes_gate_a_best_lee"],
            }

        band_rows.append(
            {
                "band": bname,
                "f_low": f_low,
                "f_high": f_high,
                "delta_chi2": nom.delta_chi2,
                "mf_snr": nom.mf_snr,
                "amp": nom.amp,
                "phase": nom.phase,
                "pe_snr": {d.detector: d.pe_snr_proxy for d in dets},
                "gate_c_strict": strict,
                "gate_c_weak": weak,
                "scan": scan_info,
            }
        )

    # Injections on catalog band
    inj_payload = None
    if not args.skip_injections:
        print("\n--- network injection recovery (catalog band) ---")
        _ev, _params, dets = prepare_network(
            event.name,
            detectors,
            project_root=project_root,
            f_low=event.f_low_hz,
            f_high=event.f_high_hz,
        )
        for into in ("residual", "noise"):
            print(f"\n  into {into}:")
            res = network_injection_recovery(
                dets,
                event,
                inv,
                a_injs=a_injs,
                n_echoes=args.n_echoes,
                f_low=event.f_low_hz,
                f_high=event.f_high_hz,
                into=into,
                gate_delta_chi2=args.gate_dchi2,
                gate_mf_snr=args.gate_snr,
            )
            print(f"  {'a_inj':>8}  {'Δχ²':>10}  {'SNR':>8}  pass")
            for row in res["rows"]:
                print(
                    f"  {row['a_inj']:8.3f}  {row['delta_chi2']:10.3f}  "
                    f"{row['mf_snr']:8.3f}  "
                    f"{'YES' if row['passes_gate_c_strict'] else 'no'}"
                )
            print(f"  thr a_inj (strict) = {res['detection_threshold_a_inj']}")
            if inj_payload is None:
                inj_payload = {}
            inj_payload[into] = res

    # Verdict
    catalog = next((r for r in band_rows if r.get("band") == "catalog_wide"), None)
    narrow = [r for r in band_rows if r.get("band") not in (None, "catalog_wide", "gw150914_band") and "error" not in r]
    n_strict_narrow = sum(1 for r in narrow if r.get("gate_c_strict"))
    off_band = next((r for r in band_rows if r.get("band") == "gw150914_band"), None)

    print("\n" + "=" * 60)
    print(f"STRESS TEST SUMMARY — {event.name}")
    print(f"{'band':<18} {'Δχ²':>8} {'SNR':>7} {'strict':>7} {'LEE':>6}")
    for r in band_rows:
        if "error" in r:
            print(f"{r['band']:<18}  ERROR: {r['error'][:40]}")
            continue
        lee = r.get("scan") or {}
        lee_s = "Y" if lee.get("passes_lee") else ("n" if lee else "—")
        print(
            f"{r['band']:<18} {r['delta_chi2']:8.3f} {r['mf_snr']:7.3f} "
            f"{'Y' if r['gate_c_strict'] else 'n':>7} {lee_s:>6}"
        )
    print("-" * 60)

    holds = False
    reasons = []
    if catalog and catalog.get("gate_c_strict"):
        reasons.append("catalog band passes Gate C strict")
    else:
        reasons.append("catalog band fails Gate C strict")
    if narrow:
        frac = n_strict_narrow / len(narrow)
        reasons.append(f"narrow bands strict pass {n_strict_narrow}/{len(narrow)}")
        if frac >= 0.5 and catalog and catalog.get("gate_c_strict"):
            holds = True
    if off_band and not off_band.get("gate_c_strict") and catalog and catalog.get("gate_c_strict"):
        reasons.append("off-band (50-300) fails while catalog passes — band-localized (good sign)")
    elif off_band and off_band.get("gate_c_strict"):
        reasons.append("off-band also passes — may be broadband noise/systematics")
        holds = False

    if inj_payload:
        bg = (inj_payload.get("residual") or {}).get("background") or {}
        thr = (inj_payload.get("residual") or {}).get("detection_threshold_a_inj")
        reasons.append(
            f"injection thr a_inj={thr}; real residual Δχ²={bg.get('delta_chi2')}"
        )
        noise_bg = (inj_payload.get("noise") or {}).get("background") or {}
        if noise_bg:
            reasons.append(f"noise floor Δχ²={noise_bg.get('delta_chi2')}")

    print(f"Holds under stress?: {'YES (provisional)' if holds else 'NO / weak'}")
    for r in reasons:
        print(f"  • {r}")
    print("=" * 60)

    out = Path(args.out) if args.out else (
        project_root
        / "outputs"
        / "benchmarks"
        / f"{event.name}_stress_test.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.event_stress_test.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "event": event.to_dict(),
        "detectors": detectors,
        "gate_c_strict": {"delta_chi2": args.gate_dchi2, "mf_snr": args.gate_snr},
        "bands": band_rows,
        "injections": {
            k: {
                "detection_threshold_a_inj": v.get("detection_threshold_a_inj"),
                "background": v.get("background"),
                "rows": v.get("rows"),
            }
            for k, v in (inj_payload or {}).items()
        },
        "holds_under_stress": holds,
        "reasons": reasons,
        "note": (
            "Provisional 'holds' requires catalog Gate C strict AND majority of "
            "narrower f_ring-centered bands also strict-pass. Not a discovery claim."
        ),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            ok = [r for r in band_rows if "delta_chi2" in r]
            labels = [r["band"] for r in ok]
            dchi = [r["delta_chi2"] for r in ok]
            snrs = [r["mf_snr"] for r in ok]
            x = np.arange(len(ok))

            fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            colors = [
                "C2" if r.get("gate_c_strict") else ("C1" if r.get("gate_c_weak") else "C3")
                for r in ok
            ]
            axes[0].bar(x, dchi, color=colors)
            axes[0].axhline(args.gate_dchi2, color="k", ls="--", label=f"strict={args.gate_dchi2}")
            axes[0].axhline(4.0, color="0.5", ls=":", label="weak=4")
            axes[0].set_ylabel("Δχ²")
            axes[0].legend(fontsize=8)
            axes[0].set_title(f"{event.name} band systematics")

            axes[1].bar(x, snrs, color=colors)
            axes[1].axhline(args.gate_snr, color="k", ls="--")
            axes[1].set_ylabel("MF SNR")
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
            fig.tight_layout()
            fig.savefig(out.with_suffix(".png"), dpi=150)
            print(f"Wrote {out.with_suffix('.png')}")

            if inj_payload and "residual" in inj_payload:
                rows = inj_payload["residual"]["rows"]
                fig2, ax = plt.subplots(figsize=(7, 4))
                ax.plot(
                    [r["a_inj"] for r in rows],
                    [r["delta_chi2"] for r in rows],
                    "o-",
                    label="into residual",
                )
                if "noise" in inj_payload:
                    rn = inj_payload["noise"]["rows"]
                    ax.plot(
                        [r["a_inj"] for r in rn],
                        [r["delta_chi2"] for r in rn],
                        "s--",
                        label="into noise",
                    )
                ax.axhline(args.gate_dchi2, color="k", ls="--")
                ax.set_xlabel("a_inj")
                ax.set_ylabel("Δχ²")
                ax.legend(fontsize=8)
                ax.set_title(f"{event.name} network injection recovery")
                fig2.tight_layout()
                fig2.savefig(
                    out.with_name(out.stem + "_injections.png"), dpi=150
                )
                print(f"Wrote {out.with_name(out.stem + '_injections.png')}")
        except ImportError:
            print("matplotlib not available")


if __name__ == "__main__":
    main()
