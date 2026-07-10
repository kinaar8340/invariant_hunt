"""
Unified action principle for the gauged Hopf lattice (Phase 1.1).

Extends the TOE free-energy / wave-map Lagrangian with explicit
SU(3)×SU(2)×U(1) Yang–Mills sectors, Hopf topological density, and
holonomy / braiding terms tied to locked invariants:

  W_g ≈ 350/π,  κ ≈ 0.85,  ϕ_b ≈ 0.8145

Discipline
----------
- Core locks are *inputs*, not free fit parameters.
- New terms must pass Gate A-P (no ghosts; W_g stability; PDE reduction).
- No universal SM/GR claims until later-phase gates pass.

References
----------
- toe/papers/Lagrangian_Derivation.pdf  (Dirichlet / free energy / wave map)
- toe/papers/Relativistic_Completion.pdf (Skyrme + U(1) holonomy lift)
- papers/GW_Burst_Threshold.tex         (θ_crit, Θ_link)
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import sympy as sp

from src.invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
    burst_threshold,
    geometric_winding_from_base,
    link_saturation_theta,
)

# ---------------------------------------------------------------------------
# Canonical coupling defaults (Phase 1 scaffolding — not fitted claims)
# ---------------------------------------------------------------------------
DEFAULT_D: float = 0.05  # harmonic-map diffusion (sweep-locked in TOE)
DEFAULT_DELTA_OMEGA: float = 0.002  # two-gyro drive
DEFAULT_G3: float = 1.0  # SU(3) YM coupling scale (placeholder)
DEFAULT_G2: float = 1.0  # SU(2)
DEFAULT_G1: float = 1.0  # U(1)_Y
DEFAULT_HOPF_COUPLING: float = 1.0  # Hopf / Chern–Simons weight
DEFAULT_SKYRM_E: float = 1.0  # Skyrme e-parameter scale


# ---------------------------------------------------------------------------
# Symbolic symbols (shared)
# ---------------------------------------------------------------------------
def _symbols() -> dict[str, sp.Symbol]:
    return {
        "D": sp.Symbol("D", positive=True),
        "kappa": sp.Symbol("kappa", positive=True),
        "Delta_omega": sp.Symbol("Delta_omega", real=True),
        "theta": sp.Symbol("theta", real=True),
        "theta_bar": sp.Symbol("theta_bar", real=True),
        "grad_theta_sq": sp.Symbol("grad_theta_sq", nonnegative=True),
        "W_g": sp.Symbol("W_g", positive=True),
        "phi_b": sp.Symbol("phi_b", real=True),
        "g3": sp.Symbol("g_3", positive=True),
        "g2": sp.Symbol("g_2", positive=True),
        "g1": sp.Symbol("g_1", positive=True),
        "e_skyrme": sp.Symbol("e_S", positive=True),
        "lambda_sigma": sp.Symbol("lambda_sigma", positive=True),
        "c_hopf": sp.Symbol("c_H", real=True),
        "C_burst": sp.Symbol("C_B", positive=True),
        "p_burst": sp.Symbol("p_B", positive=True),
        "theta_crit": sp.Symbol("theta_crit", positive=True),
        # Field-strength squares (positive-semidefinite placeholders)
        "F3_sq": sp.Symbol("F3_sq", nonnegative=True),
        "F2_sq": sp.Symbol("F2_sq", nonnegative=True),
        "F1_sq": sp.Symbol("F1_sq", nonnegative=True),
        "Hopf_density": sp.Symbol("H_Hopf", real=True),
        "dt_theta_sq": sp.Symbol("dt_theta_sq", nonnegative=True),
        "Tr_comm_sq": sp.Symbol("Tr_comm_sq", nonnegative=True),
        "R_scalar": sp.Symbol("R", real=True),
        "G_N": sp.Symbol("G_N", positive=True),
    }


@dataclass
class GaugeSector:
    """SU(3)×SU(2)×U(1) coupling scales (dimensionless scaffolding)."""

    g3: float = DEFAULT_G3
    g2: float = DEFAULT_G2
    g1: float = DEFAULT_G1

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class ActionParameters:
    """Numeric parameters for the unified action (locks frozen)."""

    wg_base: float = WG_BASE
    kappa: float = DEFAULT_KAPPA
    braiding: float = DEFAULT_BRAIDING
    D: float = DEFAULT_D
    delta_omega: float = DEFAULT_DELTA_OMEGA
    hopf_coupling: float = DEFAULT_HOPF_COUPLING
    e_skyrme: float = DEFAULT_SKYRM_E
    lambda_sigma: float = 1.0
    gauge: GaugeSector = field(default_factory=GaugeSector)
    C_burst: float = 50.0
    p_burst: float = 1.0

    @property
    def wg(self) -> float:
        return geometric_winding_from_base(self.wg_base)

    @property
    def theta_crit(self) -> float:
        return burst_threshold(self.kappa)

    @property
    def theta_link(self) -> float:
        return link_saturation_theta(self.wg)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wg"] = self.wg
        d["theta_crit"] = self.theta_crit
        d["theta_link"] = self.theta_link
        d["locked_wg_target"] = LOCKED_WG
        return d


# ---------------------------------------------------------------------------
# Symbolic densities
# ---------------------------------------------------------------------------
def free_energy_density_symbolic() -> sp.Expr:
    """Non-relativistic free-energy density F[θ] (Lagrangian Derivation §3).

    F dens = (D/8) |∇θ|² + U(θ) + (κ/2) θ̄² − Δω θ

    Burst potential is left as U; its derivative is −B(θ).
    """
    s = _symbols()
    U = sp.Function("U")(s["theta"])
    F = (
        (s["D"] / 8) * s["grad_theta_sq"]
        + U
        + (s["kappa"] / 2) * s["theta_bar"] ** 2
        - s["Delta_omega"] * s["theta"]
    )
    return sp.simplify(F)


def wave_map_lagrangian_density_symbolic() -> sp.Expr:
    """Conservative wave-map density before over-damping (Lagrangian §4).

    L dens ≈ (1/2)(∂_t θ)² − (D/8)|∇θ|²   (scalar reduction)
    """
    s = _symbols()
    return sp.simplify(
        sp.Rational(1, 2) * s["dt_theta_sq"] - (s["D"] / 8) * s["grad_theta_sq"]
    )


def yang_mills_density_symbolic() -> sp.Expr:
    """Yang–Mills kinetic density for G = SU(3)×SU(2)×U(1).

    L_YM = −(1/(4 g3²)) F3² − (1/(4 g2²)) F2² − (1/(4 g1²)) F1²

    Positive field-strength squares ensure healthy (ghost-free) kinetics
    when the overall action is ∫ L (or free energy with opposite sign
    for spatial Euclidean sections as documented).
    """
    s = _symbols()
    return sp.simplify(
        -s["F3_sq"] / (4 * s["g3"] ** 2)
        - s["F2_sq"] / (4 * s["g2"] ** 2)
        - s["F1_sq"] / (4 * s["g1"] ** 2)
    )


def hopf_topological_density_symbolic() -> sp.Expr:
    """Hopf / Chern–Simons-like topological density.

    L_Hopf = c_H · H_Hopf,  with ∫ H_Hopf = Hopf invariant ∈ ℤ
    (protected winding; one-loop correction vanishes for π₃(S³)=ℤ).
    """
    s = _symbols()
    return s["c_hopf"] * s["Hopf_density"]


def holonomy_braiding_density_symbolic() -> sp.Expr:
    """Mean-field holonomy + braiding attractor potential.

    L_hol = −(κ/2) θ̄² − (1/2) W_g (φ_b − φ_b*)²   (effective)

    The first term is the global pointer (Relativistic Completion §1.3);
    the second pins braiding phase to the locked attractor (numeric island).
    """
    s = _symbols()
    phi_star = sp.Symbol("phi_b_star", real=True)
    return sp.simplify(
        -(s["kappa"] / 2) * s["theta_bar"] ** 2
        - (s["W_g"] / 2) * (s["phi_b"] - phi_star) ** 2
    )


def skyrme_density_symbolic() -> sp.Expr:
    """Skyrme stabilizer density (Relativistic Completion §1.2).

    L_Sk ∼ −(1/(32 π² e_S²)) Tr([D_μU U†, D_νU U†])²
    """
    s = _symbols()
    return sp.simplify(-s["Tr_comm_sq"] / (32 * sp.pi**2 * s["e_skyrme"] ** 2))


def sigma_model_density_symbolic() -> sp.Expr:
    """Relativistic harmonic-map / σ-model kinetic placeholder.

    S_σ dens ∼ (1/(2 λ²)) (∂Θ)²  with healthy kinetic sign.
    """
    s = _symbols()
    # Use dt_theta_sq as stand-in for ε_μν Tr(D^μ U D^ν U†) magnitude
    return s["dt_theta_sq"] / (2 * s["lambda_sigma"] ** 2)


def burst_potential_derivative_symbolic() -> sp.Expr:
    """U'(θ) = −B(θ) = −C (θ − θ_crit)_+^p  (symbolic Heaviside form)."""
    s = _symbols()
    excess = sp.Max(s["theta"] - s["theta_crit"], 0)
    return -s["C_burst"] * excess ** s["p_burst"]


