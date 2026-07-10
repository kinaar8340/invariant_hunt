"""
Fit / bound pre-merger topological phase coupling α on whitened strain.

Pipeline:
  1. Load long pre-merger + merger window, whiten (reuse network stack)
  2. Fit PE IMR in whitened domain (lag + A+, Ax)
  3. On inspiral samples (t < t_end): residual r vs phase basis τ(α)
  4. Fit α: r ≈ α · τ   (or joint a0 leftover + α)
  5. Report Δχ², α_hat, Gate P
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .coherent_echo import fit_linear_combo, fit_amplitude, chi2
from .echo_ladder import fit_amplitude as _fa  # noqa: F401
from .gw_events import PublicGWEvent, get_event
from .invariants import InvariantSet
from .network_likelihood import DetectorWhitened, prepare_detector, prepare_network
from .pe_waveform import pe_params_for_event
from .premerger_theory import (
    GATE_P_DELTA_CHI2,
    GATE_P_T_END,
    PremergerPhaseModel,
    orbital_phase_from_strain,
    phase_basis_template,
)
from .whiten import apply_same_whiten


@dataclass
class PremergerFitResult:
    event: str
    detector: str | None
    alpha_hat: float
    alpha_sigma: float
    chi2_base: float
    chi2_topo: float
    delta_chi2: float
    n_inspiral: int
    t_end: float
    f_low: float
    f_high: float
    pe_snr: float
    gate_p_pass: bool
    model: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "detector": self.detector,
            "alpha_hat": self.alpha_hat,
            "alpha_sigma": self.alpha_sigma,
            "chi2_base": self.chi2_base,
            "chi2_topo": self.chi2_topo,
            "delta_chi2": self.delta_chi2,
            "n_inspiral": self.n_inspiral,
            "t_end": self.t_end,
            "f_band_hz": [self.f_low, self.f_high],
            "pe_snr": self.pe_snr,
            "gate_p_pass": self.gate_p_pass,
            "model": self.model,
            "notes": self.notes,
        }


def _inspiral_mask(t_rel: np.ndarray, t_end: float = GATE_P_T_END) -> np.ndarray:
    return t_rel < t_end


def fit_premerger_phase_single(
    det: DetectorWhitened,
    event: PublicGWEvent,
    *,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    inv: InvariantSet | None = None,
) -> PremergerFitResult:
    """Fit α on one detector's whitened PE residual in the inspiral window."""
    inv = inv or InvariantSet()
    model = PremergerPhaseModel.from_invariants(inv)
    t = det.t_rel
    mask = _inspiral_mask(t, t_end)
    if int(np.sum(mask)) < 64:
        raise RuntimeError("inspiral window too short — increase duration_pre_s")

    # GR template already whitened as pe_template_w; residual = data - GR
    h_gr = det.pe_template_w
    residual = det.residual_w
    # orbital phase from GR template (full window), then restrict
    phi_orb = orbital_phase_from_strain(
        h_gr, det.sample_rate, t_rel=t, t_ref=0.0
    )
    tau = phase_basis_template(h_gr, phi_orb, model)

    # Optional re-whiten consistency: tau already in same domain as h_gr
    r_i = residual[mask]
    tau_i = tau[mask]
    # baseline: residual ≈ 0 (GR already subtracted); optional constant amp leftover
    # use pure α fit on residual: r ≈ α τ
    # Also allow tiny leftover scale on GR in inspiral: r + a0 h ≈ α τ
    # → a0 h_i + α τ_i ≈ r is wrong; residual is already d - GR
    # Fit: r_i ≈ α τ_i
    denom = float(np.sum(tau_i * tau_i)) + 1e-60
    alpha_hat = float(np.sum(r_i * tau_i) / denom)
    # white unit variance after whitening
    sigma = 1.0
    alpha_sigma = float(sigma / math.sqrt(denom))

    pred = alpha_hat * tau_i
    chi_base = float(np.sum(r_i**2))  # null: no topo term
    chi_topo = float(np.sum((r_i - pred) ** 2))
    dchi = chi_base - chi_topo

    notes = [
        f"Inspiral samples: {int(np.sum(mask))} with t < {t_end}",
        f"K = W_g cos(φ_b) = {model.coupling_kernel():.4f}",
        f"α_hat / σ_α = {alpha_hat / alpha_sigma:.3f}" if alpha_sigma > 0 else "α unconstrained",
    ]
    if abs(alpha_hat) < 3.0 * alpha_sigma:
        notes.append("|α| < 3σ — no significant phase coupling under this form")
    if dchi < gate_dchi2:
        notes.append(f"Δχ²={dchi:.2f} < Gate P thr {gate_dchi2}")

    return PremergerFitResult(
        event=event.name,
        detector=det.detector,
        alpha_hat=alpha_hat,
        alpha_sigma=alpha_sigma,
        chi2_base=chi_base,
        chi2_topo=chi_topo,
        delta_chi2=dchi,
        n_inspiral=int(np.sum(mask)),
        t_end=t_end,
        f_low=f_low,
        f_high=f_high,
        pe_snr=det.pe_snr_proxy,
        gate_p_pass=bool(
            dchi >= gate_dchi2 and abs(alpha_hat) > 2.0 * alpha_sigma
        ),
        model=model.to_dict(),
        notes=notes,
    )


