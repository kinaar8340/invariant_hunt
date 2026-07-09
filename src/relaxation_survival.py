"""
relaxation_survival.py
======================
Normalize simulation time / accumulated twist to dimensionless λt = 2.

In any memoryless constant-rate exponential decay process,

    f(t) = f₀ · exp(−λt),

the universal survival fraction at λt = 2 is exp(−2) ≈ 0.135335.  This module
maps the gauged Hopf / twist-PDE dynamics onto that normalization:

  • PDE mean-field gauge term −κ θ̄  ⇒  effective λ ≈ κ
  • Conduit global pointer damping κ  ⇒  same rate identification
  • Normalized horizon:  t_norm = λt_target / κ ,  n_steps = t_norm / dt

After evolving to λt = 2, measured residuals (mean twist, fluctuation energy,
braiding phase, identity survival) are compared to:

  • e^{−2}  — exponential survival analog
  • R = φ² + e² − π²  — φ-e-π Pythagorean residual (mystery repo)
  • 137.5°/1000 ≈ 0.1375  — golden-angle packing analog
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
E = math.e
PI = math.pi

# Mystery residual and interpretive analogs
R_RESIDUAL = PHI**2 + E**2 - PI**2
E_INV2 = math.exp(-2.0)
GOLDEN_ANGLE_DEG = 360.0 * (1.0 - 1.0 / PHI)  # ≈ 137.5078°
GOLDEN_ANGLE_FRACTION = GOLDEN_ANGLE_DEG / 1000.0  # ≈ 0.1375
PHI_INV2 = 1.0 / PHI**2  # ≈ 0.381966 — related golden packing scale


@dataclass
class SurvivalAnalogs:
    """Reference values for comparison tables."""

    r_residual: float = R_RESIDUAL
    e_inv2: float = E_INV2
    golden_angle_fraction: float = GOLDEN_ANGLE_FRACTION
    phi_inv2: float = PHI_INV2


@dataclass
class LambdaTNormalization:
    """Parameters for λt = 2 normalization."""

    lambda_t_target: float = 2.0
    kappa: float = 0.85
    dt: float = 0.001
    characteristic_rate: float = field(init=False)
    t_physical: float = field(init=False)
    n_steps: int = field(init=False)

    def __post_init__(self) -> None:
        # Mean-field reduction: gauge restoring torque −κθ̄ ⇒ λ ≈ κ
        self.characteristic_rate = self.kappa
        self.t_physical = self.lambda_t_target / self.characteristic_rate
        self.n_steps = max(1, int(round(self.t_physical / self.dt)))


def steps_for_lambda_t(
    lambda_t_target: float = 2.0,
    kappa: float = 0.85,
    dt: float = 0.001,
) -> int:
    """Discrete steps to reach λt = lambda_t_target with λ ≈ κ."""
    return LambdaTNormalization(lambda_t_target=lambda_t_target, kappa=kappa, dt=dt).n_steps


def compare_to_analogs(
    measured: float,
    label: str = "survival",
    analogs: SurvivalAnalogs | None = None,
) -> dict[str, Any]:
    """Rank measured value against R, e^{−2}, and golden-angle fraction."""
    ref = analogs or SurvivalAnalogs()
    candidates = {
        "R_phi_e_pi": ref.r_residual,
        "e_inv2": ref.e_inv2,
        "golden_angle_over_1000": ref.golden_angle_fraction,
        "phi_inv2": ref.phi_inv2,
    }
    deltas = {name: abs(measured - val) for name, val in candidates.items()}
    best_name = min(deltas, key=deltas.get)
    best_val = candidates[best_name]

    # Hybrid: 60% golden-angle packing + 40% e^{-2} dissipative survival
    golden_delta_pct = (
        100.0 * abs(measured - ref.golden_angle_fraction) / abs(ref.golden_angle_fraction)
    )
    e_inv2_delta_pct = 100.0 * abs(measured - ref.e_inv2) / abs(ref.e_inv2)
    hybrid_delta_pct = 0.6 * golden_delta_pct + 0.4 * e_inv2_delta_pct
    golden_closeness = 1.0 / (1.0 + abs(measured - ref.golden_angle_fraction))
    e_inv2_closeness = 1.0 / (1.0 + abs(measured - ref.e_inv2))
    hybrid_score = 0.6 * golden_closeness + 0.4 * e_inv2_closeness

    return {
        "label": label,
        "measured": measured,
        "candidates": candidates,
        "best_match": best_name,
        "best_value": best_val,
        "delta_abs": deltas[best_name],
        "delta_pct_vs_best": 100.0 * deltas[best_name] / abs(best_val) if best_val else 0.0,
        "delta_pct_vs_R": 100.0 * abs(measured - ref.r_residual) / abs(ref.r_residual),
        "delta_pct_vs_e_inv2": e_inv2_delta_pct,
        "delta_pct_vs_golden": golden_delta_pct,
        "hybrid_delta_pct": hybrid_delta_pct,
        "hybrid_score": hybrid_score,
    }


def simulate_twist_pde_survival(
    nx: int = 20,
    nt: int | None = None,
    dt: float = 0.001,
    D: float = 0.05,
    kappa: float = 0.85,
    delta_omega: float = 0.002,
    theta_crit: float | None = None,
    seed: int = 42,
    normalize_to_lambda_t: float | None = 2.0,
    track_interval: int = 50,
) -> dict[str, Any]:
    """
    Run twist-PDE relaxation, optionally stopping at λt = normalize_to_lambda_t.

    Returns survival fractions and analog comparison at the normalized horizon.
    """
    if theta_crit is None:
        theta_crit = PI * (1.0 + kappa)

    norm: LambdaTNormalization | None = None
    if normalize_to_lambda_t is not None:
        norm = LambdaTNormalization(
            lambda_t_target=normalize_to_lambda_t,
            kappa=kappa,
            dt=dt,
        )
        nt = norm.n_steps

    rng = np.random.default_rng(seed)
    theta = rng.uniform(0.1, 2.0, (nx, nx, nx))

    theta0_mean = float(theta.mean())
    theta0_std = float(theta.std())
    theta0_fluct = float(np.sqrt(np.mean((theta - theta0_mean) ** 2)))

    mean_history: list[float] = []
    std_history: list[float] = []
    fluct_history: list[float] = []

    for step in range(nt):
        lap = (
            np.roll(theta, 1, 0)
            + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1)
            + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2)
            + np.roll(theta, -1, 2)
            - 6 * theta
        ) / (1.0 / nx) ** 2

        with np.errstate(divide="ignore", invalid="ignore"):
            cot_term = (
                (D / 2.0)
                * np.cos(theta / 2.0)
                / np.maximum(np.sin(theta / 2.0), 1e-8)
                * (
                    np.gradient(theta, axis=0) ** 2
                    + np.gradient(theta, axis=1) ** 2
                    + np.gradient(theta, axis=2) ** 2
                ).sum(axis=0)
            )

        bar_theta = float(theta.mean())
        gauge = -kappa * bar_theta
        burst = np.where(theta > theta_crit, -50.0 * (theta - theta_crit), 0.0)
        theta += dt * (D * lap + cot_term + delta_omega + gauge + burst)
        theta = np.clip(theta, 0.01, 2 * PI - 0.01)

        if step % track_interval == 0 or step == nt - 1:
            mean_history.append(bar_theta)
            std_history.append(float(theta.std()))
            fluct_history.append(float(np.sqrt(np.mean((theta - bar_theta) ** 2))))

    final_mean = float(theta.mean())
    final_std = float(theta.std())
    final_fluct = float(np.sqrt(np.mean((theta - final_mean) ** 2)))

    def safe_ratio(num: float, denom: float) -> float:
        return float(num / denom) if abs(denom) > 1e-12 else 0.0

    survival = {
        "mean_survival": safe_ratio(final_mean, theta0_mean),
        "std_survival": safe_ratio(final_std, theta0_std),
        "fluctuation_survival": safe_ratio(final_fluct, theta0_fluct),
        "theoretical_e_inv2": E_INV2,
        "theta0_mean": theta0_mean,
        "final_mean": final_mean,
        "final_std": final_std,
    }

    comparisons = {
        "mean_survival": compare_to_analogs(survival["mean_survival"], "mean_survival"),
        "std_survival": compare_to_analogs(survival["std_survival"], "std_survival"),
        "fluctuation_survival": compare_to_analogs(
            survival["fluctuation_survival"], "fluctuation_survival"
        ),
    }

    return {
        "normalization": (
            {
                "lambda_t_target": norm.lambda_t_target,
                "kappa": norm.kappa,
                "dt": norm.dt,
                "characteristic_rate": norm.characteristic_rate,
                "t_physical": norm.t_physical,
                "n_steps": norm.n_steps,
                "note": "λ ≈ κ from mean-field gauge −κθ̄; survival at λt=2 should track e^{−2}",
            }
            if norm
            else None
        ),
        "pde_params": {
            "nx": nx,
            "nt": nt,
            "dt": dt,
            "D": D,
            "kappa": kappa,
            "delta_omega": delta_omega,
            "theta_crit": theta_crit,
            "seed": seed,
        },
        "survival": survival,
        "analog_comparisons": comparisons,
        "mean_history": mean_history,
        "std_history": std_history,
    }


def evolve_gauged_twist_survival(
    n_steps: int,
    kappa: float = 0.85,
    gauge_strength: float = 0.88,
    omega_L: float = 0.025,
    omega_R: float = 0.0225,
    n_identities: int = 96,
    seed: int = 42,
    normalize_to_lambda_t: float | None = None,
    dt: float = 1.0,
) -> dict[str, Any]:
    """
    Lightweight two-gyro gauged twist evolution (numpy) for survival probes.

    Identity survival = mean cosine similarity to initial random orientations
    after gauge-restoring steps — the discrete analog of exp(−λt) persistence.
    """
    if normalize_to_lambda_t is not None:
        n_steps = steps_for_lambda_t(normalize_to_lambda_t, kappa, dt)

    rng = np.random.default_rng(seed)

    def _normalize(q: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(q)
        return q / n if n > 1e-8 else q

    def _small_rotor(theta: float) -> np.ndarray:
        half = theta / 2.0
        return np.array([np.cos(half), 0.0, 0.0, np.sin(half)])

    def _q_mult(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return np.array(
            [
                w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            ]
        )

    def _q_conj(q: np.ndarray) -> np.ndarray:
        return np.array([q[0], -q[1], -q[2], -q[3]])

    current_q = np.array([1.0, 0.0, 0.0, 0.0])
    twist_history = np.array([0.0])
    identities = np.array([_normalize(rng.standard_normal(4)) for _ in range(n_identities)])
    initial_identities = identities.copy()

    identity_survival_trace: list[float] = []
    pointer_trace: list[float] = []
    burst_count = 0
    theta_crit = PI * (1.0 + kappa)

    initial_twist = None
    for _ in range(n_steps):
        delta_L = _small_rotor(omega_L)
        delta_R = _small_rotor(omega_R)
        current_q = _normalize(_q_mult(_q_mult(delta_L, current_q), _q_conj(delta_R)))

        avg_imbalance = float(np.mean(twist_history) % (2 * PI))
        # Gauge torque: strength × imbalance, scaled by κ (pointer damping)
        gauge_alpha = -gauge_strength * avg_imbalance - kappa * avg_imbalance * 0.1
        gauge_rot = np.array([np.cos(gauge_alpha), 0.0, 0.0, np.sin(gauge_alpha)])
        current_q = _normalize(_q_mult(current_q, gauge_rot))

        # Propagate gauge rotation into identity orientations (memory decay across lattice)
        for i in range(n_identities):
            identities[i] = _normalize(_q_mult(gauge_rot, identities[i]))

        twist = 2.0 * np.arccos(np.clip(current_q[0], -1.0, 1.0))
        twist_history = np.append(twist_history, twist)
        if initial_twist is None and twist > 1e-6:
            initial_twist = twist

        cosines = np.sum(identities * initial_identities, axis=1)
        identity_survival_trace.append(float(np.mean(np.abs(cosines))))
        pointer_trace.append(float(np.tanh(gauge_alpha * 6.0)))

        if twist > theta_crit:
            burst_count += 1

    final_identity_survival = identity_survival_trace[-1] if identity_survival_trace else 1.0
    # Residual = 1 − survival (what remains "un-relaxed" as a positive fraction)
    identity_residual = 1.0 - final_identity_survival

    twist_survival = 1.0
    if initial_twist and initial_twist > 1e-8:
        twist_survival = float(twist_history[-1] / initial_twist)

    return {
        "n_steps": n_steps,
        "kappa": kappa,
        "gauge_strength": gauge_strength,
        "omega_L": omega_L,
        "omega_R": omega_R,
        "normalize_to_lambda_t": normalize_to_lambda_t,
        "lambda_t_achieved": kappa * n_steps * dt,
        "final_twist": float(twist_history[-1]),
        "twist_variance": float(np.var(twist_history)),
        "burst_count": burst_count,
        "identity_survival": final_identity_survival,
        "identity_residual": identity_residual,
        "twist_survival": twist_survival,
        "pointer_final": pointer_trace[-1] if pointer_trace else 0.0,
        "analog_comparison_residual": compare_to_analogs(identity_residual, "identity_residual"),
        "analog_comparison_survival": compare_to_analogs(
            final_identity_survival, "identity_survival"
        ),
        "analog_comparison_twist_survival": compare_to_analogs(
            twist_survival, "twist_survival"
        ),
        "identity_survival_trace": identity_survival_trace[:: max(1, n_steps // 20)],
    }