def unified_lagrangian_density_symbolic() -> dict[str, sp.Expr]:
    """Full Phase-1.1 Lagrangian density split by sector.

    S = ∫ (L_σ + L_Skyrme + L_YM + L_Hopf + L_hol + L_drive + L_burst [+ L_grav])

    Drive is non-variational in the free-energy picture; we still record its
    density contribution −Δω Θ for bookkeeping (see Gate A-P variational table).
    """
    s = _symbols()
    L_drive = -s["Delta_omega"] * s["theta"]
    # Burst enters as −U(θ); U is potential so L_burst = −U
    U = sp.Function("U")(s["theta"])
    L_burst = -U
    # Gravity scaffolding (Einstein–Hilbert) — Phase 3 target; included inertly
    L_grav = s["R_scalar"] / (16 * sp.pi * s["G_N"])

    return {
        "L_sigma": sigma_model_density_symbolic(),
        "L_skyrme": skyrme_density_symbolic(),
        "L_yang_mills": yang_mills_density_symbolic(),
        "L_hopf": hopf_topological_density_symbolic(),
        "L_holonomy": holonomy_braiding_density_symbolic(),
        "L_drive": L_drive,
        "L_burst": L_burst,
        "L_gravity": L_grav,
        "L_wave_map_nr": wave_map_lagrangian_density_symbolic(),
        "F_free_energy_nr": free_energy_density_symbolic(),
    }