def fit_premerger_phase_network(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    *,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    inv: InvariantSet | None = None,
) -> PremergerFitResult:
    """Shared α across detectors; stack whitened inspiral residuals."""
    inv = inv or InvariantSet()
    model = PremergerPhaseModel.from_invariants(inv)

    r_list = []
    tau_list = []
    pe_snrs = []
    n_insp = 0
    for det in dets:
        t = det.t_rel
        mask = _inspiral_mask(t, t_end)
        h_gr = det.pe_template_w
        phi_orb = orbital_phase_from_strain(
            h_gr, det.sample_rate, t_rel=t, t_ref=0.0
        )
        tau = phase_basis_template(h_gr, phi_orb, model)
        r_list.append(det.residual_w[mask])
        tau_list.append(tau[mask])
        pe_snrs.append(det.pe_snr_proxy)
        n_insp += int(np.sum(mask))

    r = np.concatenate(r_list)
    tau = np.concatenate(tau_list)
    denom = float(np.sum(tau * tau)) + 1e-60
    alpha_hat = float(np.sum(r * tau) / denom)
    alpha_sigma = float(1.0 / math.sqrt(denom))
    pred = alpha_hat * tau
    chi_base = float(np.sum(r**2))
    chi_topo = float(np.sum((r - pred) ** 2))
    dchi = chi_base - chi_topo

    notes = [
        f"Network detectors: {[d.detector for d in dets]}",
        f"Inspiral samples (stacked): {n_insp}",
        f"K = {model.coupling_kernel():.4f}",
        f"α_hat = {alpha_hat:.3e} ± {alpha_sigma:.3e}",
    ]

    # Per-detector α for sign-consistency check (systematics flag)
    det_alphas = []
    for det in dets:
        t = det.t_rel
        mask = _inspiral_mask(t, t_end)
        h_gr = det.pe_template_w
        phi_orb = orbital_phase_from_strain(
            h_gr, det.sample_rate, t_rel=t, t_ref=0.0
        )
        tau_d = phase_basis_template(h_gr, phi_orb, model)[mask]
        r_d = det.residual_w[mask]
        den = float(np.sum(tau_d * tau_d)) + 1e-60
        a_d = float(np.sum(r_d * tau_d) / den)
        sig_d = float(1.0 / math.sqrt(den))
        det_alphas.append((det.detector, a_d, sig_d))

    signs = [np.sign(a) for _, a, s in det_alphas if abs(a) > 2.0 * s]
    sign_consistent = len(signs) < 2 or (max(signs) * min(signs) > 0)
    if not sign_consistent:
        notes.append(
            "H1/L1 α signs disagree at >2σ — treat as systematics; Gate P fail"
        )
    for det_name, a_d, sig_d in det_alphas:
        notes.append(f"{det_name} α={a_d:.3e}±{sig_d:.3e}")

    gate = (
        dchi >= gate_dchi2
        and abs(alpha_hat) > 2.0 * alpha_sigma
        and sign_consistent
    )

    return PremergerFitResult(
        event=event.name,
        detector="+".join(d.detector for d in dets),
        alpha_hat=alpha_hat,
        alpha_sigma=alpha_sigma,
        chi2_base=chi_base,
        chi2_topo=chi_topo,
        delta_chi2=dchi,
        n_inspiral=n_insp,
        t_end=t_end,
        f_low=f_low,
        f_high=f_high,
        pe_snr=float(np.mean(pe_snrs)),
        gate_p_pass=bool(gate),
        model=model.to_dict(),
        notes=notes,
    )


