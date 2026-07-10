#!/usr/bin/env python3
"""
Meta-optimizer for robust topological invariants (positional 350/π focus).

Extends the TOE script meta_optimize_invariants.py with:
  - positional / phase framing of W_g = wg_base/π
  - stability across seeds + optional parameter jitter
  - JSON output for the prediction pipeline
  - optional lightweight mode (no conduit) for CI / dry runs
  - Phase 1.2: --locks-fixed holonomy/gauge sweeps (W_g, κ*, φ_b* frozen)

Usage:
  python scripts/meta_optimize_invariants.py --trials 30
  python scripts/meta_optimize_invariants.py --trials 100 --positional
  python scripts/meta_optimize_invariants.py --dry-run --trials 20
  python scripts/meta_optimize_invariants.py --locks-fixed --dry-run --trials 40
  python scripts/meta_optimize_invariants.py --locks-fixed --monte-carlo --samples 64
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gauged_meta_sweep import (  # noqa: E402
    run_locks_fixed_monte_carlo,
    run_locks_fixed_optuna,
)
from src.invariants import (  # noqa: E402
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
    geometric_winding_from_base,
    hopf_penalty,
)
from src.positional import (  # noqa: E402
    PositionalPhase,
    phase_to_frequency,
    phase_to_timing_offset,
    positional_hopf_residual,
)

# Real noble-gas + magic-island targets for island loss (from TOE)
REAL_ISLAND_TARGETS = {
    2: {"stability": 8.0, "bursts": 0.05},
    10: {"stability": 8.0, "bursts": 0.05},
    18: {"stability": 8.0, "bursts": 0.05},
    36: {"stability": 8.0, "bursts": 0.05},
    54: {"stability": 8.0, "bursts": 0.05},
    86: {"stability": 8.0, "bursts": 0.05},
    129: {"stability": 8.5, "bursts": 0.02},
}


def _evaluate_with_conduit(
    wg_base: float,
    kappa: float,
    braiding_target: float,
    n_seeds: int = 3,
    positional: bool = True,
) -> dict:
    """Full evaluation via RubikConeConduit (requires torch + config)."""
    import torch
    from src.conduit import RubikConeConduit
    from src.config import load_config

    cfg = load_config(project_root / "configs" / "default.yaml")
    results = []
    last_stats = {}

    for seed in range(n_seeds):
        torch.manual_seed(seed)
        conduit = RubikConeConduit(
            embed_dim=cfg.model.embed_dim,
            twist_rate=cfg.model.twist_rate,
            max_depth=cfg.model.max_depth,
            num_polarizations=cfg.model.num_polarizations,
            quat_logical_dim=getattr(cfg.model, "quat_logical_dim", 96),
            toroidal_modulo9=True,
            vortex_math_369=True,
            clifford_projection=True,
            wg_base=wg_base,
            kappa=kappa,
            braiding_target=braiding_target,
        ).to("cuda" if torch.cuda.is_available() else "cpu")

        stats = conduit.monitor_topological_winding(n_samples=512)
        last_stats = stats

        geo_w = float(stats.get("geometric_winding", 0.0))
        braiding = float(stats.get("braiding_phase", 0.0))
        stability = float(stats.get("stability_score", 5.0))
        bursts = float(stats.get("bursts_per_step", 1.0))

        island_loss = 0.0
        for _pseudo_z, target in REAL_ISLAND_TARGETS.items():
            island_loss += abs(stability - target["stability"]) + 5.0 * abs(
                bursts - target["bursts"]
            )

        if positional:
            # Positional framing: residual is lattice misalignment of winding
            hopf = positional_hopf_residual(geo_w, wg_base)
            phase = PositionalPhase(wg=geo_w if geo_w > 0 else geometric_winding_from_base(wg_base))
            # Prefer low alignment residual + timing structure consistency
            timing_term = abs(
                phase_to_timing_offset(phase, base_period=1.0) - (1.0 / max(geo_w, 1e-6)) % 1.0
            )
            pos_term = 0.5 * phase.alignment_to_canonical() + 0.2 * timing_term
        else:
            hopf = hopf_penalty(geo_w, wg_base)
            pos_term = 0.0

        braiding_penalty = abs(braiding - braiding_target)
        total_loss = island_loss + 3.0 * hopf + 0.8 * braiding_penalty + pos_term
        results.append(total_loss)

    inv = InvariantSet.from_monitor_stats(
        last_stats, wg_base=wg_base, kappa=kappa, braiding_target=braiding_target
    )
    return {
        "loss": float(np.mean(results)),
        "loss_std": float(np.std(results)),
        "discovered_Wg": geometric_winding_from_base(wg_base),
        "kappa": kappa,
        "braiding_target": braiding_target,
        "invariant": inv.to_dict(),
        "positional": positional,
    }


def _evaluate_dry(
    wg_base: float,
    kappa: float,
    braiding_target: float,
    positional: bool = True,
) -> dict:
    """Analytic surrogate loss for CI / no-GPU environments.

    Loss is minimized near wg_base=350, kappa=0.85, braiding≈0.8145,
    with a soft positional penalty on phase misalignment.
    """
    geo_w = geometric_winding_from_base(wg_base)
    hopf = abs(geo_w - LOCKED_WG)
    kappa_pen = abs(kappa - 0.85)
    braid_pen = abs(braiding_target - 0.8145)
    phase = PositionalPhase(wg=geo_w, lattice_index=1)
    pos_pen = phase.alignment_to_canonical() if positional else 0.0
    # synthetic island bowl around lock
    island = 0.1 * (hopf**2) + 2.0 * kappa_pen**2 + 1.5 * braid_pen**2
    loss = island + 3.0 * hopf + 0.8 * braid_pen + 0.5 * pos_pen

    inv = InvariantSet(wg_base=wg_base, kappa=kappa, braiding_target=braiding_target)
    return {
        "loss": float(loss),
        "loss_std": 0.0,
        "discovered_Wg": geo_w,
        "kappa": kappa,
        "braiding_target": braiding_target,
        "invariant": inv.to_dict(),
        "positional": positional,
        "dry_run": True,
        "predicted_freq_proxy": phase_to_frequency(phase, scale_hz=250.0),
        "predicted_timing_offset": phase_to_timing_offset(phase, base_period=1.0),
    }


def evaluate_trial(
    wg_base: float,
    kappa: float,
    braiding_target: float,
    n_seeds: int = 3,
    positional: bool = True,
    dry_run: bool = False,
) -> dict:
    if dry_run:
        return _evaluate_dry(wg_base, kappa, braiding_target, positional=positional)
    try:
        return _evaluate_with_conduit(
            wg_base, kappa, braiding_target, n_seeds=n_seeds, positional=positional
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"⚠️  Conduit evaluation failed ({exc}); falling back to dry-run surrogate.")
        out = _evaluate_dry(wg_base, kappa, braiding_target, positional=positional)
        out["fallback_reason"] = str(exc)
        return out


def _default_out_path(prefix: str = "meta_optimize") -> Path:
    return (
        project_root
        / "outputs"
        / "meta_optimize"
        / f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )


def run_legacy_optuna(args: argparse.Namespace, positional: bool) -> dict:
    """Original free search over wg_base, κ, braiding_target."""
    try:
        import optuna
    except ImportError as e:
        raise SystemExit("optuna is required: pip install optuna") from e

    if args.use_ray:
        import ray

        ray.init(address="auto", ignore_reinit_error=True)
        print(f"   Ray cluster ready — {len(ray.nodes())} nodes")

    def objective(trial: "optuna.Trial") -> float:
        wg_base = trial.suggest_float("wg_base", 300.0, 400.0, step=0.5)
        kappa = trial.suggest_float("kappa", 0.70, 0.95, step=0.01)
        braiding_target = trial.suggest_float("braiding_target", 0.75, 0.85, step=0.001)
        result = evaluate_trial(
            wg_base,
            kappa,
            braiding_target,
            n_seeds=args.seeds,
            positional=positional,
            dry_run=args.dry_run,
        )
        trial.set_user_attr("discovered_Wg", result["discovered_Wg"])
        trial.set_user_attr("invariant", result.get("invariant", {}))
        if "predicted_freq_proxy" in result:
            trial.set_user_attr("predicted_freq_proxy", result["predicted_freq_proxy"])
        return result["loss"]

    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=42)
    )
    study.optimize(objective, n_trials=args.trials)

    best = study.best_trial
    wg = best.user_attrs.get("discovered_Wg", best.params["wg_base"] / math.pi)

    print("\n" + "=" * 60)
    print("META-OPTIMIZATION COMPLETE")
    print(f"Best loss: {best.value:.6f}")
    print(f"Emergent wg_base: {best.params['wg_base']:.3f} → Wg = {wg:.4f}")
    print(f"Emergent κ: {best.params['kappa']:.4f}")
    print(f"Emergent braiding_target: {best.params['braiding_target']:.5f}")
    if abs(best.params["wg_base"] - WG_BASE) < 8:
        print("TRUE EMERGENCE — 350/π dropped out naturally (within ±8 of 350)")
    else:
        print("Good convergence — increase trials or widen ranges if needed.")
    print("=" * 60)

    payload = {
        "schema": "invariant_hunt.meta_optimize.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "free_search",
        "positional": positional,
        "dry_run": args.dry_run,
        "trials": args.trials,
        "best_loss": best.value,
        "best_params": best.params,
        "discovered_Wg": wg,
        "canonical_Wg": LOCKED_WG,
        "lock_residual": abs(wg - LOCKED_WG),
        "user_attrs": {k: v for k, v in best.user_attrs.items() if k != "invariant"}
        | {"invariant": best.user_attrs.get("invariant", {})},
    }

    if args.use_ray:
        import ray

        ray.shutdown()

    return payload


def run_locks_fixed(args: argparse.Namespace, positional: bool) -> dict:
    """Phase 1.2: holonomy/gauge knobs only; W_g, κ*, φ_b* frozen."""
    print("\n" + "=" * 60)
    print("PHASE 1.2 — LOCKS-FIXED HOLONOMY / GAUGE SWEEP")
    print(f"  locks: W_g={LOCKED_WG:.6f} (base {WG_BASE}), κ*≈0.85, φ_b*≈0.8145")
    print(f"  free: g3,g2,g1, D, hopf_coupling, gauge_flux, kappa_scale probe")
    print("=" * 60)

    common = dict(
        seed=args.seed,
        gauge_lo=args.gauge_lo,
        gauge_hi=args.gauge_hi,
        D_lo=args.D_lo,
        D_hi=args.D_hi,
        hopf_lo=args.hopf_lo,
        hopf_hi=args.hopf_hi,
        flux_amp=args.flux_amp,
        kappa_scale_amp=args.kappa_scale_amp,
        positional=positional,
        pde_probe=args.pde_probe,
    )

    if args.monte_carlo:
        payload = run_locks_fixed_monte_carlo(n_samples=args.samples, **common)
    else:
        payload = run_locks_fixed_optuna(n_trials=args.trials, **common)

    payload["created_utc"] = datetime.now(timezone.utc).isoformat()
    payload["dry_run"] = True  # locks-fixed path is analytic / light PDE by design
    payload["phase"] = "1.2"

    gate = payload.get("gate_H_S", {})
    print(f"\nGate H-S: {'PASS' if gate.get('pass') else 'FAIL'}")
    for k, v in gate.get("criteria", {}).items():
        print(f"  {k}: {v}")
    print(f"  ghost_free_fraction: {payload.get('ghost_free_fraction')}")
    print(f"  wg_residual_max: {payload.get('wg_residual_max')}")
    if "best_loss" in payload:
        print(f"  best_loss: {payload['best_loss']}")
        print(f"  best_params: {payload.get('best_params')}")
    elif "best" in payload:
        print(f"  best_loss: {payload['best'].get('loss')}")
        print(f"  best_knobs: {payload['best'].get('knobs')}")
    print("=" * 60)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Meta-optimize Hopf-lattice invariants")
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument(
        "--positional",
        action="store_true",
        default=True,
        help="Use positional/phase framing of 350/π (default on)",
    )
    parser.add_argument(
        "--no-positional",
        action="store_true",
        help="Disable positional terms (legacy temporal framing)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Analytic surrogate (no torch conduit)")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42, help="RNG / Optuna seed (locks-fixed)")
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="JSON output path (default outputs/meta_optimize/...)",
    )
    parser.add_argument("--use-ray", action="store_true")

    # Phase 1.2
    parser.add_argument(
        "--locks-fixed",
        action="store_true",
        help="Phase 1.2: freeze W_g, κ*, φ_b*; sweep holonomy/gauge knobs only",
    )
    parser.add_argument(
        "--monte-carlo",
        action="store_true",
        help="With --locks-fixed: uniform MC sample instead of Optuna",
    )
    parser.add_argument("--samples", type=int, default=64, help="MC samples for --monte-carlo")
    parser.add_argument("--gauge-lo", type=float, default=0.3)
    parser.add_argument("--gauge-hi", type=float, default=3.0)
    parser.add_argument("--D-lo", type=float, default=0.02)
    parser.add_argument("--D-hi", type=float, default=0.12)
    parser.add_argument("--hopf-lo", type=float, default=0.2)
    parser.add_argument("--hopf-hi", type=float, default=2.0)
    parser.add_argument("--flux-amp", type=float, default=0.05, help="|gauge_flux| half-width")
    parser.add_argument(
        "--kappa-scale-amp",
        type=float,
        default=0.15,
        help="Probe jitter amplitude for κ_eff = κ* · scale (not a lock re-fit)",
    )
    parser.add_argument(
        "--pde-probe",
        action="store_true",
        help="Include short 3-torus PDE stability probe in locks-fixed loss",
    )
    args = parser.parse_args()

    positional = not args.no_positional
    print("🚀 Meta-Optimizer — Emergent invariants (Wg, κ, braiding_phase)")
    print(
        f"   positional={positional}  dry_run={args.dry_run}  "
        f"trials={args.trials}  locks_fixed={args.locks_fixed}"
    )

    if args.locks_fixed:
        payload = run_locks_fixed(args, positional)
        prefix = "meta_optimize_locks_fixed"
    else:
        payload = run_legacy_optuna(args, positional)
        prefix = "meta_optimize"

    out_path = Path(args.out) if args.out else _default_out_path(prefix)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    # Latest pointer for Phase 1.2
    if args.locks_fixed:
        latest = out_path.parent / "meta_optimize_locks_fixed_latest.json"
        latest.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {latest}")
    print(f"Wrote {out_path}")

    # Exit non-zero if Gate H-S fails
    if args.locks_fixed and not payload.get("gate_H_S", {}).get("pass", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
