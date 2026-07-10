"""
Pre-merger mapping v2 — pre-registered mass-scaled coupling (not yet the default fit path).

Form (docs/PREREG_PREMERGER_MAPPING_V2.md):

  β = α_0 * (M_tot / M_ref)^p
  τ_v2 = τ_0 * (M_tot / M_ref)^p
  residual model: r ≈ α_0 · τ_v2

Locks W_g, κ, φ_b fixed. Default campaign: p=1, M_ref=60 M_⊙.
Does not auto-run held-outs; scoring only via explicit scripts after approval.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .invariants import DEFAULT_BRAIDING, LOCKED_WG, InvariantSet
from .premerger_theory import PremergerPhaseModel, phase_basis_template

# Pre-registered defaults (PREREG_PREMERGER_MAPPING_V2.md)
M_REF_SOLAR: float = 60.0
MASS_POWER_DEFAULT: float = 1.0  # p=1 fixed for primary campaign
ALPHA0_PRIOR_SIGMA: float = 1.0e-3


@dataclass(frozen=True)
class PremergerPhaseModelV2:
    """v2 model: locks + mass-power scaling; free α_0 only at fit time."""

    wg: float = LOCKED_WG
    kappa: float = 0.85
    phi_b: float = DEFAULT_BRAIDING
    mass_power: float = MASS_POWER_DEFAULT
    m_ref_solar: float = M_REF_SOLAR
    m_tot_solar: float = M_REF_SOLAR  # set per event
    alpha_0: float = 0.0

    @classmethod
    def from_invariants(
        cls,
        inv: InvariantSet | None = None,
        *,
        m_tot_solar: float,
        mass_power: float = MASS_POWER_DEFAULT,
        m_ref_solar: float = M_REF_SOLAR,
        alpha_0: float = 0.0,
    ) -> "PremergerPhaseModelV2":
        inv = inv or InvariantSet()
        return cls(
            wg=inv.wg,
            kappa=inv.kappa,
            phi_b=inv.braiding_target,
            mass_power=float(mass_power),
            m_ref_solar=float(m_ref_solar),
            m_tot_solar=float(m_tot_solar),
            alpha_0=float(alpha_0),
        )

    @property
    def scale_factor(self) -> float:
        """(M_tot / M_ref)^p"""
        return (self.m_tot_solar / self.m_ref_solar) ** self.mass_power

    def base_model(self) -> PremergerPhaseModel:
        return PremergerPhaseModel(
            wg=self.wg, kappa=self.kappa, phi_b=self.phi_b, alpha=self.alpha_0
        )

    def effective_beta(self) -> float:
        """β = α_0 * (M/M_ref)^p"""
        return self.alpha_0 * self.scale_factor

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "scale_factor": self.scale_factor,
            "effective_beta": self.effective_beta(),
            "formula": "β = α_0 (M_tot/M_ref)^p ; τ_v2 = τ_0 * (M_tot/M_ref)^p",
            "prereg": "docs/PREREG_PREMERGER_MAPPING_V2.md",
            "locks_frozen": True,
        }


def phase_basis_template_v2(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    model_v2: PremergerPhaseModelV2,
) -> np.ndarray:
    """τ_v2 = τ_0 * (M_tot/M_ref)^p  so r ≈ α_0 · τ_v2."""
    tau0 = phase_basis_template(h_gr, phi_orb, model_v2.base_model())
    return tau0 * model_v2.scale_factor


def predict_beta_ratio_gw170809_vs_150914(
    m_tot_809: float = 35.0 + 23.8,
    m_tot_914: float = 35.6 + 30.6,
    p: float = MASS_POWER_DEFAULT,
) -> dict[str, float]:
    """Sanity: with p=1, β_809/β_914 = M_809/M_914 if α_0 shared.

    Empirical v1 α_809/α_914 ~ 8.6e-4 / 6.9e-5 ~ 12.4 — mass ratio alone
    (~0.89) does **not** explain the gap; p-scaling alone may fail SUCCESS.
    Documented for honesty before execution.
    """
    r_mass = (m_tot_809 / m_tot_914) ** p
    return {
        "m_tot_809": m_tot_809,
        "m_tot_914": m_tot_914,
        "p": p,
        "beta_ratio_if_shared_alpha0": float(r_mass),
        "empirical_alpha_ratio_v1": float(8.58e-4 / 6.928e-5),
        "note": (
            "Mass-only p=1 predicts β ratio ~ O(1), not ~12; "
            "v2 may FALSIFY mass-only scaling — pre-registered outcome is OK."
        ),
    }


# ---------------------------------------------------------------------------
# Network fit / Bayes for v2
# ---------------------------------------------------------------------------
@dataclass
class MappingV2FitResult:
    event: str
    mapping: str
    mass_power: float
    m_tot_solar: float
    m_ref_solar: float
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
    gate_p_v2_pass: bool
    gate_p_v1_pass: bool | None
    alpha_v1_hat: float | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stack_network_residual_basis_v2(
    dets: list,
    model_v2: PremergerPhaseModelV2,
    *,
    t_end: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Stack r and τ_v2 across detectors."""
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
        tau = phase_basis_template_v2(h_gr, phi_orb, model_v2)
        r_list.append(det.residual_w[mask])
        tau_list.append(tau[mask])
    return np.concatenate(r_list), np.concatenate(tau_list)