def prepare_premerger_network(
    event_name: str,
    detectors: list[str],
    *,
    project_root: Path,
    duration_pre_s: float = 4.0,
    duration_post_s: float = 0.05,
    f_low: float = 20.0,
    f_high: float = 100.0,
    approximant: str | None = None,
    params: "PEParams | None" = None,
) -> tuple[PublicGWEvent, list[DetectorWhitened]]:
    """Long pre-merger window for inspiral phase analysis.

    ``approximant`` overrides the PE waveform family (e.g. IMRPhenomD,
    SEOBNRv4_opt, IMRPhenomXAS). ``params`` allows PE mass/distance jitter.
    """
    from .pe_waveform import PEParams  # local import for type

    event = get_event(event_name)
    pe_dir = project_root / "data" / "pe"
    cache = project_root / "data" / "gwosc"
    if params is None:
        params = pe_params_for_event(event.name, pe_dir=pe_dir)
    if approximant is not None:
        # dataclass may be frozen-like; PEParams is not frozen
        params = PEParams(
            event=params.event,
            mass1=params.mass1,
            mass2=params.mass2,
            distance_mpc=params.distance_mpc,
            spin1z=params.spin1z,
            spin2z=params.spin2z,
            ra=params.ra,
            dec=params.dec,
            costheta_jn=params.costheta_jn,
            approximant=approximant,
            posterior_dataset=params.posterior_dataset,
            n_samples=params.n_samples,
            source=params.source,
        )
    dets = [
        prepare_detector(
            event,
            det,
            params,
            cache_dir=cache,
            f_low=f_low,
            f_high=f_high,
            duration_pre_s=duration_pre_s,
            duration_post_s=duration_post_s,
            psd_pre_end=-0.5,  # PSD from earlier than inspiral fit end
            psd_duration_s=8.0,
            approximant=approximant or params.approximant,
        )
        for det in detectors
    ]
    return event, dets


def _clone_with_residual(det: DetectorWhitened, residual_w: np.ndarray) -> DetectorWhitened:
    return DetectorWhitened(
        detector=det.detector,
        t_rel=det.t_rel,
        strain_raw=det.strain_raw,
        strain_w=det.strain_w,
        residual_w=residual_w,
        pe_template_w=det.pe_template_w,
        psd=det.psd,
        whiten_scale=det.whiten_scale,
        pe_lag_s=det.pe_lag_s,
        pe_a_plus=det.pe_a_plus,
        pe_a_cross=det.pe_a_cross,
        pe_chi2=det.pe_chi2,
        pe_snr_proxy=det.pe_snr_proxy,
        sample_rate=det.sample_rate,
        path=det.path,
    )


def network_tau_templates(
    dets: list[DetectorWhitened],
    inv: InvariantSet | None = None,
    *,
    t_end: float = GATE_P_T_END,
) -> tuple[list[np.ndarray], PremergerPhaseModel]:
    """Per-detector full-window phase basis τ (same length as residual_w)."""
    inv = inv or InvariantSet()
    model = PremergerPhaseModel.from_invariants(inv)
    taus = []
    for det in dets:
        phi_orb = orbital_phase_from_strain(
            det.pe_template_w, det.sample_rate, t_rel=det.t_rel, t_ref=0.0
        )
        taus.append(phase_basis_template(det.pe_template_w, phi_orb, model))
    return taus, model


def residual_tau_correlation(
    dets: list[DetectorWhitened],
    inv: InvariantSet | None = None,
    *,
    t_end: float = GATE_P_T_END,
) -> dict[str, Any]:
    """Systematics diagnostic: corr(residual, τ) and energy fraction in τ direction."""
    inv = inv or InvariantSet()
    model = PremergerPhaseModel.from_invariants(inv)
    out: dict[str, Any] = {"detectors": {}, "model_K": model.coupling_kernel()}
    for det in dets:
        mask = _inspiral_mask(det.t_rel, t_end)
        phi = orbital_phase_from_strain(
            det.pe_template_w, det.sample_rate, t_rel=det.t_rel, t_ref=0.0
        )
        tau = phase_basis_template(det.pe_template_w, phi, model)[mask]
        r = det.residual_w[mask]
        if np.std(r) < 1e-30 or np.std(tau) < 1e-30:
            corr = 0.0
        else:
            corr = float(np.corrcoef(r, tau)[0, 1])
        # fraction of residual power along τ
        den = float(np.sum(tau * tau)) + 1e-60
        a = float(np.sum(r * tau) / den)
        frac = float(np.sum((a * tau) ** 2) / (np.sum(r**2) + 1e-60))
        out["detectors"][det.detector] = {
            "corr_r_tau": corr,
            "power_frac_along_tau": frac,
            "alpha_proj": a,
        }
    return out