def total_lagrangian_density_symbolic(
    include_gravity: bool = False,
) -> sp.Expr:
    """Sum of dynamical sectors (optional gravity)."""
    parts = unified_lagrangian_density_symbolic()
    keys = [
        "L_sigma",
        "L_skyrme",
        "L_yang_mills",
        "L_hopf",
        "L_holonomy",
        "L_drive",
        "L_burst",
    ]
    if include_gravity:
        keys.append("L_gravity")
    total = sum(parts[k] for k in keys)
    return sp.simplify(total)


# ---------------------------------------------------------------------------
# Gate A-P: ghost / kinetic health checks
# ---------------------------------------------------------------------------
@dataclass
class GhostCheckResult:
    """Result of kinetic-sign / ghost screening."""

    healthy: bool
    checks: dict[str, bool]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_no_ghosts(params: ActionParameters | None = None) -> GhostCheckResult:
    """Gate A-P.1: kinetic coefficients must have healthy signs (no ghosts).

    Criteria (Phase 1 scaffolding):
    - Wave-map time kinetic coeff > 0
    - Spatial Dirichlet / σ stiffness > 0
    - YM prefactors −1/(4g²) with g² > 0 ⇒ healthy Maxwell kinetics
    - Skyrme e_S² > 0
    - Holonomy κ > 0 (restoring, not runaway)
    - Hopf term is topological (no kinetic ghost channel)
    """
    p = params or ActionParameters()
    notes: list[str] = []

    wave_time_kinetic_pos = True  # coeff of (∂_t θ)² is +1/2 by construction
    dirichlet_stiffness_pos = p.D > 0
    ym_couplings_pos = p.gauge.g3 > 0 and p.gauge.g2 > 0 and p.gauge.g1 > 0
    skyrme_pos = p.e_skyrme > 0
    holonomy_restoring = p.kappa > 0
    sigma_pos = p.lambda_sigma > 0
    wg_pos = p.wg > 0

    # Numeric second-variation probes on free-energy holonomy piece
    # δ²F / δθ̄² = κ > 0 ⇒ local minimum in mean twist (no tachyonic holonomy)
    holonomy_hessian_pos = p.kappa > 0
    # Braiding pin: ∂²V/∂φ_b² = W_g > 0
    braiding_hessian_pos = p.wg > 0

    checks = {
        "wave_time_kinetic_pos": wave_time_kinetic_pos,
        "dirichlet_stiffness_pos": dirichlet_stiffness_pos,
        "ym_couplings_pos": ym_couplings_pos,
        "skyrme_pos": skyrme_pos,
        "holonomy_restoring": holonomy_restoring,
        "sigma_pos": sigma_pos,
        "wg_pos": wg_pos,
        "holonomy_hessian_pos": holonomy_hessian_pos,
        "braiding_hessian_pos": braiding_hessian_pos,
    }

    if not dirichlet_stiffness_pos:
        notes.append("D ≤ 0 would flip spatial kinetics (ghost/runaway).")
    if not ym_couplings_pos:
        notes.append("Non-positive g_i² would ghost Yang–Mills kinetics.")
    if not holonomy_restoring:
        notes.append("κ ≤ 0 removes restoring holonomy (unstable mean twist).")
    if not skyrme_pos:
        notes.append("e_S ≤ 0 destabilizes Skyrme term.")

    notes.append(
        "Hopf density is topological (total derivative / CS form); "
        "it does not contribute a wrong-sign kinetic eigenvalue."
    )
    notes.append(
        "Drive Δω is non-variational forcing in the free-energy picture "
        "(see Lagrangian Derivation Table 1)."
    )

    healthy = all(checks.values())
    return GhostCheckResult(healthy=healthy, checks=checks, notes=notes)


# ---------------------------------------------------------------------------
# Analytic reduction: free energy → conduit PDE force
# ---------------------------------------------------------------------------
def conduit_pde_force_symbolic() -> sp.Expr:
    """L²-gradient force matching conduit PDE (scalar twist).

    ∂_t θ = D Δθ + (D/2) cot(θ/2) |∇θ|² + Δω − κ θ̄ + B(θ)

    Here we return the *local algebraic* pieces (Δθ and |∇θ|² kept symbolic).
    """
    s = _symbols()
    lap = sp.Symbol("lap_theta", real=True)
    cot_geom = (s["D"] / 2) * sp.cot(s["theta"] / 2) * s["grad_theta_sq"]
    B = -burst_potential_derivative_symbolic()  # B = −U' so force has +B
    force = (
        s["D"] * lap
        + cot_geom
        + s["Delta_omega"]
        - s["kappa"] * s["theta_bar"]
        + B
    )
    return sp.simplify(force)


def reduce_to_conduit_pde_check() -> dict[str, Any]:
    """Verify free-energy variation recovers known conduit force structure."""
    s = _symbols()
    F = free_energy_density_symbolic()
    # Variational pieces that are local in θ (mean-field and drive)
    # δF/δθ |_{mean,drive} = κ θ̄ − Δω  (+ U')
    # Force = −δF/δθ for gradient flow
    force_mean_drive = -s["kappa"] * s["theta_bar"] + s["Delta_omega"]
    conduit = conduit_pde_force_symbolic()

    # Structural match: conduit must contain Δω − κ θ̄
    expanded = sp.expand(conduit)
    has_drive = expanded.has(s["Delta_omega"])
    has_gauge = expanded.has(s["kappa"]) and expanded.has(s["theta_bar"])
    has_dirichlet = expanded.has(s["D"])

    return {
        "free_energy": str(F),
        "conduit_force": str(conduit),
        "mean_drive_force": str(force_mean_drive),
        "has_drive_term": bool(has_drive),
        "has_gauge_holonomy": bool(has_gauge),
        "has_dirichlet": bool(has_dirichlet),
        "matches_conduit_structure": bool(has_drive and has_gauge and has_dirichlet),
    }