def fit_premerger_v2_network(
    dets: list,
    event_name: str,
    *,
    m_tot_solar: float,
    mass_power: float = MASS_POWER_DEFAULT,
    m_ref_solar: float = M_REF_SOLAR,
    inv: InvariantSet | None = None,
    alpha_prior_sigma: float = ALPHA0_PRIOR_SIGMA,
    gate_dchi2: float = 6.0,
    compare_v1: bool = True,
) -> MappingV2FitResult:
    """Fit α_0 with τ_v2; compute Δχ², Gate P-v2, and ln B_10."""
    from .premerger_bayes import bayes_factor_from_vectors
    from .premerger_phase import fit_premerger_phase_network
    from .premerger_theory import GATE_P_DELTA_CHI2
    from .gw_events import get_event

    inv = inv or InvariantSet()
    model_v2 = PremergerPhaseModelV2.from_invariants(
        inv,
        m_tot_solar=m_tot_solar,
        mass_power=mass_power,
        m_ref_solar=m_ref_solar,
    )
    r, tau = stack_network_residual_basis_v2(dets, model_v2)
    tau2 = float(np.sum(tau * tau)) + 1e-60
    b = float(np.sum(tau * r))
    alpha_0 = b / tau2
    alpha_sig = float(1.0 / math.sqrt(tau2))
    chi_gr = float(np.sum(r * r))
    chi_topo = float(np.sum((r - alpha_0 * tau) ** 2))
    dchi = chi_gr - chi_topo

    # Per-detector sign check on α_0 (same scale factor both dets)
    det_alphas = []
    from .premerger_phase import _inspiral_mask
    from .premerger_theory import GATE_P_T_END, orbital_phase_from_strain

    for det in dets:
        mask = _inspiral_mask(det.t_rel, GATE_P_T_END)
        h_gr = det.pe_template_w
        phi = orbital_phase_from_strain(
            h_gr, det.sample_rate, t_rel=det.t_rel, t_ref=0.0
        )
        tau_d = phase_basis_template_v2(h_gr, phi, model_v2)[mask]
        r_d = det.residual_w[mask]
        den = float(np.sum(tau_d * tau_d)) + 1e-60
        a_d = float(np.sum(r_d * tau_d) / den)
        sig_d = float(1.0 / math.sqrt(den))
        det_alphas.append((det.detector, a_d, sig_d))

    signs = [np.sign(a) for _, a, s in det_alphas if abs(a) > 2.0 * s]
    sign_ok = len(signs) < 2 or (max(signs) * min(signs) > 0)
    gate = (
        dchi >= gate_dchi2
        and abs(alpha_0) > 2.0 * alpha_sig
        and sign_ok
    )

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
        f"v2: p={mass_power}, M_tot={m_tot_solar:.2f}, M_ref={m_ref_solar}, "
        f"scale={(m_tot_solar/m_ref_solar)**mass_power:.4f}",
        f"α_0={alpha_0:.3e}±{alpha_sig:.3e}  β_eff={alpha_0 * model_v2.scale_factor:.3e}",
        f"Δχ²={dchi:.2f}  lnB={bf.ln_B_10:.2f}  Gate P-v2={'PASS' if gate else 'fail'}",
    ]
    for name, a, s in det_alphas:
        notes.append(f"{name} α_0={a:.3e}±{s:.3e}")
    if not sign_ok:
        notes.append("H1/L1 α_0 signs disagree at >2σ")

    return MappingV2FitResult(
        event=event_name,
        mapping="v2_mass_power",
        mass_power=float(mass_power),
        m_tot_solar=float(m_tot_solar),
        m_ref_solar=float(m_ref_solar),
        scale_factor=float(model_v2.scale_factor),
        alpha_0_hat=float(alpha_0),
        alpha_0_sigma=float(alpha_sig),
        beta_eff=float(alpha_0 * model_v2.scale_factor),
        chi2_gr=chi_gr,
        chi2_topo=chi_topo,
        delta_chi2=float(dchi),
        ln_B_10=float(bf.ln_B_10),
        B_10=float(bf.B_10) if math.isfinite(bf.B_10) else float("inf"),
        kass_raftery=bf.kass_raftery,
        gate_p_v2_pass=bool(gate),
        gate_p_v1_pass=v1_pass,
        alpha_v1_hat=alpha_v1,
        notes=notes,
    )


