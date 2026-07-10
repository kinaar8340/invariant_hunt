"""
Pre-merger mapping v3 — pre-registered non-mass scale (docs/PREREG_PREMERGER_MAPPING_V3.md).

  β = α_0 · S
  τ_v3 = τ_0 · S
  r ≈ α_0 · τ_v3

Primary P-v3a:  S = (ρ_ref / ρ_net)^q   with q=1 fixed (inverse SNR)
Secondary P-v3b: S = (d_L / d_ref)^s    with s=1 fixed (distance), only if P-v3a fails

Locks W_g, κ, φ_b frozen. Mass scaling closed by v2 FALSIFY.
GW151012 is systematics check only — not a design anchor.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np

from .invariants import DEFAULT_BRAIDING, LOCKED_WG, InvariantSet
from .premerger_theory import PremergerPhaseModel, phase_basis_template

# Pre-registered defaults
ALPHA0_PRIOR_SIGMA: float = 1.0e-3
RHO_REF: float = 24.4  # GW150914 GWTC-1 network SNR
INV_SNR_POWER_DEFAULT: float = 1.0  # q=1
DISTANCE_POWER_DEFAULT: float = 1.0  # s=1
EMPIRICAL_ALPHA_RATIO_V1: float = 8.58e-4 / 6.928e-5  # ~12.4

ScaleMode = Literal["inv_snr", "distance"]

# Frozen GWTC-1 network matched-filter SNR table (PREREG)
NETWORK_SNR_GWTC1: dict[str, float] = {
    "GW150914": 24.4,
    "GW170814": 17.2,
    "GW170809": 12.4,
    "GW151012": 10.0,
    "GW170729": 10.8,
    "GW151226": 13.1,
    "GW170104": 13.0,
    "GW170608": 14.9,
    "GW170818": 11.3,
    "GW170823": 11.5,
}


@dataclass(frozen=True)
class PremergerPhaseModelV3:
    """v3 model: locks + bulk scale S; free α_0 only at fit time."""

    wg: float = LOCKED_WG
    kappa: float = 0.85
    phi_b: float = DEFAULT_BRAIDING
    scale_mode: ScaleMode = "inv_snr"
    scale_power: float = INV_SNR_POWER_DEFAULT
    scale_value: float = RHO_REF  # ρ_net or d_L for this event
    scale_ref: float = RHO_REF  # ρ_ref or d_ref
    alpha_0: float = 0.0

    @classmethod
    def from_invariants(
        cls,
        inv: InvariantSet | None = None,
        *,
        scale_mode: ScaleMode,
        scale_value: float,
        scale_ref: float,
        scale_power: float,
        alpha_0: float = 0.0,
    ) -> "PremergerPhaseModelV3":
        inv = inv or InvariantSet()
        return cls(
            wg=inv.wg,
            kappa=inv.kappa,
            phi_b=inv.braiding_target,
            scale_mode=scale_mode,
            scale_power=float(scale_power),
            scale_value=float(scale_value),
            scale_ref=float(scale_ref),
            alpha_0=float(alpha_0),
        )

    @property
    def scale_factor(self) -> float:
        """S for inv_snr: (ρ_ref/ρ)^q ; for distance: (d/d_ref)^s."""
        if self.scale_mode == "inv_snr":
            return (self.scale_ref / self.scale_value) ** self.scale_power
        if self.scale_mode == "distance":
            return (self.scale_value / self.scale_ref) ** self.scale_power
        raise ValueError(f"Unknown scale_mode {self.scale_mode}")

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
            "formula": (
                "β = α_0 S; τ_v3 = τ_0 S; "
                "inv_snr: S=(ρ_ref/ρ)^q; distance: S=(d/d_ref)^s"
            ),
            "prereg": "docs/PREREG_PREMERGER_MAPPING_V3.md",
            "locks_frozen": True,
        }


def phase_basis_template_v3(
    h_gr: np.ndarray,
    phi_orb: np.ndarray,
    model_v3: PremergerPhaseModelV3,
) -> np.ndarray:
    """τ_v3 = τ_0 · S  so r ≈ α_0 · τ_v3."""
    tau0 = phase_basis_template(h_gr, phi_orb, model_v3.base_model())
    return tau0 * model_v3.scale_factor


def predict_honesty_v3(
    *,
    rho_809: float = NETWORK_SNR_GWTC1["GW170809"],
    rho_914: float = NETWORK_SNR_GWTC1["GW150914"],
    d_809: float = 1028.2,
    d_914: float = 439.3,
) -> dict[str, Any]:
    """Pre-run honesty: predicted β ratios if shared α_0 vs empirical ~12.4."""
    inv_q1 = (rho_914 / rho_809) ** 1.0
    inv_q2 = (rho_914 / rho_809) ** 2.0
    d_s1 = (d_809 / d_914) ** 1.0
    d_s2 = (d_809 / d_914) ** 2.0
    d_s3 = (d_809 / d_914) ** 3.0  # not registered — curiosity only
    return {
        "empirical_alpha_ratio_v1": float(EMPIRICAL_ALPHA_RATIO_V1),
        "inv_snr_q1_ratio": float(inv_q1),
        "inv_snr_q2_ratio": float(inv_q2),
        "distance_s1_ratio": float(d_s1),
        "distance_s2_ratio": float(d_s2),
        "distance_s3_ratio_not_registered": float(d_s3),
        "rho_809": rho_809,
        "rho_914": rho_914,
        "d_809": d_809,
        "d_914": d_914,
        "note": (
            "Mild inv-SNR q=1 (~2) and d^1 (~2.3) fall far short of ~12; "
            "unification FALSIFY is an allowed pre-registered outcome. "
            "d^3 is NOT registered (post-hoc numerical match)."
        ),
    }


@dataclass
class MappingV3FitResult:
    event: str
    mapping: str
    scale_mode: str
    scale_power: float
    scale_value: float
    scale_ref: float
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
    gate_p_v3_pass: bool
    gate_p_v1_pass: bool | None
    alpha_v1_hat: float | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stack_network_residual_basis_v3(
    dets: list,
    model_v3: PremergerPhaseModelV3,
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
        tau = phase_basis_template_v3(h_gr, phi_orb, model_v3)
        r_list.append(det.residual_w[mask])
        tau_list.append(tau[mask])
    return np.concatenate(r_list), np.concatenate(tau_list)


def fit_premerger_v3_network(
    dets: list,
    event_name: str,
    *,
    scale_mode: ScaleMode,
    scale_value: float,
    scale_ref: float,
    scale_power: float,
    inv: InvariantSet | None = None,
    alpha_prior_sigma: float = ALPHA0_PRIOR_SIGMA,
    gate_dchi2: float = 6.0,
    compare_v1: bool = True,
) -> MappingV3FitResult:
    """Fit α_0 with τ_v3; compute Δχ², Gate P-v3, and ln B_10."""
    from .gw_events import get_event
    from .premerger_bayes import bayes_factor_from_vectors
    from .premerger_phase import _inspiral_mask, fit_premerger_phase_network
    from .premerger_theory import GATE_P_T_END, orbital_phase_from_strain

    inv = inv or InvariantSet()
    model_v3 = PremergerPhaseModelV3.from_invariants(
        inv,
        scale_mode=scale_mode,
        scale_value=scale_value,
        scale_ref=scale_ref,
        scale_power=scale_power,
    )
    r, tau = stack_network_residual_basis_v3(dets, model_v3)
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
        tau_d = phase_basis_template_v3(h_gr, phi, model_v3)[mask]
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
        f"v3: mode={scale_mode}, power={scale_power}, "
        f"value={scale_value:.4g}, ref={scale_ref:.4g}, S={model_v3.scale_factor:.4f}",
        f"α_0={alpha_0:.3e}±{alpha_sig:.3e}  β_eff={alpha_0 * model_v3.scale_factor:.3e}",
        f"Δχ²={dchi:.2f}  lnB={bf.ln_B_10:.2f}  Gate P-v3={'PASS' if gate else 'fail'}",
    ]
    for name, a, s in det_alphas:
        notes.append(f"{name} α_0={a:.3e}±{s:.3e}")
    if not sign_ok:
        notes.append("H1/L1 α_0 signs disagree at >2σ")

    mapping_name = f"v3_{scale_mode}_p{scale_power:g}"
    return MappingV3FitResult(
        event=event_name,
        mapping=mapping_name,
        scale_mode=scale_mode,
        scale_power=float(scale_power),
        scale_value=float(scale_value),
        scale_ref=float(scale_ref),
        scale_factor=float(model_v3.scale_factor),
        alpha_0_hat=float(alpha_0),
        alpha_0_sigma=float(alpha_sig),
        beta_eff=float(alpha_0 * model_v3.scale_factor),
        chi2_gr=chi_gr,
        chi2_topo=chi_topo,
        delta_chi2=float(dchi),
        ln_B_10=float(bf.ln_B_10),
        B_10=float(bf.B_10) if math.isfinite(bf.B_10) else float("inf"),
        kass_raftery=bf.kass_raftery,
        gate_p_v3_pass=bool(gate),
        gate_p_v1_pass=v1_pass,
        alpha_v1_hat=alpha_v1,
        notes=notes,
    )


def score_event_v3(
    event_name: str,
    *,
    project_root,
    scale_mode: ScaleMode = "inv_snr",
    scale_power: float | None = None,
    rho_net: float | None = None,
    distance_mpc: float | None = None,
    d_ref_mpc: float | None = None,
    approximant: str = "IMRPhenomD",
    detectors: list[str] | None = None,
) -> MappingV3FitResult:
    """Prepare network + freeze scale observables; fit v3."""
    from pathlib import Path

    from .pe_waveform import pe_params_for_event
    from .premerger_phase import prepare_premerger_network

    root = Path(project_root)
    detectors = detectors or ["H1", "L1"]
    params = pe_params_for_event(event_name, pe_dir=root / "data" / "pe")

    if scale_mode == "inv_snr":
        power = INV_SNR_POWER_DEFAULT if scale_power is None else float(scale_power)
        if rho_net is None:
            if event_name not in NETWORK_SNR_GWTC1:
                raise KeyError(
                    f"No frozen GWTC-1 network SNR for {event_name}; "
                    "add to NETWORK_SNR_GWTC1 or pass rho_net="
                )
            rho_net = NETWORK_SNR_GWTC1[event_name]
        scale_value = float(rho_net)
        scale_ref = RHO_REF
    elif scale_mode == "distance":
        power = DISTANCE_POWER_DEFAULT if scale_power is None else float(scale_power)
        d_l = float(distance_mpc if distance_mpc is not None else params.distance_mpc)
        if d_ref_mpc is None:
            # Freeze d_ref from GW150914 PE median once
            p914 = pe_params_for_event("GW150914", pe_dir=root / "data" / "pe")
            d_ref_mpc = float(p914.distance_mpc)
        scale_value = d_l
        scale_ref = float(d_ref_mpc)
    else:
        raise ValueError(f"Unknown scale_mode {scale_mode}")

    _event, dets = prepare_premerger_network(
        event_name,
        detectors,
        project_root=root,
        approximant=approximant,
        params=params,
    )
    return fit_premerger_v3_network(
        dets,
        event_name,
        scale_mode=scale_mode,
        scale_value=scale_value,
        scale_ref=scale_ref,
        scale_power=power,
    )


def evaluate_v3_campaign(
    results: dict[str, MappingV3FitResult],
    *,
    scale_mode: ScaleMode,
    scale_power: float,
    ln_b_thr: float = 5.0,
    z_unify_thr: float = 3.0,
) -> dict[str, Any]:
    """Apply pre-registered SUCCESS/FALSIFY/NULL for GW170809 under one scale family."""
    r809 = results.get("GW170809")
    r914 = results.get("GW150914")
    if r809 is None:
        return {
            "verdict": "INCONCLUSIVE",
            "reason": "GW170809 missing",
            "scale_mode": scale_mode,
            "scale_power": scale_power,
        }

    notes: list[str] = []
    p_pass = r809.gate_p_v3_pass
    b_pass = r809.ln_B_10 > ln_b_thr
    notes.append(
        f"GW170809 P-v3={'PASS' if p_pass else 'fail'} lnB={r809.ln_B_10:.2f}"
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
            f"β_eff ratio={beta_ratio:.3f} vs scale ratio={scale_pred:.3f} "
            f"(mode={scale_mode}, power={scale_power})"
        )
        unify_ok = z_alpha0 <= z_unify_thr

    label = f"{scale_mode} power={scale_power}"
    if not p_pass:
        verdict = "NULL"
        reason = f"GW170809 Gate P-v3 fail under {label}"
    elif not b_pass:
        verdict = "FALSIFY"
        reason = (
            f"GW170809 ln B_10={r809.ln_B_10:.2f} ≤ {ln_b_thr} under {label}"
        )
    elif unify_ok is False:
        verdict = "FALSIFY"
        reason = (
            f"GW170809 residual-strong but α_0 not shared with core "
            f"(z={z_alpha0:.2f}>3) — {label} fails unification"
        )
    elif unify_ok is True and p_pass and b_pass:
        verdict = "SUCCESS"
        reason = (
            f"GW170809 P-v3+BF pass and α_0 consistent with GW150914 under {label}"
        )
    else:
        verdict = "INCONCLUSIVE"
        reason = "Missing core comparison or incomplete gates"

    return {
        "verdict": verdict,
        "reason": reason,
        "notes": notes,
        "ln_b_thr": ln_b_thr,
        "z_alpha0_809_vs_914": z_alpha0,
        "unify_ok": unify_ok,
        "beta_eff_ratio": beta_ratio,
        "scale_ratio_pred": scale_pred,
        "scale_mode": scale_mode,
        "scale_power": scale_power,
        "prereg": "docs/PREREG_PREMERGER_MAPPING_V3.md",
    }


def evaluate_v3_family(
    camp_a: dict[str, Any],
    camp_b: dict[str, Any] | None,
) -> dict[str, Any]:
    """Combine P-v3a and optional P-v3b into family-level verdict."""
    if camp_a.get("verdict") == "SUCCESS":
        return {
            "family_verdict": "SUCCESS",
            "reason": "P-v3a (inv_snr q=1) SUCCESS",
            "p_v3a": camp_a,
            "p_v3b": camp_b,
            "bulk_pe_power_family_closed": False,
        }
    if camp_b is None:
        return {
            "family_verdict": camp_a.get("verdict", "INCONCLUSIVE"),
            "reason": (
                f"P-v3a {camp_a.get('verdict')}; P-v3b not run "
                f"({camp_a.get('reason', '')})"
            ),
            "p_v3a": camp_a,
            "p_v3b": None,
            "bulk_pe_power_family_closed": False,
        }
    if camp_b.get("verdict") == "SUCCESS":
        return {
            "family_verdict": "SUCCESS",
            "reason": "P-v3a failed; P-v3b (distance s=1) SUCCESS",
            "p_v3a": camp_a,
            "p_v3b": camp_b,
            "bulk_pe_power_family_closed": False,
        }
    # Both failed unification or NULL
    a_f = camp_a.get("verdict") in ("FALSIFY", "NULL")
    b_f = camp_b.get("verdict") in ("FALSIFY", "NULL")
    if a_f and b_f and camp_a.get("verdict") == "FALSIFY" and camp_b.get("verdict") == "FALSIFY":
        return {
            "family_verdict": "FALSIFY",
            "reason": (
                "Both P-v3a (inv_snr q=1) and P-v3b (distance s=1) FALSIFY "
                "on Unify — bulk PE-power mapping family closed under this pre-reg"
            ),
            "p_v3a": camp_a,
            "p_v3b": camp_b,
            "bulk_pe_power_family_closed": True,
        }
    return {
        "family_verdict": "FALSIFY" if a_f and b_f else "INCONCLUSIVE",
        "reason": (
            f"P-v3a={camp_a.get('verdict')}, P-v3b={camp_b.get('verdict')}"
        ),
        "p_v3a": camp_a,
        "p_v3b": camp_b,
        "bulk_pe_power_family_closed": bool(
            camp_a.get("verdict") == "FALSIFY" and camp_b.get("verdict") == "FALSIFY"
        ),
    }