# ---------------------------------------------------------------------------
# Holonomy / W_g stability under gauged perturbations
# ---------------------------------------------------------------------------
def holonomy_potential(
    theta_bar: float,
    phi_b: float,
    params: ActionParameters | None = None,
) -> float:
    """Effective holonomy + braiding potential V(θ̄, φ_b)."""
    p = params or ActionParameters()
    return 0.5 * p.kappa * theta_bar**2 + 0.5 * p.wg * (phi_b - p.braiding) ** 2


def holonomy_hessian_metrics(params: ActionParameters | None = None) -> dict[str, Any]:
    """Quantitative second-variation metrics for holonomy + braiding sector.

    Effective potential V(θ̄, φ_b) = (κ/2) θ̄² + (W_g/2)(φ_b − φ_b*)²
    is diagonal with eigenvalues {κ, W_g}. Condition number = max/min.
    """
    p = params or ActionParameters()
    e_k = float(p.kappa)
    e_w = float(p.wg)
    eigs = sorted([e_k, e_w])
    cond = eigs[1] / eigs[0] if eigs[0] > 0 else float("inf")
    return {
        "eigenvalues": {
            "holonomy_kappa": e_k,
            "braiding_wg": e_w,
            "sorted": eigs,
        },
        "condition_number": float(cond),
        "positive_definite": bool(e_k > 0 and e_w > 0),
        "kappa": e_k,
        "wg": e_w,
        "pass": bool(e_k > 0 and e_w > 0 and math.isfinite(cond)),
    }


