"""
Pre-merger mapping v5 — Hopf-lattice geometric scale Λ
(docs/PREREG_PREMERGER_MAPPING_V5.md).

  Θ_link = 2π W_g / (2 W_g + 1)
  Λ = (Θ_link / π) · (M_f,ref / M_f)
  β = α_0 · Λ
  τ_v5 = τ_0 · Λ
  r ≈ α_0 · τ_v5

Locks frozen. Closed v1–v4 families not reopened. GW151012 systematics only.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .gw_events import get_event
from .invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    InvariantSet,
    burst_threshold,
    link_saturation_theta,
)
from .premerger_mapping_v4 import M_F_REF, REMNANT_MASS_CATALOG, remnant_mass_solar
from .premerger_theory import PremergerPhaseModel, phase_basis_template

ALPHA0_PRIOR_SIGMA: float = 1.0e-3
EMPIRICAL_ALPHA_RATIO_V1: float = 8.58e-4 / 6.928e-5  # ~12.4


def theta_link_locked(wg: float = LOCKED_WG) -> float:
    """Θ_link = 2π W_g / (2 W_g + 1)."""
    return float(link_saturation_theta(wg))


def lambda_hopf(
    m_f_solar: float,
    *,
    m_f_ref_solar: float = M_F_REF,
    wg: float = LOCKED_WG,
    control: bool = False,
) -> float:
    """Primary Λ = (Θ_link/π)·(M_f,ref/M_f); control = Θ_link/π only."""
    lam0 = theta_link_locked(wg) / math.pi
    if control:
        return float(lam0)
    return float(lam0 * (m_f_ref_solar / m_f_solar))


def lambda_sensitivity(
    m_f_solar: float,
    *,
    m_f_ref_solar: float = M_F_REF,
    wg: float = LOCKED_WG,
    kappa: float = DEFAULT_KAPPA,
) -> float:
    """Sensitivity: (Θ_link/θ_crit)·(M_f,ref/M_f) — not SUCCESS path."""
    th_l = theta_link_locked(wg)
    th_c = burst_threshold(kappa)
    return float((th_l / th_c) * (m_f_ref_solar / m_f_solar))


@dataclass(frozen=True)
class PremergerPhaseModelV5:
    """v5 model: locks + Hopf geometric Λ; free α_0 at fit time."""

    wg: float = LOCKED_WG
    kappa: float = DEFAULT_KAPPA
    phi_b: float = DEFAULT_BRAIDING
    m_f_ref_solar: float = M_F_REF
    m_f_solar: float = M_F_REF
    control: bool = False  # if True, event-independent Λ_ctrl
    alpha_0: float = 0.0

    @classmethod
    def from_invariants(
        cls,
        inv: InvariantSet | None = None,
        *,
        m_f_solar: float,
        m_f_ref_solar: float = M_F_REF,
        control: bool = False,
        alpha_0: float = 0.0,
    ) -> "PremergerPhaseModelV5":
        inv = inv or InvariantSet()
        return cls(
            wg=inv.wg,
            kappa=inv.kappa,
            phi_b=inv.braiding_target,
            m_f_ref_solar=float(m_f_ref_solar),
            m_f_solar=float(m_f_solar),
            control=bool(control),
            alpha_0=float(alpha_0),
        )

    @property
    def theta_link(self) -> float:
        return theta_link_locked(self.wg)

    @property
    def lambda_0(self) -> float:
        """Θ_link / π (event-independent weight)."""
        return self.theta_link / math.pi

    @property
    def scale_factor(self) -> float:
        """Λ primary or control."""
        return lambda_hopf(
            self.m_f_solar,
            m_f_ref_solar=self.m_f_ref_solar,
            wg=self.wg,
            control=self.control,
        )

    def base_model(self) -> PremergerPhaseModel:
        return PremergerPhaseModel(
            wg=self.wg, kappa=self.kappa, phi_b=self.phi_b, alpha=self.alpha_0
        )

    def effective_beta(self) -> float:
        return self.alpha_0 * self.scale_factor

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "theta_link": self.theta_link,
            "lambda_0": self.lambda_0,
            "scale_factor": self.scale_factor,
            "effective_beta": self.effective_beta(),
            "formula": (
                "Λ = (Θ_link/π)·(M_f,ref/M_f); Θ_link=2π W_g/(2 W_g+1); "
                "τ_v5 = τ_0 · Λ"
            ),
            "prereg": "docs/PREREG_PREMERGER_MAPPING_V5.md",
            "locks_frozen": True,
        }


def phase_basis_template_v5(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    model_v5: PremergerPhaseModelV5,
) -> np.ndarray:
    """τ_v5 = τ_0 · Λ."""
    tau0 = phase_basis_template(h_gr, phi_orb, model_v5.base_model())
    return tau0 * model_v5.scale_factor


def predict_honesty_v5(
    *,
    m_f_809: float = REMNANT_MASS_CATALOG["GW170809"],
    m_f_914: float = REMNANT_MASS_CATALOG["GW150914"],
    wg: float = LOCKED_WG,
) -> dict[str, Any]:
    """Pre-run honesty: Λ ratio vs empirical ~12.4."""
    lam_809 = lambda_hopf(m_f_809, m_f_ref_solar=m_f_914, wg=wg)
    lam_914 = lambda_hopf(m_f_914, m_f_ref_solar=m_f_914, wg=wg)
    ratio = lam_809 / lam_914
    lam0 = theta_link_locked(wg) / math.pi
    return {
        "m_f_809": m_f_809,
        "m_f_914": m_f_914,
        "m_f_ref": m_f_914,
        "theta_link": theta_link_locked(wg),
        "lambda_0": float(lam0),
        "lambda_809": float(lam_809),
        "lambda_914": float(lam_914),
        "beta_ratio_if_shared_alpha0": float(ratio),
        "control_ratio": 1.0,
        "empirical_alpha_ratio_v1": float(EMPIRICAL_ALPHA_RATIO_V1),
        "note": (
            f"Hopf Λ primary predicts β ratio ~{ratio:.3f} (far short of ~12); "
            "unification FALSIFY is the expected pre-registered outcome."
        ),
    }


@dataclass
class MappingV5FitResult:
    event: str
    mapping: str
    m_f_solar: float
    m_f_ref_solar: float
    theta_link: float
    lambda_0: float
    scale_factor: float
    alpha_0_hat: float
    alpha_0_sigma: float
    beta_eff: float
    chi2_gr: float
    chi2_topo: float
    delta_chi2: float
    ln_B_10: float
    B_10: float
    kass_raftery: str
    gate_p_v5_pass: bool
    gate_p_v1_pass: bool | None
    alpha_v1_hat: float | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stack_network_residual_basis_v5(
    dets: list,
    model_v5: PremergerPhaseModelV5,
    *,
    t_end: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    from .premerger_phase import _inspiral_mask
    from .premerger_theory import GATE_P_T_END, orbital_phase_from_strain

    t_end = GATE_P_T_END if t_end is None else t_end
    r_list: list[np.ndarray] = []
    tau_list: list[np.ndarray] = []
    for det in dets:
        mask = _inspiral_mask(det.t_rel, t_end)
        h_gr = det.pe_template_w
        phi_orb = orbital_phase_from_strain(
            h_gr, det.sample_rate, t_rel=det.t_rel, t_ref=0.0
        )
        tau = phase_basis_template_v5(h_gr, phi_orb, model_v5)
        r_list.append(det.residual_w[mask])
        tau_list.append(tau[mask])
    return np.concatenate(r_list), np.concatenate(tau_list)


def fit_premerger_v5_network(
    dets: list,
    event_name: str,
    *,
    m_f_solar: float,
    m_f_ref_solar: float = M_F_REF,
    control: bool = False,
    inv: InvariantSet | None = None,
    alpha_prior_sigma: float = ALPHA0_PRIOR_SIGMA,
    gate_dchi2: float = 6.0,
    compare_v1: bool = True,
) -> MappingV5FitResult:
    """Fit α_0 with τ_v5; Δχ², Gate P-v5, ln B_10."""
    from .premerger_bayes import bayes_factor_from_vectors
    from .premerger_phase import _inspiral_mask, fit_premerger_phase_network
    from .premerger_theory import GATE_P_T_END, orbital_phase_from_strain

    inv = inv or InvariantSet()
    model_v5 = PremergerPhaseModelV5.from_invariants(
        inv,
        m_f_solar=m_f_solar,
        m_f_ref_solar=m_f_ref_solar,
        control=control,
    )
    r, tau = stack_network_residual_basis_v5(dets, model_v5)
    tau2 = float(np.sum(tau * tau)) + 1e-60
    b = float(np.sum(tau * r))
    alpha_0 = b / tau2
    alpha_sig = float(1.0 / math.sqrt(tau2))
    chi_gr = float(np.sum(r * r))
    chi_topo = float(np.sum((r - alpha_0 * tau) ** 2))
    dchi = chi_gr - chi_topo

    det_alphas = []
    for det in dets:
        mask = _inspiral_mask(det.t_rel, GATE_P_T_END)
        h_gr = det.pe_template_w
        phi = orbital_phase_from_strain(
            h_gr, det.sample_rate, t_rel=det.t_rel, t_ref=0.0
        )
        tau_d = phase_basis_template_v5(h_gr, phi, model_v5)[mask]
        r_d = det.residual_w[mask]
        den = float(np.sum(tau_d * tau_d)) + 1e-60
        a_d = float(np.sum(r_d * tau_d) / den)
        sig_d = float(1.0 / math.sqrt(den))
        det_alphas.append((det.detector, a_d, sig_d))

    signs = [np.sign(a) for _, a, s in det_alphas if abs(a) > 2.0 * s]
    sign_ok = len(signs) < 2 or (max(signs) * min(signs) > 0)
    gate = dchi >= gate_dchi2 and abs(alpha_0) > 2.0 * alpha_sig and sign_ok

    bf = bayes_factor_from_vectors(
        r,
        tau,
        alpha_prior_sigma=alpha_prior_sigma,
        event=event_name,
        detectors="+".join(d.detector for d in dets),
        gate_p_pass=gate,
    )

    v1_pass = None
    alpha_v1 = None
    if compare_v1:
        ev = get_event(event_name)
        fit_v1 = fit_premerger_phase_network(dets, ev, inv=inv)
        v1_pass = fit_v1.gate_p_pass
        alpha_v1 = fit_v1.alpha_hat

    notes = [
        f"v5: Λ={model_v5.scale_factor:.4f}  "
        f"(Θ_link/π={model_v5.lambda_0:.4f}, M_f={m_f_solar:.2f}, "
        f"M_f,ref={m_f_ref_solar}, control={control})",
        f"α_0={alpha_0:.3e}±{alpha_sig:.3e}  β_eff={alpha_0 * model_v5.scale_factor:.3e}",
        f"Δχ²={dchi:.2f}  lnB={bf.ln_B_10:.2f}  Gate P-v5={'PASS' if gate else 'fail'}",
    ]
    for name, a, s in det_alphas:
        notes.append(f"{name} α_0={a:.3e}±{s:.3e}")
    if not sign_ok:
        notes.append("H1/L1 α_0 signs disagree at >2σ")

    return MappingV5FitResult(
        event=event_name,
        mapping="v5_hopf_lambda_ctrl" if control else "v5_hopf_lambda",
        m_f_solar=float(m_f_solar),
        m_f_ref_solar=float(m_f_ref_solar),
        theta_link=float(model_v5.theta_link),
        lambda_0=float(model_v5.lambda_0),
        scale_factor=float(model_v5.scale_factor),
        alpha_0_hat=float(alpha_0),
        alpha_0_sigma=float(alpha_sig),
        beta_eff=float(alpha_0 * model_v5.scale_factor),
        chi2_gr=chi_gr,
        chi2_topo=chi_topo,
        delta_chi2=float(dchi),
        ln_B_10=float(bf.ln_B_10),
        B_10=float(bf.B_10) if math.isfinite(bf.B_10) else float("inf"),
        kass_raftery=bf.kass_raftery,
        gate_p_v5_pass=bool(gate),
        gate_p_v1_pass=v1_pass,
        alpha_v1_hat=alpha_v1,
        notes=notes,
    )


def score_event_v5(
    event_name: str,
    *,
    project_root,
    control: bool = False,
    approximant: str = "IMRPhenomD",
    detectors: list[str] | None = None,
) -> MappingV5FitResult:
    """Prepare network + catalog M_f; fit v5 with frozen Λ."""
    from pathlib import Path

    from .pe_waveform import pe_params_for_event
    from .premerger_phase import prepare_premerger_network

    root = Path(project_root)
    detectors = detectors or ["H1", "L1"]
    params = pe_params_for_event(event_name, pe_dir=root / "data" / "pe")
    m_f = remnant_mass_solar(event_name)
    _event, dets = prepare_premerger_network(
        event_name,
        detectors,
        project_root=root,
        approximant=approximant,
        params=params,
    )
    return fit_premerger_v5_network(
        dets,
        event_name,
        m_f_solar=m_f,
        m_f_ref_solar=M_F_REF,
        control=control,
    )


def evaluate_v5_campaign(
    results: dict[str, MappingV5FitResult],
    *,
    ln_b_thr: float = 5.0,
    z_unify_thr: float = 3.0,
) -> dict[str, Any]:
    """Pre-registered SUCCESS/FALSIFY/NULL for primary Hopf Λ."""
    r809 = results.get("GW170809")
    r914 = results.get("GW150914")
    if r809 is None:
        return {"verdict": "INCONCLUSIVE", "reason": "GW170809 missing"}

    notes: list[str] = []
    p_pass = r809.gate_p_v5_pass
    b_pass = r809.ln_B_10 > ln_b_thr
    notes.append(
        f"GW170809 P-v5={'PASS' if p_pass else 'fail'} lnB={r809.ln_B_10:.2f}"
    )

    unify_ok = None
    z_alpha0 = None
    beta_ratio = None
    scale_pred = None
    if r914 is not None:
        z_alpha0 = abs(r809.alpha_0_hat - r914.alpha_0_hat) / math.hypot(
            r809.alpha_0_sigma, r914.alpha_0_sigma
        )
        if abs(r914.beta_eff) > 1e-30:
            beta_ratio = r809.beta_eff / r914.beta_eff
        else:
            beta_ratio = float("nan")
        scale_pred = r809.scale_factor / r914.scale_factor
        notes.append(
            f"α_0(809)={r809.alpha_0_hat:.3e} α_0(914)={r914.alpha_0_hat:.3e} "
            f"z={z_alpha0:.2f}"
        )
        notes.append(
            f"β_eff ratio={beta_ratio:.3f} vs Λ scale ratio={scale_pred:.3f}"
        )
        unify_ok = z_alpha0 <= z_unify_thr

    if not p_pass:
        verdict = "NULL"
        reason = "GW170809 Gate P-v5 fail"
        family_closed = False
    elif not b_pass:
        verdict = "FALSIFY"
        reason = f"GW170809 ln B_10={r809.ln_B_10:.2f} ≤ {ln_b_thr}"
        family_closed = False
    elif unify_ok is False:
        verdict = "FALSIFY"
        reason = (
            f"GW170809 residual-strong but α_0 not shared with core "
            f"(z={z_alpha0:.2f}>3) — Hopf Λ fails unification; "
            "Hopf-lattice geometric scaling family closed under this pre-reg"
        )
        family_closed = True
    elif unify_ok is True and p_pass and b_pass:
        verdict = "SUCCESS"
        reason = (
            "GW170809 P-v5+BF pass and α_0 consistent with GW150914 under Hopf Λ"
        )
        family_closed = False
    else:
        verdict = "INCONCLUSIVE"
        reason = "Missing core comparison or incomplete gates"
        family_closed = False

    return {
        "verdict": verdict,
        "reason": reason,
        "notes": notes,
        "ln_b_thr": ln_b_thr,
        "z_alpha0_809_vs_914": z_alpha0,
        "unify_ok": unify_ok,
        "beta_eff_ratio": beta_ratio,
        "scale_ratio_pred": scale_pred,
        "hopf_lambda_family_closed": family_closed,
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V5.md",
        "formula": "Λ = (Θ_link/π)·(M_f,ref/M_f)",
    }