def score_event_v2(
    event_name: str,
    *,
    project_root,
    mass_power: float = MASS_POWER_DEFAULT,
    approximant: str = "IMRPhenomD",
    detectors: list[str] | None = None,
) -> MappingV2FitResult:
    """Prepare network + PE median M_tot and fit v2."""
    from pathlib import Path

    from .pe_waveform import pe_params_for_event
    from .premerger_phase import prepare_premerger_network

    root = Path(project_root)
    detectors = detectors or ["H1", "L1"]
    params = pe_params_for_event(event_name, pe_dir=root / "data" / "pe")
    m_tot = float(params.mass1 + params.mass2)
    _event, dets = prepare_premerger_network(
        event_name,
        detectors,
        project_root=root,
        approximant=approximant,
        params=params,
    )
    return fit_premerger_v2_network(
        dets,
        event_name,
        m_tot_solar=m_tot,
        mass_power=mass_power,
    )


def evaluate_v2_campaign(
    results: dict[str, MappingV2FitResult],
    *,
    ln_b_thr: float = 5.0,
) -> dict[str, Any]:
    """Apply pre-registered SUCCESS/FALSIFY/NULL for primary GW170809.

    SUCCESS (strict PREREG):
      GW170809: P-v2 PASS + ln B_10 > 5
      AND mass scaling improves unification: |α_0(809)-α_0(914)| / σ combined
      smaller than |α_v1(809)-α_v1(914)| OR report honesty if mass scale fails
      to pull α_0 together.

    Pre-reg also said: p=1 fixed; mass-only may FALSIFY if α_0 not shared.
    We report:
      - gate on GW170809 alone (P-v2 + lnB)
      - alpha0 consistency: |α_0_809 - α_0_914| / hypot(σ809,σ914)
      - FALSIFY mass-unification if that z-score > 3 while both gate-pass
    """
    r809 = results.get("GW170809")
    r914 = results.get("GW150914")
    if r809 is None:
        return {"verdict": "INCONCLUSIVE", "reason": "GW170809 missing"}

    notes = []
    # Primary gates on GW170809
    p_pass = r809.gate_p_v2_pass
    b_pass = r809.ln_B_10 > ln_b_thr
    notes.append(f"GW170809 P-v2={'PASS' if p_pass else 'fail'} lnB={r809.ln_B_10:.2f}")

    mass_unify_ok = None
    z_alpha0 = None
    if r914 is not None:
        z_alpha0 = abs(r809.alpha_0_hat - r914.alpha_0_hat) / math.hypot(
            r809.alpha_0_sigma, r914.alpha_0_sigma
        )
        # Also compare empirical β ratio to mass prediction
        if abs(r914.beta_eff) > 1e-30:
            beta_ratio = r809.beta_eff / r914.beta_eff
        else:
            beta_ratio = float("nan")
        mass_pred = r809.scale_factor / r914.scale_factor
        notes.append(
            f"α_0(809)={r809.alpha_0_hat:.3e} α_0(914)={r914.alpha_0_hat:.3e} "
            f"z={z_alpha0:.2f}"
        )
        notes.append(
            f"β_eff ratio={beta_ratio:.3f} vs mass scale ratio={mass_pred:.3f}"
        )
        # Shared α_0 would require z ≲ 3
        mass_unify_ok = z_alpha0 <= 3.0

    # Pre-registered SUCCESS: GW170809 P-v2 + lnB>5 AND mass unification of α_0
    # (shared α_0 across 914 and 809). If P-v2+lnB pass but α_0 inconsistent,
    # FALSIFY mass-only scaling (allowed pre-reg outcome).
    if not p_pass:
        verdict = "NULL"
        reason = "GW170809 Gate P-v2 fail"
    elif not b_pass:
        verdict = "FALSIFY"
        reason = f"GW170809 ln B_10={r809.ln_B_10:.2f} ≤ {ln_b_thr} (BF gate)"
    elif mass_unify_ok is False:
        verdict = "FALSIFY"
        reason = (
            f"GW170809 residual-strong but α_0 not shared with core "
            f"(z={z_alpha0:.2f}>3) — mass-only p=1 scaling fails unification"
        )
    elif mass_unify_ok is True and p_pass and b_pass:
        verdict = "SUCCESS"
        reason = "GW170809 P-v2+BF pass and α_0 consistent with GW150914 under p=1"
    else:
        verdict = "INCONCLUSIVE"
        reason = "Missing core comparison or incomplete gates"

    return {
        "verdict": verdict,
        "reason": reason,
        "notes": notes,
        "ln_b_thr": ln_b_thr,
        "z_alpha0_809_vs_914": z_alpha0,
        "mass_unify_ok": mass_unify_ok,
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V2.md",
        "mass_power": MASS_POWER_DEFAULT,
    }