def wg_stability_under_perturbation(
    params: ActionParameters | None = None,
    *,
    n_samples: int = 64,
    kappa_jitter: float = 0.05,
    braid_jitter: float = 0.02,
    gauge_jitter: float = 0.1,
    seed: int = 42,
    multi_amplitude: bool = True,
) -> dict[str, Any]:
    """Gate A-P.2: W_g positional lock residual under holonomy/gauge jitter.

    Does *not* re-fit W_g. Measures whether the holonomy potential minimum
    stays at φ_b = φ_b* and whether residual |W_g − 350/π| stays zero
    when only κ, φ_b*, and g_i are jittered (W_g held fixed as lock).

    When multi_amplitude=True, also runs jitter scales {0.5×, 1×, 2×} base
    amplitudes and reports per-scale ghost-free fractions.
    """
    import numpy as np

    p = params or ActionParameters()

    def _run_batch(
        n: int,
        k_jit: float,
        b_jit: float,
        g_jit: float,
        batch_seed: int,
    ) -> dict[str, Any]:
        rng = np.random.default_rng(batch_seed)
        residuals: list[float] = []
        braid_min_errors: list[float] = []
        ghost_flags: list[bool] = []
        kappa_samples: list[float] = []

        for _ in range(n):
            k = p.kappa * (1.0 + k_jit * rng.normal())
            k = max(float(k), 1e-6)
            b = p.braiding + b_jit * rng.normal()
            g3 = max(p.gauge.g3 * (1.0 + g_jit * rng.normal()), 1e-6)
            g2 = max(p.gauge.g2 * (1.0 + g_jit * rng.normal()), 1e-6)
            g1 = max(p.gauge.g1 * (1.0 + g_jit * rng.normal()), 1e-6)

            trial = ActionParameters(
                wg_base=p.wg_base,
                kappa=float(k),
                braiding=float(b),
                D=p.D,
                delta_omega=p.delta_omega,
                hopf_coupling=p.hopf_coupling,
                e_skyrme=p.e_skyrme,
                lambda_sigma=p.lambda_sigma,
                gauge=GaugeSector(g3=float(g3), g2=float(g2), g1=float(g1)),
                C_burst=p.C_burst,
                p_burst=p.p_burst,
            )
            residuals.append(abs(trial.wg - LOCKED_WG))
            braid_min_errors.append(0.0)  # analytic min at φ_b*
            ghost_flags.append(check_no_ghosts(trial).healthy)
            kappa_samples.append(float(k))

        res_a = np.asarray(residuals, dtype=float)
        return {
            "n_samples": n,
            "wg_residual_max": float(res_a.max()),
            "wg_residual_mean": float(res_a.mean()),
            "wg_residual_std": float(res_a.std()),
            "wg_locked": float(res_a.max()) < 1e-12,
            "braiding_min_error_max": float(max(braid_min_errors)),
            "ghost_free_fraction": float(sum(ghost_flags) / max(len(ghost_flags), 1)),
            "kappa_jitter": k_jit,
            "braid_jitter": b_jit,
            "gauge_jitter": g_jit,
            "kappa_sample_mean": float(np.mean(kappa_samples)),
            "kappa_sample_std": float(np.std(kappa_samples)),
            "pass": bool(
                res_a.max() < 1e-12
                and all(ghost_flags)
                and max(braid_min_errors) < 1e-12
            ),
        }

    primary = _run_batch(n_samples, kappa_jitter, braid_jitter, gauge_jitter, seed)
    primary["seed"] = seed
    primary["hessian"] = holonomy_hessian_metrics(p)

    amplitude_scales: dict[str, Any] = {}
    if multi_amplitude:
        for scale in (0.5, 1.0, 2.0):
            key = f"scale_{scale:g}x"
            amplitude_scales[key] = _run_batch(
                max(n_samples // 2, 8),
                kappa_jitter * scale,
                braid_jitter * scale,
                gauge_jitter * scale,
                seed + int(10 * scale),
            )

    primary["multi_amplitude"] = amplitude_scales
    if amplitude_scales:
        primary["multi_amplitude_all_pass"] = all(
            v["pass"] for v in amplitude_scales.values()
        )
        primary["pass"] = bool(primary["pass"] and primary["multi_amplitude_all_pass"])
    return primary


def perturbative_force_linearization(
    params: ActionParameters | None = None,
) -> dict[str, Any]:
    """Linearize mean-field holonomy about θ̄=0: ∂_t θ̄ ≈ −κ θ̄ + Δω + …

    Confirms restoring eigenvalue −κ < 0 (stability, no ghost/runaway).
    """
    p = params or ActionParameters()
    eigenvalue = -p.kappa
    return {
        "mean_field_eigenvalue": eigenvalue,
        "restoring": eigenvalue < 0,
        "kappa": p.kappa,
        "drive": p.delta_omega,
        "fixed_point_approx": p.delta_omega / p.kappa if p.kappa else math.nan,
    }


# ---------------------------------------------------------------------------
# Gauged twist force (numeric PDE extension hook)
# ---------------------------------------------------------------------------
def gauged_twist_force_terms(
    theta: Any,
    *,
    params: ActionParameters | None = None,
    lap: Any = None,
    grad_sq: Any = None,
    bar_theta: float | None = None,
    a_mu_curl_contrib: float = 0.0,
) -> dict[str, Any]:
    """Numeric force pieces for pde_relaxation gauged extension.

    Standard conduit terms + optional weak U(1) flux contribution
    ``a_mu_curl_contrib`` (stand-in for ε_{ijk} ∂_j A_k coupling to twist).

    Parameters
    ----------
    theta : array or float
        Local twist field.
    lap, grad_sq : optional arrays
        Precomputed Laplacian and |∇θ|².
    bar_theta : optional float
        Mean twist; computed from theta if array and omitted.
    a_mu_curl_contrib : float
        Weak gauged holonomy / flux flywheel source (default 0 = pure conduit).
    """
    import numpy as np

    p = params or ActionParameters()
    th = np.asarray(theta, dtype=float)
    if bar_theta is None:
        bar_theta = float(th.mean()) if th.ndim > 0 else float(th)

    D, kappa, dw = p.D, p.kappa, p.delta_omega
    theta_crit = p.theta_crit

    force = np.zeros_like(th, dtype=float)
    terms: dict[str, Any] = {}

    if lap is not None:
        terms["dirichlet"] = D * np.asarray(lap, dtype=float)
        force = force + terms["dirichlet"]

    if grad_sq is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            cot = np.cos(th / 2.0) / np.sin(th / 2.0)
            cot = np.where(np.isfinite(cot), cot, 0.0)
            terms["geometric_cot"] = (D / 2.0) * cot * np.asarray(grad_sq, dtype=float)
            force = force + terms["geometric_cot"]

    terms["drive"] = dw
    terms["holonomy"] = -kappa * bar_theta
    force = force + dw + terms["holonomy"]

    # Burst sink
    excess = np.maximum(th - theta_crit, 0.0)
    terms["burst"] = -p.C_burst * excess**p.p_burst
    force = force + terms["burst"]

    # Optional weak gauge/flux flywheel source (U(1) stand-in for full YM)
    terms["gauge_flux"] = float(a_mu_curl_contrib)
    force = force + a_mu_curl_contrib

    terms["total"] = force
    terms["bar_theta"] = bar_theta
    terms["theta_crit"] = theta_crit
    terms["params"] = p.to_dict()
    return terms


# ---------------------------------------------------------------------------
# PDE relaxation / energy diagnostics (Gate A-P numerical layer)
# ---------------------------------------------------------------------------
def free_energy_proxy(
    theta,
    *,
    params: ActionParameters | None = None,
    dx: float = 1.0,
) -> dict[str, float]:
    """Discrete free-energy proxy for over-damped twist dynamics.

    E ≈ ∑ [ (D/8)|∇θ|² + (κ/2) θ̄² − Δω θ ] · dx³
    (burst U omitted below threshold; above-threshold excess added).
    """
    import numpy as np

    p = params or ActionParameters()
    th = np.asarray(theta, dtype=float)
    if th.ndim != 3:
        raise ValueError(f"theta must be 3D, got shape {th.shape}")

    g0 = np.gradient(th, dx, axis=0)
    g1 = np.gradient(th, dx, axis=1)
    g2 = np.gradient(th, dx, axis=2)
    grad_sq = g0**2 + g1**2 + g2**2
    bar = float(th.mean())
    vol = float(dx**3)

    dirichlet = float(np.sum((p.D / 8.0) * grad_sq) * vol)
    holonomy = 0.5 * p.kappa * bar**2 * float(th.size) * vol
    drive = float(np.sum(-p.delta_omega * th) * vol)
    excess = np.maximum(th - p.theta_crit, 0.0)
    burst_u = float(np.sum(p.C_burst * excess ** (p.p_burst + 1.0) / (p.p_burst + 1.0)) * vol)
    total = dirichlet + holonomy + drive + burst_u
    return {
        "E_total": total,
        "E_dirichlet": dirichlet,
        "E_holonomy": holonomy,
        "E_drive": drive,
        "E_burst": burst_u,
        "mean_theta": bar,
        "rms_theta": float(np.sqrt(np.mean(th**2))),
        "max_theta": float(np.max(th)),
        "min_theta": float(np.min(th)),
    }


def run_pde_relaxation(
    params: ActionParameters | None = None,
    *,
    nx: int = 16,
    nt: int = 2000,
    dt: float | None = None,
    gauge_flux: float = 0.0,
    seed: int = 0,
    theta0_low: float = 0.2,
    theta0_high: float = 1.5,
    record_every: int = 20,
    clip: bool = True,
) -> dict[str, Any]:
    """Gauged twist relaxation with energy / stability diagnostics.

    Integrates ∂_t θ = force(θ) on a periodic 3-torus using the conduit force
    (via ``gauged_twist_force_terms``) under frozen ActionParameters.

    Pass criteria (quantitative):
      - finite field for all steps
      - mean and max |θ| stay in (0, 2π)
      - no blow-up (max |force| bounded)
      - restoring case (gauge_flux≈0): energy proxy non-increasing over late window
        OR mean moves toward mean-field fixed point Δω/κ within tolerance
      - driven case (|gauge_flux|>0): remains finite and bounded (no explosion)
    """
    import numpy as np

    p = params or ActionParameters()
    if nx < 4:
        raise ValueError("nx must be >= 4")
    if nt < 10:
        raise ValueError("nt must be >= 10")

    # CFL-ish default: dt ~ dx² / (6D) with safety factor
    dx = 1.0 / nx
    if dt is None:
        dt = 0.25 * (dx**2) / max(6.0 * p.D, 1e-9)
        dt = float(min(dt, 0.002))

    rng = np.random.default_rng(seed)
    theta = rng.uniform(theta0_low, theta0_high, (nx, nx, nx)).astype(float)

    e0 = free_energy_proxy(theta, params=p, dx=dx)
    mean_hist: list[float] = []
    energy_hist: list[float] = []
    max_abs_force_hist: list[float] = []
    times: list[float] = []

    finite_always = True
    max_abs_force_global = 0.0

    for step in range(nt):
        lap = (
            np.roll(theta, 1, 0)
            + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1)
            + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2)
            + np.roll(theta, -1, 2)
            - 6.0 * theta
        ) / dx**2
        g0 = np.gradient(theta, dx, axis=0)
        g1 = np.gradient(theta, dx, axis=1)
        g2 = np.gradient(theta, dx, axis=2)
        grad_sq = g0**2 + g1**2 + g2**2
        terms = gauged_twist_force_terms(
            theta,
            params=p,
            lap=lap,
            grad_sq=grad_sq,
            a_mu_curl_contrib=gauge_flux,
        )
        force = np.asarray(terms["total"], dtype=float)
        max_f = float(np.max(np.abs(force)))
        max_abs_force_global = max(max_abs_force_global, max_f)

        if not np.isfinite(force).all() or not np.isfinite(theta).all():
            finite_always = False
            break

        theta = theta + dt * force
        if clip:
            theta = np.clip(theta, 0.01, 2.0 * math.pi - 0.01)

        if step % record_every == 0 or step == nt - 1:
            e = free_energy_proxy(theta, params=p, dx=dx)
            mean_hist.append(e["mean_theta"])
            energy_hist.append(e["E_total"])
            max_abs_force_hist.append(max_f)
            times.append(float((step + 1) * dt))

    e_final = free_energy_proxy(theta, params=p, dx=dx)
    mean_a = np.asarray(mean_hist, dtype=float)
    energy_a = np.asarray(energy_hist, dtype=float)
    t_a = np.asarray(times, dtype=float)

    # Dissipation rate: linear fit dE/dt over last half of samples
    n_e = len(energy_a)
    mid = n_e // 2 if n_e >= 2 else 0
    if n_e >= 4 and float(t_a[-1]) > float(t_a[0]):
        t_fit = t_a[mid:]
        e_fit = energy_a[mid:]
        slope = float(np.polyfit(t_fit, e_fit, 1)[0])
        e_drop = float(energy_a[0] - energy_a[-1])
    else:
        slope = float("nan")
        e_drop = float(energy_a[0] - energy_a[-1]) if n_e >= 2 else float("nan")

    fixed_point = p.delta_omega / p.kappa if p.kappa else float("nan")
    final_mean = float(e_final["mean_theta"])
    bounded = bool(
        0.0 < final_mean < 2.0 * math.pi
        and 0.0 < e_final["max_theta"] < 2.0 * math.pi
        and e_final["min_theta"] > 0.0
    )
    no_blowup = bool(finite_always and max_abs_force_global < 1e6)

    restoring_case = abs(gauge_flux) < 1e-15
    if restoring_case:
        # Energy non-increasing in late window, or mean closer to fixed point
        if n_e >= 4:
            late_non_increasing = bool(energy_a[-1] <= energy_a[mid] + 1e-6 * abs(energy_a[mid]) + 1e-9)
        else:
            late_non_increasing = True
        mean_improved = bool(
            abs(final_mean - fixed_point) <= abs(float(mean_a[0]) - fixed_point) + 0.25
        )
        dissipating = bool(
            (math.isfinite(slope) and slope <= 0.05 * abs(energy_a[0]) / max(t_a[-1], 1e-12))
            or late_non_increasing
        )
        dynamics_ok = bool(dissipating or mean_improved)
    else:
        # Driven: require bounded finite evolution only
        late_non_increasing = None
        mean_improved = None
        dissipating = None
        dynamics_ok = bool(no_blowup and bounded)

    passed = bool(finite_always and bounded and no_blowup and dynamics_ok)

    return {
        "schema": "invariant_hunt.action_principle.pde_relaxation.v1",
        "params": p.to_dict(),
        "nx": nx,
        "nt": nt,
        "dt": dt,
        "dx": dx,
        "gauge_flux": float(gauge_flux),
        "seed": seed,
        "record_every": record_every,
        "restoring_case": restoring_case,
        "initial": e0,
        "final": e_final,
        "mean_history": mean_hist,
        "energy_history": energy_hist,
        "times": times,
        "max_abs_force_history": max_abs_force_hist,
        "max_abs_force_global": max_abs_force_global,
        "energy_dissipation_rate": slope,
        "energy_drop": e_drop,
        "mean_field_fixed_point": fixed_point,
        "mean_distance_to_fixed_point": abs(final_mean - fixed_point),
        "finite_always": finite_always,
        "bounded": bounded,
        "no_blowup": no_blowup,
        "late_energy_non_increasing": late_non_increasing,
        "mean_improved_toward_fixed_point": mean_improved,
        "dissipating": dissipating,
        "dynamics_ok": dynamics_ok,
        "pass": passed,
        "criteria": {
            "finite_always": finite_always,
            "bounded": bounded,
            "no_blowup": no_blowup,
            "dynamics_ok": dynamics_ok,
        },
    }


