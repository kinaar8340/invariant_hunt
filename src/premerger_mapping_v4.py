"""
Pre-merger mapping v4 — remnant mass scaling (docs/PREREG_PREMERGER_MAPPING_V4.md).

  β = α_0 · (M_f / M_f,ref)^p
  τ_v4 = τ_0 · (M_f / M_f,ref)^p
  r ≈ α_0 · τ_v4

Primary: p=1 fixed. Locks frozen. Closed bulk PE families (v2/v3) not reopened.
GW151012 systematics check only.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .gw_events import get_event
from .invariants import DEFAULT_BRAIDING, LOCKED_WG, InvariantSet
from .premerger_theory import PremergerPhaseModel, phase_basis_template

ALPHA0_PRIOR_SIGMA: float = 1.0e-3
MASS_POWER_DEFAULT: float = 1.0  # p=1 fixed
EMPIRICAL_ALPHA_RATIO_V1: float = 8.58e-4 / 6.928e-5  # ~12.4

# Frozen catalog remnant masses (PublicGWEvent.mass_final_solar) — PREREG table
REMNANT_MASS_CATALOG: dict[str, float] = {
    "GW150914": 63.1,
    "GW170814": 53.2,
    "GW170809": 56.3,
    "GW151012": 35.7,
    "GW170729": 79.5,
    "GW151226": 20.5,
    "GW170104": 48.9,
    "GW170608": 17.8,
    "GW170818": 59.4,
    "GW170823": 65.4,
}
M_F_REF: float = REMNANT_MASS_CATALOG["GW150914"]


def remnant_mass_solar(event_name: str) -> float:
    """Frozen catalog M_f; falls back to PublicGWEvent if not in table."""
    if event_name in REMNANT_MASS_CATALOG:
        return float(REMNANT_MASS_CATALOG[event_name])
    return float(get_event(event_name).mass_final_solar)


@dataclass(frozen=True)
class PremergerPhaseModelV4:
    """v4 model: locks + remnant-mass power; free α_0 at fit time."""

    wg: float = LOCKED_WG
    kappa: float = 0.85
    phi_b: float = DEFAULT_BRAIDING
    mass_power: float = MASS_POWER_DEFAULT
    m_f_ref_solar: float = M_F_REF
    m_f_solar: float = M_F_REF
    alpha_0: float = 0.0

    @classmethod
    def from_invariants(
        cls,
        inv: InvariantSet | None = None,
        *,
        m_f_solar: float,
        mass_power: float = MASS_POWER_DEFAULT,
        m_f_ref_solar: float = M_F_REF,
        alpha_0: float = 0.0,
    ) -> "PremergerPhaseModelV4":
        inv = inv or InvariantSet()
        return cls(
            wg=inv.wg,
            kappa=inv.kappa,
            phi_b=inv.braiding_target,
            mass_power=float(mass_power),
            m_f_ref_solar=float(m_f_ref_solar),
            m_f_solar=float(m_f_solar),
            alpha_0=float(alpha_0),
        )

    @property
    def scale_factor(self) -> float:
        """(M_f / M_f,ref)^p"""
        return (self.m_f_solar / self.m_f_ref_solar) ** self.mass_power

    def base_model(self) -> PremergerPhaseModel:
        return PremergerPhaseModel(
            wg=self.wg, kappa=self.kappa, phi_b=self.phi_b, alpha=self.alpha_0
        )

    def effective_beta(self) -> float:
        return self.alpha_0 * self.scale_factor

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "scale_factor": self.scale_factor,
            "effective_beta": self.effective_beta(),
            "formula": "β = α_0 (M_f/M_f,ref)^p ; τ_v4 = τ_0 · (M_f/M_f,ref)^p",
            "prereg": "docs/PREREG_PREMERGER_MAPPING_V4.md",
            "locks_frozen": True,
        }


def phase_basis_template_v4(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    model_v4: PremergerPhaseModelV4,
) -> np.ndarray:
    """τ_v4 = τ_0 · S."""
    tau0 = phase_basis_template(h_gr, phi_orb, model_v4.base_model())
    return tau0 * model_v4.scale_factor


def predict_honesty_v4(
    *,
    m_f_809: float = REMNANT_MASS_CATALOG["GW170809"],
    m_f_914: float = REMNANT_MASS_CATALOG["GW150914"],
    p: float = MASS_POWER_DEFAULT,
) -> dict[str, Any]:
    """Pre-run honesty: remnant ratio vs empirical ~12.4 (often wrong way)."""
    r1 = (m_f_809 / m_f_914) ** 1.0
    r2 = (m_f_809 / m_f_914) ** 2.0
    rp = (m_f_809 / m_f_914) ** p
    return {
        "m_f_809": m_f_809,
        "m_f_914": m_f_914,
        "m_f_ref": m_f_914,
        "p": p,
        "beta_ratio_p1": float(r1),
        "beta_ratio_p2": float(r2),
        "beta_ratio_if_shared_alpha0": float(rp),
        "empirical_alpha_ratio_v1": float(EMPIRICAL_ALPHA_RATIO_V1),
        "note": (
            f"Remnant p=1 predicts β ratio ~{r1:.3f} (wrong way vs ~12); "
            "unification FALSIFY is the expected pre-registered outcome."
        ),
    }


@dataclass
class MappingV4FitResult:
    event: str
    mapping: str
    mass_power: float
    m_f_solar: float
    m_f_ref_solar: float
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
    gate_p_v4_pass: bool
    gate_p_v1_pass: bool | None
    alpha_v1_hat: float | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stack_network_residual_basis_v4(
    dets: list,
    model_v4: PremergerPhaseModelV4,
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
        tau = phase_basis_template_v4(h_gr, phi_orb, model_v4)
        r_list.append(det.residual_w[mask])
        tau_list.append(tau[mask])
    return np.concatenate(r_list), np.concatenate(tau_list)


def fit_premerger_v4_network(
    dets: list,
    event_name: str,
    *,
    m_f_solar: float,
    mass_power: float = MASS_POWER_DEFAULT,
    m_f_ref_solar: float = M_F_REF,
    inv: InvariantSet | None = None,
    alpha_prior_sigma: float = ALPHA0_PRIOR_SIGMA,
    gate_dchi2: float = 6.0,
    compare_v1: bool = True,
) -> MappingV4FitResult:
    """Fit α_0 with τ_v4; Δχ², Gate P-v4, ln B_10."""
    from .premerger_bayes import bayes_factor_from_vectors
    from .premerger_phase import _inspiral_mask, fit_premerger_phase_network
    from .premerger_theory import GATE_P_T_END, orbital_phase_from_strain

    inv = inv or InvariantSet()
    model_v4 = PremergerPhaseModelV4.from_invariants(
        inv,
        m_f_solar=m_f_solar,
        mass_power=mass_power,
        m_f_ref_solar=m_f_ref_solar,
    )
    r, tau = stack_network_residual_basis_v4(dets, model_v4)
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
        tau_d = phase_basis_template_v4(h_gr, phi, model_v4)[mask]
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
        f"v4: p={mass_power}, M_f={m_f_solar:.2f}, M_f,ref={m_f_ref_solar}, "
        f"S={model_v4.scale_factor:.4f}",
        f"α_0={alpha_0:.3e}±{alpha_sig:.3e}  β_eff={alpha_0 * model_v4.scale_factor:.3e}",
        f"Δχ²={dchi:.2f}  lnB={bf.ln_B_10:.2f}  Gate P-v4={'PASS' if gate else 'fail'}",
    ]
    for name, a, s in det_alphas:
        notes.append(f"{name} α_0={a:.3e}±{s:.3e}")
    if not sign_ok:
        notes.append("H1/L1 α_0 signs disagree at >2σ")

    return MappingV4FitResult(
        event=event_name,
        mapping="v4_remnant_mass",
        mass_power=float(mass_power),
        m_f_solar=float(m_f_solar),
        m_f_ref_solar=float(m_f_ref_solar),
        scale_factor=float(model_v4.scale_factor),
        alpha_0_hat=float(alpha_0),
        alpha_0_sigma=float(alpha_sig),
        beta_eff=float(alpha_0 * model_v4.scale_factor),
        chi2_gr=chi_gr,
        chi2_topo=chi_topo,
        delta_chi2=float(dchi),
        ln_B_10=float(bf.ln_B_10),
        B_10=float(bf.B_10) if math.isfinite(bf.B_10) else float("inf"),
        kass_raftery=bf.kass_raftery,
        gate_p_v4_pass=bool(gate),
        gate_p_v1_pass=v1_pass,
        alpha_v1_hat=alpha_v1,
        notes=notes,
    )


def score_event_v4(
    event_name: str,
    *,
    project_root,
    mass_power: float = MASS_POWER_DEFAULT,
    approximant: str = "IMRPhenomD",
    detectors: list[str] | None = None,
) -> MappingV4FitResult:
    """Prepare network + catalog M_f; fit v4."""
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
    return fit_premerger_v4_network(
        dets,
        event_name,
        m_f_solar=m_f,
        mass_power=mass_power,
        m_f_ref_solar=M_F_REF,
    )


def evaluate_v4_campaign(
    results: dict[str, MappingV4FitResult],
    *,
    ln_b_thr: float = 5.0,
    z_unify_thr: float = 3.0,
) -> dict[str, Any]:
    """Pre-registered SUCCESS/FALSIFY/NULL for remnant-mass p=1 primary."""
    r809 = results.get("GW170809")
    r914 = results.get("GW150914")
    if r809 is None:
        return {"verdict": "INCONCLUSIVE", "reason": "GW170809 missing"}

    notes: list[str] = []
    p_pass = r809.gate_p_v4_pass
    b_pass = r809.ln_B_10 > ln_b_thr
    notes.append(
        f"GW170809 P-v4={'PASS' if p_pass else 'fail'} lnB={r809.ln_B_10:.2f}"
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
            f"β_eff ratio={beta_ratio:.3f} vs remnant scale ratio={scale_pred:.3f}"
        )
        unify_ok = z_alpha0 <= z_unify_thr

    if not p_pass:
        verdict = "NULL"
        reason = "GW170809 Gate P-v4 fail"
        family_closed = False
    elif not b_pass:
        verdict = "FALSIFY"
        reason = f"GW170809 ln B_10={r809.ln_B_10:.2f} ≤ {ln_b_thr}"
        family_closed = False
    elif unify_ok is False:
        verdict = "FALSIFY"
        reason = (
            f"GW170809 residual-strong but α_0 not shared with core "
            f"(z={z_alpha0:.2f}>3) — remnant-mass p=1 fails unification; "
            "remnant-mass scaling family closed under this pre-reg"
        )
        family_closed = True
    elif unify_ok is True and p_pass and b_pass:
        verdict = "SUCCESS"
        reason = (
            "GW170809 P-v4+BF pass and α_0 consistent with GW150914 under M_f p=1"
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
        "mass_power": MASS_POWER_DEFAULT,
        "remnant_mass_family_closed": family_closed,
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V4.md",
    }
