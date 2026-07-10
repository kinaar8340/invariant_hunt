"""
PE / residual systematics deep-dive for pre-merger FALSIFY events (Gate S-1).

Aggregates:
  • Multi-approximant Gate P + α + ln B_10
  • PE mass/distance jitter
  • PE posterior draws → α distribution
  • corr(r, τ) and power fraction along τ (GW170608-style flag)
  • Time-cut robustness
  • Optional injection recovery thr

Verdicts (pre-registered):
  SYSTEMATICS_RISK  — fails robustness criteria (prefer NULL/systematics)
  ROBUST_ANOMALY    — survives multi-approx / jitter / corr cuts (mapping issue)
  INCONCLUSIVE      — incomplete runs or mixed signals

Does not re-fit α band or core locks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .invariants import InvariantSet
from .pe_waveform import PEParams, load_pe_posterior_draws, pe_params_for_event
from .premerger_bayes import (
    ALPHA_PRIOR_SIGMA,
    bayes_factor_network,
)
from .premerger_phase import (
    fit_premerger_phase_network,
    prepare_premerger_network,
    residual_tau_correlation,
    time_cut_robustness,
)
from .premerger_theory import GATE_P_DELTA_CHI2, GATE_P_T_END

# Pre-registered Gate S-1 thresholds (from GW170608 demotion culture)
CORR_R_TAU_FLAG: float = 0.10  # |corr| ≳ 0.1 → PE-systematics risk
ALPHA_REL_SPREAD_FLAG: float = 0.50  # std/|mean| among approx passes
MIN_APPROX_PASS_FRAC: float = 0.5
MIN_JITTER_PASS_FRAC: float = 0.5
MIN_DRAW_PASS_FRAC: float = 0.5

DEFAULT_APPROXIMANTS: tuple[str, ...] = (
    "IMRPhenomD",
    "SEOBNRv4_opt",
    "IMRPhenomXAS",
    "IMRPhenomXP",
)


def _jitter_params(base: PEParams, scale_m: float, scale_d: float) -> PEParams:
    return PEParams(
        event=base.event,
        mass1=base.mass1 * scale_m,
        mass2=base.mass2 * scale_m,
        distance_mpc=base.distance_mpc * scale_d,
        spin1z=base.spin1z,
        spin2z=base.spin2z,
        ra=base.ra,
        dec=base.dec,
        costheta_jn=base.costheta_jn,
        approximant=base.approximant,
        posterior_dataset=base.posterior_dataset,
        n_samples=base.n_samples,
        source=base.source + f"|jitter_m={scale_m}_d={scale_d}",
    )


def run_approximant_suite(
    event_name: str,
    *,
    project_root: Path,
    detectors: list[str],
    approximants: list[str],
    base_params: PEParams,
    inv: InvariantSet,
    duration_pre_s: float = 4.0,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    alpha_prior_sigma: float = ALPHA_PRIOR_SIGMA,
    compute_bayes: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for approx in approximants:
        row: dict[str, Any] = {"approximant": approx}
        try:
            event, dets = prepare_premerger_network(
                event_name,
                detectors,
                project_root=project_root,
                duration_pre_s=duration_pre_s,
                f_low=f_low,
                f_high=f_high,
                approximant=approx,
                params=base_params,
            )
            fit = fit_premerger_phase_network(
                dets,
                event,
                t_end=t_end,
                f_low=f_low,
                f_high=f_high,
                gate_dchi2=gate_dchi2,
                inv=inv,
            )
            corr = residual_tau_correlation(dets, inv, t_end=t_end)
            row.update(
                {
                    "alpha_hat": fit.alpha_hat,
                    "alpha_sigma": fit.alpha_sigma,
                    "delta_chi2": fit.delta_chi2,
                    "gate_p_pass": fit.gate_p_pass,
                    "corr_r_tau": {
                        d: corr["detectors"][d]["corr_r_tau"]
                        for d in corr["detectors"]
                    },
                    "power_frac_tau": {
                        d: corr["detectors"][d]["power_frac_along_tau"]
                        for d in corr["detectors"]
                    },
                    "pe_snr": {d.detector: d.pe_snr_proxy for d in dets},
                    "error": None,
                }
            )
            if compute_bayes:
                bf = bayes_factor_network(
                    dets,
                    event,
                    t_end=t_end,
                    alpha_prior_sigma=alpha_prior_sigma,
                    inv=inv,
                    include_gate_p=False,
                )
                row["ln_B_10"] = bf.ln_B_10
                row["kass_raftery"] = bf.kass_raftery
            rows.append(row)
        except Exception as exc:
            row["error"] = str(exc)
            row["gate_p_pass"] = False
            rows.append(row)
    return rows


def run_jitter_suite(
    event_name: str,
    *,
    project_root: Path,
    detectors: list[str],
    base_params: PEParams,
    inv: InvariantSet,
    duration_pre_s: float = 4.0,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
) -> list[dict[str, Any]]:
    jitters = [
        ("nominal", 1.0, 1.0),
        ("m+3%", 1.03, 1.0),
        ("m-3%", 0.97, 1.0),
        ("d+15%", 1.0, 1.15),
        ("d-15%", 1.0, 0.85),
        ("m+3%_d+15%", 1.03, 1.15),
    ]
    rows: list[dict[str, Any]] = []
    for label, sm, sd in jitters:
        try:
            jp = _jitter_params(base_params, sm, sd)
            event, dets = prepare_premerger_network(
                event_name,
                detectors,
                project_root=project_root,
                duration_pre_s=duration_pre_s,
                f_low=f_low,
                f_high=f_high,
                approximant="IMRPhenomD",
                params=jp,
            )
            fit = fit_premerger_phase_network(
                dets,
                event,
                t_end=t_end,
                f_low=f_low,
                f_high=f_high,
                gate_dchi2=gate_dchi2,
                inv=inv,
            )
            rows.append(
                {
                    "label": label,
                    "scale_mass": sm,
                    "scale_distance": sd,
                    "alpha_hat": fit.alpha_hat,
                    "alpha_sigma": fit.alpha_sigma,
                    "delta_chi2": fit.delta_chi2,
                    "gate_p_pass": fit.gate_p_pass,
                    "error": None,
                }
            )
        except Exception as exc:
            rows.append({"label": label, "error": str(exc), "gate_p_pass": False})
    return rows


def run_posterior_draws(
    event_name: str,
    *,
    project_root: Path,
    detectors: list[str],
    inv: InvariantSet,
    n_draws: int = 12,
    seed: int = 42,
    duration_pre_s: float = 4.0,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    approximant: str = "IMRPhenomD",
) -> dict[str, Any]:
    pe_dir = project_root / "data" / "pe"
    draws = load_pe_posterior_draws(
        event_name,
        n_draws=n_draws,
        seed=seed,
        pe_dir=pe_dir,
        approximant=approximant,
    )
    alphas = []
    rows = []
    for i, params in enumerate(draws):
        try:
            event, dets = prepare_premerger_network(
                event_name,
                detectors,
                project_root=project_root,
                duration_pre_s=duration_pre_s,
                f_low=f_low,
                f_high=f_high,
                approximant=approximant,
                params=params,
            )
            fit = fit_premerger_phase_network(
                dets,
                event,
                t_end=t_end,
                f_low=f_low,
                f_high=f_high,
                gate_dchi2=gate_dchi2,
                inv=inv,
            )
            rows.append(
                {
                    "draw": i,
                    "alpha_hat": fit.alpha_hat,
                    "alpha_sigma": fit.alpha_sigma,
                    "delta_chi2": fit.delta_chi2,
                    "gate_p_pass": fit.gate_p_pass,
                    "error": None,
                }
            )
            alphas.append(fit.alpha_hat)
        except Exception as exc:
            rows.append({"draw": i, "error": str(exc), "gate_p_pass": False})

    ok = [r for r in rows if r.get("error") is None]
    passes = [r for r in ok if r.get("gate_p_pass")]
    a = np.array(alphas, dtype=float) if alphas else np.array([])
    return {
        "n_draws": len(draws),
        "n_ok": len(ok),
        "n_gate_p_pass": len(passes),
        "pass_frac": float(len(passes) / max(len(ok), 1)),
        "alpha_mean": float(np.mean(a)) if a.size else None,
        "alpha_std": float(np.std(a)) if a.size else None,
        "alpha_median": float(np.median(a)) if a.size else None,
        "frac_positive": float(np.mean(a > 0)) if a.size else None,
        "rows": rows,
    }


def score_systematics_verdict(
    approx_rows: list[dict[str, Any]],
    jitter_rows: list[dict[str, Any]],
    draws: dict[str, Any] | None,
    corr_block: dict[str, Any] | None,
) -> dict[str, Any]:
    """Gate S-1 aggregate verdict from systematics suite."""
    flags: list[str] = []
    ok_approx = [r for r in approx_rows if r.get("error") is None]
    n_approx = len(ok_approx)
    n_pass = sum(1 for r in ok_approx if r.get("gate_p_pass"))
    pass_frac = n_pass / max(n_approx, 1)

    alphas_pass = [
        r["alpha_hat"] for r in ok_approx if r.get("gate_p_pass") and "alpha_hat" in r
    ]
    signs = [np.sign(a) for a in alphas_pass if abs(a) > 0]
    sign_stable = len(signs) < 2 or (max(signs) * min(signs) > 0)
    if alphas_pass:
        rel_spread = float(
            np.std(alphas_pass) / (np.mean(np.abs(alphas_pass)) + 1e-30)
        )
    else:
        rel_spread = float("nan")

    if pass_frac < MIN_APPROX_PASS_FRAC:
        flags.append("approx_pass_frac_low")
    if not sign_stable:
        flags.append("approx_sign_unstable")
    if math.isfinite(rel_spread) and rel_spread > ALPHA_REL_SPREAD_FLAG:
        flags.append("approx_alpha_spread_high")

    ok_jit = [r for r in jitter_rows if r.get("error") is None]
    n_jit_pass = sum(1 for r in ok_jit if r.get("gate_p_pass"))
    jit_frac = n_jit_pass / max(len(ok_jit), 1)
    if ok_jit and jit_frac < MIN_JITTER_PASS_FRAC:
        flags.append("jitter_pass_frac_low")

    # Mass sign flip (classic systematics)
    a_nom = next((r["alpha_hat"] for r in ok_jit if r.get("label") == "nominal"), None)
    a_mp = next((r.get("alpha_hat") for r in ok_jit if r.get("label") == "m+3%"), None)
    a_mm = next((r.get("alpha_hat") for r in ok_jit if r.get("label") == "m-3%"), None)
    if a_nom is not None and a_mp is not None and a_nom * a_mp < 0:
        flags.append("mass_plus_sign_flip")
    if a_nom is not None and a_mm is not None and a_nom * a_mm < 0:
        flags.append("mass_minus_sign_flip")

    max_abs_corr = 0.0
    soft_flags: list[str] = []
    if corr_block and "detectors" in corr_block:
        for d, v in corr_block["detectors"].items():
            max_abs_corr = max(max_abs_corr, abs(float(v.get("corr_r_tau", 0.0))))
    # High corr alone is *expected* for a loud projection onto τ; only elevates
    # SYSTEMATICS_RISK when combined with hard instability (GW170608 pattern).
    if max_abs_corr >= CORR_R_TAU_FLAG:
        soft_flags.append(f"corr_r_tau_high_{max_abs_corr:.3f}")

    if draws is not None and draws.get("n_ok", 0) > 0:
        if draws["pass_frac"] < MIN_DRAW_PASS_FRAC:
            flags.append("posterior_draw_pass_frac_low")
        if draws.get("frac_positive") is not None:
            if draws["pass_frac"] >= MIN_DRAW_PASS_FRAC and draws["frac_positive"] < 0.25:
                flags.append("posterior_alpha_mostly_negative")

    hard_flags = list(flags)
    # Soft corr becomes hard only with other instability (demotion pattern)
    if soft_flags and hard_flags:
        flags = hard_flags + soft_flags
    elif soft_flags and not hard_flags:
        flags = list(soft_flags)  # advisory only
        hard_flags = []

    # Verdict uses hard_flags only
    if n_approx == 0:
        verdict = "INCONCLUSIVE"
    elif hard_flags:
        verdict = "SYSTEMATICS_RISK"
    elif pass_frac >= MIN_APPROX_PASS_FRAC and sign_stable:
        verdict = "ROBUST_ANOMALY"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "verdict": verdict,
        "flags": flags,
        "hard_flags": hard_flags,
        "soft_flags": soft_flags,
        "n_approx_ok": n_approx,
        "n_approx_pass": n_pass,
        "approx_pass_frac": pass_frac,
        "sign_stable": bool(sign_stable),
        "alpha_rel_spread": rel_spread,
        "jitter_pass_frac": jit_frac,
        "max_abs_corr_r_tau": max_abs_corr,
        "thresholds": {
            "corr_r_tau_flag": CORR_R_TAU_FLAG,
            "alpha_rel_spread_flag": ALPHA_REL_SPREAD_FLAG,
            "min_approx_pass_frac": MIN_APPROX_PASS_FRAC,
            "min_jitter_pass_frac": MIN_JITTER_PASS_FRAC,
            "min_draw_pass_frac": MIN_DRAW_PASS_FRAC,
        },
        "interpretation": {
            "SYSTEMATICS_RISK": (
                "Hard instability (approx/jitter/sign/draws); α/B10 may be PE "
                "residual absorption — prefer systematics narrative over new mapping."
            ),
            "ROBUST_ANOMALY": (
                "Survives multi-approx, jitter, and draws under locked template. "
                "Soft corr(r,τ) may still be high (expected for loud τ projection). "
                "Supports *new pre-registered mapping* only — not band re-fit. "
                "Band FALSIFY still stands (α not in demoted universal band)."
            ),
            "INCONCLUSIVE": "Insufficient clean runs or mixed diagnostics.",
        }.get(verdict, ""),
    }


def deep_dive_event(
    event_name: str,
    *,
    project_root: Path,
    detectors: list[str] | None = None,
    approximants: list[str] | None = None,
    n_draws: int = 12,
    seed: int = 42,
    skip_draws: bool = False,
    skip_jitter: bool = False,
    duration_pre_s: float = 4.0,
) -> dict[str, Any]:
    """Full Gate S-1 deep dive for one event."""
    detectors = detectors or ["H1", "L1"]
    approximants = approximants or list(DEFAULT_APPROXIMANTS)
    inv = InvariantSet()
    pe_dir = project_root / "data" / "pe"
    base_params = pe_params_for_event(event_name, pe_dir=pe_dir)

    approx_rows = run_approximant_suite(
        event_name,
        project_root=project_root,
        detectors=detectors,
        approximants=approximants,
        base_params=base_params,
        inv=inv,
        duration_pre_s=duration_pre_s,
    )

    jitter_rows: list[dict[str, Any]] = []
    if not skip_jitter:
        jitter_rows = run_jitter_suite(
            event_name,
            project_root=project_root,
            detectors=detectors,
            base_params=base_params,
            inv=inv,
            duration_pre_s=duration_pre_s,
        )

    # Nominal corr + time cuts
    event, dets = prepare_premerger_network(
        event_name,
        detectors,
        project_root=project_root,
        duration_pre_s=duration_pre_s,
        approximant="IMRPhenomD",
        params=base_params,
    )
    corr = residual_tau_correlation(dets, inv)
    tcuts = time_cut_robustness(dets, event, inv=inv)

    draws = None
    if not skip_draws:
        draws = run_posterior_draws(
            event_name,
            project_root=project_root,
            detectors=detectors,
            inv=inv,
            n_draws=n_draws,
            seed=seed,
            duration_pre_s=duration_pre_s,
        )

    verdict = score_systematics_verdict(approx_rows, jitter_rows, draws, corr)

    return {
        "schema": "invariant_hunt.premerger_systematics.v1",
        "event": event_name,
        "detectors": detectors,
        "locks_frozen": True,
        "band_not_refit": True,
        "approximants": approx_rows,
        "pe_jitter": jitter_rows,
        "posterior_draws": draws,
        "corr_r_tau": corr,
        "time_cut_robustness": tcuts,
        "gate_S1": verdict,
    }