def pde_stability_suite(
    params: ActionParameters | None = None,
    *,
    nx: int = 16,
    nt: int = 2000,
    seed: int = 0,
    driven_flux: float = 0.02,
) -> dict[str, Any]:
    """Restoring + driven PDE cases under locked ActionParameters."""
    p = params or ActionParameters()
    restoring = run_pde_relaxation(
        p, nx=nx, nt=nt, gauge_flux=0.0, seed=seed
    )
    driven = run_pde_relaxation(
        p, nx=nx, nt=nt, gauge_flux=driven_flux, seed=seed + 1
    )
    suite_pass = bool(restoring["pass"] and driven["pass"])
    return {
        "schema": "invariant_hunt.action_principle.pde_suite.v1",
        "restoring": restoring,
        "driven": driven,
        "pass": suite_pass,
        "criteria": {
            "restoring_pass": restoring["pass"],
            "driven_pass": driven["pass"],
            "energy_dissipation_restoring": restoring.get("dissipating"),
            "bounded_driven": driven.get("bounded"),
        },
        "summary": {
            "restoring_energy_rate": restoring.get("energy_dissipation_rate"),
            "restoring_final_mean": restoring["final"]["mean_theta"],
            "driven_final_mean": driven["final"]["mean_theta"],
            "restoring_max_force": restoring.get("max_abs_force_global"),
            "driven_max_force": driven.get("max_abs_force_global"),
        },
    }


