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
) -> tuple[PublicGWEvent, list[DetectorWhitened]]:
    """Long pre-merger window for inspiral phase analysis."""
    event = get_event(event_name)
    pe_dir = project_root / "data" / "pe"
    cache = project_root / "data" / "gwosc"
    params = pe_params_for_event(event.name, pe_dir=pe_dir)
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
        )
        for det in detectors
    ]
    return event, dets