def premerger_injection_recovery(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    *,
    alpha_injs: list[float] | None = None,
    t_end: float = GATE_P_T_END,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    inv: InvariantSet | None = None,
    into: str = "residual",
    seed: int = 42,
) -> dict[str, Any]:
    """Inject known α into whitened residuals; recover α_hat and Gate P.

    into='residual': PE residual + α·τ (realistic background)
    into='noise': unit Gaussian + α·τ (ideal recovery)
    """
    inv = inv or InvariantSet()
    taus, model = network_tau_templates(dets, inv, t_end=t_end)
    if alpha_injs is None:
        alpha_injs = [0.0, 2e-5, 5e-5, 7e-5, 1e-4, 2e-4, 5e-4]

    rng = np.random.default_rng(seed)
    rows = []
    thr = None
    for a_inj in alpha_injs:
        clones = []
        for det, tau in zip(dets, taus):
            if into == "noise":
                base = rng.standard_normal(det.residual_w.shape)
            elif into == "residual":
                base = det.residual_w.copy()
            else:
                raise ValueError(into)
            # coherent injection: same α on both detectors
            clones.append(_clone_with_residual(det, base + float(a_inj) * tau))

        fit = fit_premerger_phase_network(
            clones,
            event,
            t_end=t_end,
            f_low=f_low,
            f_high=f_high,
            gate_dchi2=gate_dchi2,
            inv=inv,
        )
        bias = fit.alpha_hat - float(a_inj)
        frac = (
            fit.alpha_hat / float(a_inj)
            if abs(a_inj) > 1e-15
            else float("nan")
        )
        row = {
            "alpha_inj": float(a_inj),
            "alpha_hat": fit.alpha_hat,
            "alpha_sigma": fit.alpha_sigma,
            "delta_chi2": fit.delta_chi2,
            "gate_p_pass": fit.gate_p_pass,
            "bias": bias,
            "recovered_frac": frac,
            "sign_ok": fit.gate_p_pass or abs(a_inj) < 1e-15,
        }
        rows.append(row)
        if thr is None and a_inj > 0 and fit.gate_p_pass:
            thr = float(a_inj)

    bg = rows[0] if rows and abs(rows[0]["alpha_inj"]) < 1e-15 else None
    return {
        "schema": "invariant_hunt.premerger_injection.v1",
        "into": into,
        "event": event.name,
        "detectors": [d.detector for d in dets],
        "model_K": model.coupling_kernel(),
        "gate_dchi2": gate_dchi2,
        "detection_threshold_alpha": thr,
        "background": bg,
        "rows": rows,
        "note": (
            "Coherent α·τ injection on both detectors. Gate P includes H1/L1 "
            "sign consistency. Background α_inj=0 measures false-positive rate."
        ),
    }


def time_cut_robustness(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    *,
    t_ends: list[float] | None = None,
    f_low: float = 20.0,
    f_high: float = 100.0,
    gate_dchi2: float = GATE_P_DELTA_CHI2,
    inv: InvariantSet | None = None,
) -> dict[str, Any]:
    """Systematics: Gate P vs inspiral end-time cut."""
    if t_ends is None:
        t_ends = [-0.20, -0.10, -0.05, -0.02]
    rows = []
    for te in t_ends:
        fit = fit_premerger_phase_network(
            dets,
            event,
            t_end=te,
            f_low=f_low,
            f_high=f_high,
            gate_dchi2=gate_dchi2,
            inv=inv,
        )
        rows.append(
            {
                "t_end": te,
                "alpha_hat": fit.alpha_hat,
                "alpha_sigma": fit.alpha_sigma,
                "delta_chi2": fit.delta_chi2,
                "gate_p_pass": fit.gate_p_pass,
            }
        )
    return {"t_ends": rows}
