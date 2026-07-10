"""
Pre-merger Bayes factor: (GR + topological α) vs pure GR residual.

Nested models on whitened inspiral residual (σ = 1 after whitening):

  H0 (GR):     r = n
  H1 (topo):   r = α τ + n ,  α ~ N(0, σ_prior²)

where τ = −K Φ_orb H[h_GR] is the locked-template basis (W_g, φ_b fixed).

Exact Gaussian marginal likelihood ratio (linear model + Gaussian prior):

  B_10 = Z_1 / Z_0
  log B_10 = −½ log(σ_p² H) + b² / (2 H)

  H = ||τ||² + 1/σ_p² ,  b = τ · r

Cross-checks:
  • Laplace / unrestricted (improper) limit diagnostics
  • BIC: 2 ln B ≈ Δχ² − log N
  • Savage–Dickey: B_10 = p(α=0) / p(α=0 | data)

Pre-registered prior: σ_prior = 1e-3 (covers freeze band ~1e-4; allows |α|~1e-3).
Locks W_g, κ, φ_b never free parameters of the evidence integral.

Discipline: does **not** re-fit the demoted α band. Report B_10 on held-outs
as an LVK-comparable complement to Δχ² / Gate P.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .gw_events import PublicGWEvent, get_event
from .invariants import InvariantSet
from .network_likelihood import DetectorWhitened
from .premerger_phase import (
    _inspiral_mask,
    fit_premerger_phase_network,
    prepare_premerger_network,
)
from .premerger_theory import (
    GATE_P_T_END,
    PremergerPhaseModel,
    orbital_phase_from_strain,
    phase_basis_template,
)

# Pre-registered Gaussian prior width on α (dimensionless)
ALPHA_PRIOR_SIGMA: float = 1.0e-3

# Kass & Raftery (1995) scale on 2 ln B (or ln B thresholds)
# We report ln B_10 and a qualitative grade on |ln B|


@dataclass
class BayesFactorResult:
    """Bayes factor and diagnostics for one residual stack."""

    event: str
    detectors: str
    n_samples: int
    alpha_hat_mle: float
    alpha_hat_map: float
    alpha_sigma_mle: float
    alpha_sigma_post: float
    alpha_prior_sigma: float
    chi2_gr: float
    chi2_topo_mle: float
    delta_chi2: float
    ln_B_10: float
    B_10: float
    ln_B_10_bic: float
    ln_B_10_savage_dickey: float
    kass_raftery: str
    tau_norm2: float
    gate_p_pass: bool | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # JSON-friendly
        if not math.isfinite(d["B_10"]) or d["B_10"] > 1e300:
            d["B_10"] = float("inf") if d["ln_B_10"] > 0 else 0.0
        return d


def kass_raftery_grade(ln_b_10: float) -> str:
    """Qualitative grade on ln B_10 (topo vs GR). Negative ⇒ favor GR."""
    # Use 2 ln B scale internally for KR language, but input is ln B
    two_ln = 2.0 * ln_b_10
    if two_ln < 0:
        # favor H0
        a = abs(two_ln)
        if a < 2:
            return "barely_GR"
        if a < 6:
            return "positive_GR"
        if a < 10:
            return "strong_GR"
        return "very_strong_GR"
    if two_ln < 2:
        return "barely_topo"
    if two_ln < 6:
        return "positive_topo"
    if two_ln < 10:
        return "strong_topo"
    return "very_strong_topo"


def bayes_factor_from_vectors(
    r: np.ndarray,
    tau: np.ndarray,
    *,
    alpha_prior_sigma: float = ALPHA_PRIOR_SIGMA,
    event: str = "",
    detectors: str = "",
    gate_p_pass: bool | None = None,
) -> BayesFactorResult:
    """Exact BF for white Gaussian residual and linear template + N(0,σ_p²) prior."""
    r = np.asarray(r, dtype=float).ravel()
    tau = np.asarray(tau, dtype=float).ravel()
    if r.shape != tau.shape:
        raise ValueError("r and tau shape mismatch")
    n = int(r.size)
    if n < 8:
        raise ValueError("too few samples for Bayes factor")

    tau2 = float(np.sum(tau * tau)) + 1e-60
    b = float(np.sum(tau * r))
    chi2_gr = float(np.sum(r * r))

    # MLE (improper flat prior limit)
    alpha_mle = b / tau2
    chi2_topo = float(np.sum((r - alpha_mle * tau) ** 2))
    dchi = chi2_gr - chi2_topo
    alpha_sig_mle = float(1.0 / math.sqrt(tau2))

    # Gaussian prior
    sp2 = float(alpha_prior_sigma) ** 2
    if sp2 <= 0:
        raise ValueError("alpha_prior_sigma must be positive")
    H = tau2 + 1.0 / sp2
    alpha_map = b / H
    alpha_sig_post = float(1.0 / math.sqrt(H))

    # log B_10 = -0.5 log(σ_p² H) + b²/(2H)
    ln_b = -0.5 * math.log(sp2 * H) + (b * b) / (2.0 * H)

    # BIC approximation: 2 ln B ≈ Δχ² - log N  (1 extra param)
    ln_b_bic = 0.5 * (dchi - math.log(max(n, 2)))

    # Savage–Dickey: B_10 = p(α=0)/p(α=0|data)
    # prior density at 0: 1/sqrt(2π σ_p²)
    # posterior N(α_map, 1/H): density at 0 = sqrt(H/(2π)) exp(-0.5 H α_map²)
    prior0 = 1.0 / math.sqrt(2.0 * math.pi * sp2)
    post0 = math.sqrt(H / (2.0 * math.pi)) * math.exp(-0.5 * H * alpha_map * alpha_map)
    ln_b_sd = math.log(prior0 + 1e-300) - math.log(post0 + 1e-300)
    # For nested models with Gaussian prior, SD should match exact BF

    try:
        b10 = math.exp(ln_b)
    except OverflowError:
        b10 = float("inf")

    notes = [
        f"N={n} whitened samples; σ_noise=1",
        f"σ_prior(α)={alpha_prior_sigma:.3e} (pre-registered)",
        f"||τ||²={tau2:.6e}",
        f"Δχ²={dchi:.4f}",
        f"ln B_10={ln_b:.4f}  (exact Gaussian marginal)",
        f"ln B_10(BIC)={ln_b_bic:.4f}",
        f"ln B_10(Savage–Dickey)={ln_b_sd:.4f}",
        "H0=pure GR residual; H1=GR+α·τ with locked W_g,φ_b",
        "Does not re-fit demoted α band or core locks",
    ]

    return BayesFactorResult(
        event=event,
        detectors=detectors,
        n_samples=n,
        alpha_hat_mle=float(alpha_mle),
        alpha_hat_map=float(alpha_map),
        alpha_sigma_mle=alpha_sig_mle,
        alpha_sigma_post=alpha_sig_post,
        alpha_prior_sigma=float(alpha_prior_sigma),
        chi2_gr=chi2_gr,
        chi2_topo_mle=chi2_topo,
        delta_chi2=float(dchi),
        ln_B_10=float(ln_b),
        B_10=float(b10),
        ln_B_10_bic=float(ln_b_bic),
        ln_B_10_savage_dickey=float(ln_b_sd),
        kass_raftery=kass_raftery_grade(ln_b),
        tau_norm2=float(tau2),
        gate_p_pass=gate_p_pass,
        notes=notes,
    )


def stack_network_residual_basis(
    dets: list[DetectorWhitened],
    *,
    t_end: float = GATE_P_T_END,
    inv: InvariantSet | None = None,
) -> tuple[np.ndarray, np.ndarray, PremergerPhaseModel]:
    """Stack whitened inspiral r and τ across detectors (same as network Gate P)."""
    inv = inv or InvariantSet()
    model = PremergerPhaseModel.from_invariants(inv)
    r_list: list[np.ndarray] = []
    tau_list: list[np.ndarray] = []
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
    return np.concatenate(r_list), np.concatenate(tau_list), model


def bayes_factor_network(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    *,
    t_end: float = GATE_P_T_END,
    alpha_prior_sigma: float = ALPHA_PRIOR_SIGMA,
    inv: InvariantSet | None = None,
    include_gate_p: bool = True,
) -> BayesFactorResult:
    """Network Bayes factor + optional Gate P flag from same residual stack."""
    r, tau, _model = stack_network_residual_basis(dets, t_end=t_end, inv=inv)
    gate = None
    if include_gate_p:
        fit = fit_premerger_phase_network(dets, event, t_end=t_end, inv=inv)
        gate = fit.gate_p_pass
    return bayes_factor_from_vectors(
        r,
        tau,
        alpha_prior_sigma=alpha_prior_sigma,
        event=event.name,
        detectors="+".join(d.detector for d in dets),
        gate_p_pass=gate,
    )


def bayes_factor_for_event(
    event_name: str,
    *,
    project_root: Path | None = None,
    detectors: list[str] | None = None,
    alpha_prior_sigma: float = ALPHA_PRIOR_SIGMA,
    approximant: str = "IMRPhenomD",
) -> BayesFactorResult:
    """End-to-end: prepare pre-merger network and compute B_10."""
    root = project_root or Path(__file__).resolve().parent.parent
    dets_list = detectors or ["H1", "L1"]
    event, dets = prepare_premerger_network(
        event_name,
        dets_list,
        project_root=root,
        approximant=approximant,
    )
    return bayes_factor_network(
        dets,
        event,
        alpha_prior_sigma=alpha_prior_sigma,
        include_gate_p=True,
    )


def injection_bayes_calibration(
    dets: list[DetectorWhitened],
    event: PublicGWEvent,
    *,
    alpha_inj: float,
    alpha_prior_sigma: float = ALPHA_PRIOR_SIGMA,
    inv: InvariantSet | None = None,
    t_end: float = GATE_P_T_END,
    seed: int = 0,
) -> dict[str, Any]:
    """Inject α·τ into residual copy; report B_10 for recovery sanity.

    Background: α_inj=0 should give ln B ≲ 0 typically.
    Loud injection: ln B > 0 expected.
    """
    inv = inv or InvariantSet()
    r, tau, _ = stack_network_residual_basis(dets, t_end=t_end, inv=inv)
    rng = np.random.default_rng(seed)
    # Replace residual with pure noise + optional injection (calibration)
    # Keep using actual residual as noise proxy for α_inj=0 realism;
    # for clean calibration use white noise of unit variance.
    n = r.size
    noise = rng.normal(0.0, 1.0, size=n)
    r_inj = noise + float(alpha_inj) * tau
    bf = bayes_factor_from_vectors(
        r_inj,
        tau,
        alpha_prior_sigma=alpha_prior_sigma,
        event=event.name,
        detectors="injection",
        gate_p_pass=None,
    )
    return {
        "alpha_inj": float(alpha_inj),
        "alpha_hat_mle": bf.alpha_hat_mle,
        "ln_B_10": bf.ln_B_10,
        "B_10": bf.B_10,
        "kass_raftery": bf.kass_raftery,
        "delta_chi2": bf.delta_chi2,
        "n_samples": bf.n_samples,
    }
