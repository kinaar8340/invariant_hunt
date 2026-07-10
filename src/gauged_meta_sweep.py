"""
Phase 1.2 — locks-fixed holonomy / gauge meta-sweep utilities.

Core invariants (W_g, κ, φ_b) are *frozen inputs*. Trials only vary:
  - Yang–Mills scales g3, g2, g1
  - Dirichlet stiffness D
  - Hopf coupling c_H
  - optional weak gauge_flux source
  - optional *probe* jitter of κ around the lock (not a re-fit of the lock)

Gate H-S (holonomy / gauge stability):
  - W_g residual vs 350/π is identically zero (locks fixed)
  - ghost checks pass for all (or ≥ threshold fraction of) trials
  - holonomy eigenvalue −κ_eff < 0
  - braiding potential minimized at φ_b*
  - surrogate loss remains finite / bounded
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from src.action_principle import (
    DEFAULT_D,
    DEFAULT_DELTA_OMEGA,
    DEFAULT_HOPF_COUPLING,
    ActionParameters,
    GaugeSector,
    check_no_ghosts,
    gauged_twist_force_terms,
    holonomy_potential,
    perturbative_force_linearization,
)
from src.invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
    geometric_winding_from_base,
)
from src.positional import PositionalPhase, positional_hopf_residual


@dataclass
class GaugedSweepKnobs:
    """Perturbation knobs with locks held fixed."""

    g3: float = 1.0
    g2: float = 1.0
    g1: float = 1.0
    D: float = DEFAULT_D
    hopf_coupling: float = DEFAULT_HOPF_COUPLING
    gauge_flux: float = 0.0
    # Optional probe: multiplicative jitter applied to locked κ (stability only)
    kappa_scale: float = 1.0  # effective κ = DEFAULT_KAPPA * kappa_scale

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class LocksFixedTrialResult:
    """Single locks-fixed evaluation."""

    loss: float
    ghost_free: bool
    wg_residual: float
    holonomy_restoring: bool
    braiding_at_minimum: bool
    kappa_eff: float
    knobs: dict[str, float]
    invariant: dict[str, Any]
    components: dict[str, float] = field(default_factory=dict)
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def locked_action_params(knobs: GaugedSweepKnobs) -> ActionParameters:
    """Build ActionParameters with frozen W_g, κ base, φ_b and knob gauges."""
    kappa_eff = max(DEFAULT_KAPPA * knobs.kappa_scale, 1e-9)
    return ActionParameters(
        wg_base=WG_BASE,
        kappa=kappa_eff,
        braiding=DEFAULT_BRAIDING,
        D=float(knobs.D),
        delta_omega=DEFAULT_DELTA_OMEGA,
        hopf_coupling=float(knobs.hopf_coupling),
        gauge=GaugeSector(g3=float(knobs.g3), g2=float(knobs.g2), g1=float(knobs.g1)),
    )


def evaluate_locks_fixed_trial(
    knobs: GaugedSweepKnobs,
    *,
    positional: bool = True,
    pde_probe: bool = False,
    pde_nx: int = 8,
    pde_nt: int = 40,
    pde_dt: float = 0.001,
    seed: int = 0,
) -> LocksFixedTrialResult:
    """Evaluate stability loss with W_g / φ_b* locked; knobs free.

    Loss combines:
      - ghost failure hard penalty
      - positional residual of locked W_g (should be ~0)
      - soft bowl around default g_i=1, D=0.05 (prefer mild gauges, not fit)
      - holonomy potential at attractor (should be ~0)
      - optional short PDE mean-boundedness probe
    """
    params = locked_action_params(knobs)
    ghost = check_no_ghosts(params)
    linear = perturbative_force_linearization(params)

    geo_w = geometric_winding_from_base(WG_BASE)
    wg_res = abs(geo_w - LOCKED_WG)
    pos_res = positional_hopf_residual(geo_w, WG_BASE) if positional else wg_res

    # Braiding pin minimum is analytic at φ_b*
    v_star = holonomy_potential(0.0, DEFAULT_BRAIDING, params)
    v_off = holonomy_potential(0.0, DEFAULT_BRAIDING + 0.05, params)
    braiding_at_min = v_star <= v_off + 1e-15

    # Soft preference for O(1) healthy couplings (not a data fit)
    g_bowl = (
        (knobs.g3 - 1.0) ** 2
        + (knobs.g2 - 1.0) ** 2
        + (knobs.g1 - 1.0) ** 2
        + 10.0 * (knobs.D - DEFAULT_D) ** 2
        + 0.5 * (knobs.hopf_coupling - 1.0) ** 2
        + 2.0 * knobs.gauge_flux**2
        + 5.0 * (knobs.kappa_scale - 1.0) ** 2
    )

    ghost_pen = 0.0 if ghost.healthy else 100.0
    restore_pen = 0.0 if linear["restoring"] else 50.0
    braid_pen = 0.0 if braiding_at_min else 20.0
    lock_pen = 1000.0 * wg_res  # must stay zero under locks-fixed
    pos_pen = 0.5 * pos_res if positional else 0.0
    hol_pen = abs(v_star)

    pde_pen = 0.0
    pde_final_mean = None
    if pde_probe:
        rng = np.random.default_rng(seed)
        theta = rng.uniform(0.1, 1.5, (pde_nx, pde_nx, pde_nx))
        dx = 1.0 / pde_nx
        for _ in range(pde_nt):
            lap = (
                np.roll(theta, 1, 0)
                + np.roll(theta, -1, 0)
                + np.roll(theta, 1, 1)
                + np.roll(theta, -1, 1)
                + np.roll(theta, 1, 2)
                + np.roll(theta, -1, 2)
                - 6 * theta
            ) / dx**2
            g0 = np.gradient(theta, axis=0)
            g1 = np.gradient(theta, axis=1)
            g2 = np.gradient(theta, axis=2)
            grad_sq = g0**2 + g1**2 + g2**2
            terms = gauged_twist_force_terms(
                theta,
                params=params,
                lap=lap,
                grad_sq=grad_sq,
                a_mu_curl_contrib=knobs.gauge_flux,
            )
            theta = np.clip(theta + pde_dt * terms["total"], 0.01, 2 * math.pi - 0.01)
        pde_final_mean = float(theta.mean())
        if not np.isfinite(pde_final_mean):
            pde_pen = 100.0
        elif pde_final_mean <= 0 or pde_final_mean >= 2 * math.pi:
            pde_pen = 50.0
        else:
            # Prefer mild mean twist near drive/κ balance
            target = DEFAULT_DELTA_OMEGA / max(params.kappa, 1e-9)
            pde_pen = 0.5 * (pde_final_mean - target) ** 2

    loss = ghost_pen + restore_pen + braid_pen + lock_pen + pos_pen + hol_pen + g_bowl + pde_pen

    inv = InvariantSet(
        wg_base=WG_BASE,
        kappa=params.kappa,
        braiding_target=DEFAULT_BRAIDING,
        geometric_winding=geo_w,
        braiding_phase=DEFAULT_BRAIDING,
    )
    components = {
        "ghost_pen": ghost_pen,
        "restore_pen": restore_pen,
        "braid_pen": braid_pen,
        "lock_pen": lock_pen,
        "pos_pen": pos_pen,
        "hol_pen": hol_pen,
        "g_bowl": g_bowl,
        "pde_pen": pde_pen,
    }
    if pde_final_mean is not None:
        components["pde_final_mean"] = pde_final_mean

    return LocksFixedTrialResult(
        loss=float(loss),
        ghost_free=bool(ghost.healthy),
        wg_residual=float(wg_res),
        holonomy_restoring=bool(linear["restoring"]),
        braiding_at_minimum=bool(braiding_at_min),
        kappa_eff=float(params.kappa),
        knobs=knobs.to_dict(),
        invariant=inv.to_dict(),
        components=components,
        dry_run=True,
    )


def run_locks_fixed_monte_carlo(
    *,
    n_samples: int = 64,
    seed: int = 42,
    gauge_lo: float = 0.3,
    gauge_hi: float = 3.0,
    D_lo: float = 0.02,
    D_hi: float = 0.12,
    hopf_lo: float = 0.2,
    hopf_hi: float = 2.0,
    flux_amp: float = 0.05,
    kappa_scale_amp: float = 0.15,
    positional: bool = True,
    pde_probe: bool = False,
) -> dict[str, Any]:
    """Monte Carlo holonomy/gauge jitter with locks fixed (Gate H-S sample)."""
    rng = np.random.default_rng(seed)
    results: list[LocksFixedTrialResult] = []

    for i in range(n_samples):
        knobs = GaugedSweepKnobs(
            g3=float(rng.uniform(gauge_lo, gauge_hi)),
            g2=float(rng.uniform(gauge_lo, gauge_hi)),
            g1=float(rng.uniform(gauge_lo, gauge_hi)),
            D=float(rng.uniform(D_lo, D_hi)),
            hopf_coupling=float(rng.uniform(hopf_lo, hopf_hi)),
            gauge_flux=float(rng.uniform(-flux_amp, flux_amp)),
            kappa_scale=float(
                max(1e-3, 1.0 + kappa_scale_amp * rng.normal())
            ),
        )
        results.append(
            evaluate_locks_fixed_trial(
                knobs,
                positional=positional,
                pde_probe=pde_probe,
                seed=seed + i,
            )
        )

    losses = np.array([r.loss for r in results], dtype=float)
    ghost_frac = float(np.mean([r.ghost_free for r in results]))
    wg_max = float(max(r.wg_residual for r in results))
    restore_frac = float(np.mean([r.holonomy_restoring for r in results]))
    braid_frac = float(np.mean([r.braiding_at_minimum for r in results]))
    best = min(results, key=lambda r: r.loss)

    # Gate H-S: locks intact, all healthy under sampled jitter band
    gate_pass = bool(
        wg_max < 1e-12
        and ghost_frac >= 1.0
        and restore_frac >= 1.0
        and braid_frac >= 1.0
        and np.isfinite(losses).all()
        and float(losses.max()) < 1e3
    )

    return {
        "schema": "invariant_hunt.gauged_meta_sweep.v1",
        "mode": "locks_fixed_monte_carlo",
        "n_samples": n_samples,
        "seed": seed,
        "locks": {
            "wg_base": WG_BASE,
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "ranges": {
            "g_i": [gauge_lo, gauge_hi],
            "D": [D_lo, D_hi],
            "hopf_coupling": [hopf_lo, hopf_hi],
            "gauge_flux_amp": flux_amp,
            "kappa_scale_amp": kappa_scale_amp,
        },
        "ghost_free_fraction": ghost_frac,
        "holonomy_restoring_fraction": restore_frac,
        "braiding_min_fraction": braid_frac,
        "wg_residual_max": wg_max,
        "loss_mean": float(losses.mean()),
        "loss_std": float(losses.std()),
        "loss_max": float(losses.max()),
        "loss_min": float(losses.min()),
        "best": best.to_dict(),
        "gate_H_S": {
            "pass": gate_pass,
            "criteria": {
                "wg_residual_zero": wg_max < 1e-12,
                "all_ghost_free": ghost_frac >= 1.0,
                "all_holonomy_restoring": restore_frac >= 1.0,
                "all_braiding_at_min": braid_frac >= 1.0,
                "loss_finite_bounded": bool(np.isfinite(losses).all() and losses.max() < 1e3),
            },
        },
        "positional": positional,
        "pde_probe": pde_probe,
    }


def run_locks_fixed_optuna(
    *,
    n_trials: int = 40,
    seed: int = 42,
    gauge_lo: float = 0.3,
    gauge_hi: float = 3.0,
    D_lo: float = 0.02,
    D_hi: float = 0.12,
    hopf_lo: float = 0.2,
    hopf_hi: float = 2.0,
    flux_amp: float = 0.05,
    kappa_scale_amp: float = 0.15,
    positional: bool = True,
    pde_probe: bool = False,
) -> dict[str, Any]:
    """Optuna sweep over gauge knobs with W_g, κ*, φ_b* locked."""
    try:
        import optuna
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("optuna required for locks-fixed optuna sweep") from e

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    trial_rows: list[dict[str, Any]] = []

    def objective(trial: "optuna.Trial") -> float:
        knobs = GaugedSweepKnobs(
            g3=trial.suggest_float("g3", gauge_lo, gauge_hi),
            g2=trial.suggest_float("g2", gauge_lo, gauge_hi),
            g1=trial.suggest_float("g1", gauge_lo, gauge_hi),
            D=trial.suggest_float("D", D_lo, D_hi),
            hopf_coupling=trial.suggest_float("hopf_coupling", hopf_lo, hopf_hi),
            gauge_flux=trial.suggest_float("gauge_flux", -flux_amp, flux_amp),
            kappa_scale=trial.suggest_float(
                "kappa_scale", 1.0 - kappa_scale_amp, 1.0 + kappa_scale_amp
            ),
        )
        res = evaluate_locks_fixed_trial(
            knobs,
            positional=positional,
            pde_probe=pde_probe,
            seed=seed + trial.number,
        )
        trial.set_user_attr("ghost_free", res.ghost_free)
        trial.set_user_attr("wg_residual", res.wg_residual)
        trial.set_user_attr("kappa_eff", res.kappa_eff)
        trial.set_user_attr("components", res.components)
        trial_rows.append(res.to_dict())
        return res.loss

    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed)
    )
    study.optimize(objective, n_trials=n_trials)

    best = study.best_trial
    ghost_frac = float(np.mean([r["ghost_free"] for r in trial_rows])) if trial_rows else 0.0
    wg_max = float(max(r["wg_residual"] for r in trial_rows)) if trial_rows else math.inf
    restore_frac = float(np.mean([r["holonomy_restoring"] for r in trial_rows])) if trial_rows else 0.0
    braid_frac = float(np.mean([r["braiding_at_minimum"] for r in trial_rows])) if trial_rows else 0.0
    losses = np.array([r["loss"] for r in trial_rows], dtype=float) if trial_rows else np.array([math.inf])

    gate_pass = bool(
        wg_max < 1e-12
        and ghost_frac >= 1.0
        and restore_frac >= 1.0
        and braid_frac >= 1.0
        and np.isfinite(losses).all()
        and float(losses.max()) < 1e3
    )

    return {
        "schema": "invariant_hunt.gauged_meta_sweep.v1",
        "mode": "locks_fixed_optuna",
        "n_trials": n_trials,
        "seed": seed,
        "locks": {
            "wg_base": WG_BASE,
            "W_g": LOCKED_WG,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "best_loss": float(best.value) if best.value is not None else None,
        "best_params": dict(best.params),
        "best_user_attrs": {
            k: v for k, v in best.user_attrs.items() if k != "components"
        },
        "ghost_free_fraction": ghost_frac,
        "holonomy_restoring_fraction": restore_frac,
        "braiding_min_fraction": braid_frac,
        "wg_residual_max": wg_max,
        "loss_mean": float(losses.mean()),
        "loss_max": float(losses.max()),
        "gate_H_S": {
            "pass": gate_pass,
            "criteria": {
                "wg_residual_zero": wg_max < 1e-12,
                "all_ghost_free": ghost_frac >= 1.0,
                "all_holonomy_restoring": restore_frac >= 1.0,
                "all_braiding_at_min": braid_frac >= 1.0,
                "loss_finite_bounded": bool(np.isfinite(losses).all() and losses.max() < 1e3),
            },
        },
        "positional": positional,
        "pde_probe": pde_probe,
        "canonical_Wg": LOCKED_WG,
        "lock_residual": 0.0,
        "phase": {
            "wg": LOCKED_WG,
            "alignment": float(PositionalPhase(wg=LOCKED_WG).alignment_to_canonical()),
        },
    }