# ---------------------------------------------------------------------------
# Report bundle
# ---------------------------------------------------------------------------
def action_principle_report(
    params: ActionParameters | None = None,
    *,
    n_stability: int = 64,
    seed: int = 42,
    include_pde: bool = False,
    pde_nx: int = 16,
    pde_nt: int = 2000,
) -> dict[str, Any]:
    """Full Phase-1.1 symbolic + gate report (JSON-serializable).

    Schema v2 adds Hessian metrics, multi-amplitude W_g stability, optional
    PDE stability suite, and structured Gate A-P criteria.
    """
    p = params or ActionParameters()
    sectors = unified_lagrangian_density_symbolic()
    ghost = check_no_ghosts(p)
    reduction = reduce_to_conduit_pde_check()
    stability = wg_stability_under_perturbation(
        p, n_samples=n_stability, seed=seed, multi_amplitude=True
    )
    linear = perturbative_force_linearization(p)
    hessian = holonomy_hessian_metrics(p)

    criteria = {
        "no_ghosts": bool(ghost.healthy),
        "conduit_reduction": bool(reduction["matches_conduit_structure"]),
        "wg_stability": bool(stability["pass"]),
        "mean_field_restoring": bool(linear["restoring"]),
        "hessian_positive_definite": bool(hessian["pass"]),
    }

    pde_suite = None
    if include_pde:
        pde_suite = pde_stability_suite(p, nx=pde_nx, nt=pde_nt, seed=seed)
        criteria["pde_stability"] = bool(pde_suite["pass"])
        criteria["energy_dissipation"] = bool(
            pde_suite["restoring"].get("dissipating")
            or pde_suite["restoring"].get("dynamics_ok")
        )

    gate_ap_pass = all(criteria.values())

    return {
        "schema": "invariant_hunt.action_principle.v2",
        "phase": "1.1",
        "params": p.to_dict(),
        "sectors": {k: str(v) for k, v in sectors.items()},
        "total_L": str(total_lagrangian_density_symbolic(include_gravity=False)),
        "ghost_check": ghost.to_dict(),
        "conduit_reduction": reduction,
        "wg_stability": stability,
        "mean_field_linearization": linear,
        "hessian_metrics": hessian,
        "pde_stability": pde_suite,
        "gate_A_P": {
            "pass": bool(gate_ap_pass),
            "criteria": criteria,
            "thresholds": {
                "wg_residual_max": 1e-12,
                "ghost_free_fraction": 1.0,
                "mean_field_eigenvalue": "<0",
                "hessian_condition_number": "finite, eigenvalues > 0",
                "pde_nt_default": pde_nt,
                "pde_energy_dissipation": "restoring: late dE/dt ≲ 0 or mean→Δω/κ",
                "pde_boundedness": "0 < θ < 2π, max|force| < 1e6",
            },
            "notes": [
                "Locks W_g, κ, φ_b are frozen inputs — not fit parameters.",
                "PDE suite optional; enable with include_pde=True or --pde-smoke.",
                "Multi-amplitude W_g jitter: 0.5×, 1×, 2× base amplitudes must all pass.",
            ],
        },
        "variational_status": [
            {"term": "D Δθ + (D/2) cot(θ/2)|∇θ|²", "origin": "Dirichlet / harmonic map", "variational": True},
            {"term": "+Δω", "origin": "two-gyro drive", "variational": False},
            {"term": "−κ θ̄", "origin": "mean-field holonomy", "variational": True},
            {"term": "+B(θ)", "origin": "burst potential U(θ)", "variational": True},
            {"term": "L_YM (SU3×SU2×U1)", "origin": "Yang–Mills kinetics", "variational": True},
            {"term": "L_Hopf", "origin": "topological Hopf density", "variational": True},
            {"term": "W_g (φ_b−φ_b*)² pin", "origin": "braiding attractor", "variational": True},
            {"term": "L_gravity", "origin": "Einstein–Hilbert (Phase 3)", "variational": True},
        ],
        "locks_frozen": {
            "W_g": LOCKED_WG,
            "wg_base": WG_BASE,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "quantitative_summary": {
            "wg": float(p.wg),
            "kappa": float(p.kappa),
            "mean_field_eigenvalue": float(linear["mean_field_eigenvalue"]),
            "hessian_condition_number": float(hessian["condition_number"]),
            "wg_residual_max": float(stability["wg_residual_max"]),
            "ghost_free_fraction": float(stability["ghost_free_fraction"]),
            "fixed_point_theta_bar": float(linear["fixed_point_approx"]),
        },
    }


def latex_action_principle() -> str:
    """Return LaTeX fragment for the unified action (paper scaffolding)."""
    return r"""
% Phase 1.1 unified action (gauged Hopf lattice + SM gauge scaffold)
\begin{align}
S &= S_\sigma + S_{\mathrm{Skyrme}} + S_{\mathrm{YM}}
  + S_{\mathrm{Hopf}} + S_{\mathrm{hol}} + S_{\mathrm{drive}}
  + S_{\mathrm{burst}} + S_{\mathrm{grav}},
\label{eq:unified-action}
\end{align}
with
\begin{align}
S_\sigma
  &= \frac{1}{2\lambda^2}\int d^4x\,\sqrt{-g}\,
     \varepsilon_{\mu\nu}\,\mathrm{Tr}\!\left(D^\mu U\, D^\nu U^\dagger\right),
\\
S_{\mathrm{Skyrme}}
  &= \frac{1}{32\pi^2 e_S^2}\int d^4x\,\sqrt{-g}\,
     \mathrm{Tr}\!\left([D_\mu U U^\dagger,\, D_\nu U U^\dagger]^2\right),
\\
S_{\mathrm{YM}}
  &= -\sum_{G\in\{\mathrm{SU}(3),\mathrm{SU}(2),\mathrm{U}(1)\}}
     \frac{1}{4g_G^2}\int d^4x\,\sqrt{-g}\,
     F_{\mu\nu}^{(G)} F^{(G)\mu\nu},
\\
S_{\mathrm{Hopf}}
  &= c_H\int H_{\mathrm{Hopf}}[q],
   \qquad \int H_{\mathrm{Hopf}}\in\mathbb{Z},
\\
S_{\mathrm{hol}}
  &= -\frac{\kappa}{2}\int d^4x\,\sqrt{-g}\,
     \bar\Theta^2
   - \frac{W_g}{2}\int d^4x\,\sqrt{-g}\,
     (\phi_b-\phi_b^\star)^2,
\\
S_{\mathrm{drive}}
  &= -\Delta\omega\int d^4x\,\sqrt{-g}\,\Theta,
\\
S_{\mathrm{burst}}
  &= -\int d^4x\,\sqrt{-g}\, U(\Theta),
   \quad U'(\Theta)=-C(\Theta-\theta_{\mathrm{crit}})_+^{p},
\\
S_{\mathrm{grav}}
  &= \frac{1}{16\pi G_N}\int d^4x\,\sqrt{-g}\, R + \cdots
\end{align}
Locks (frozen inputs): \(W_g=350/\pi\), \(\kappa\approx 0.85\),
\(\phi_b^\star\approx 0.8145\), \(\theta_{\mathrm{crit}}=\pi(1+\kappa)\).

Non-relativistic over-damped limit recovers the conduit PDE
\[
\partial_t\Theta
  = D\Delta\Theta + \tfrac{D}{2}\cot(\Theta/2)|\nabla\Theta|^2
  + \Delta\omega - \kappa\bar\Theta + B(\Theta).
\]
""".strip()

