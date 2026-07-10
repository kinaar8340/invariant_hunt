"""
Phase 2.2 — Topological Yukawa / mass-hierarchy ansatz.

Two coordinated pieces (locks frozen as inputs only):

1. **Mass hierarchy** (braiding-layer exponential):
   m_i^{(s)} = (v/√2) y_s exp(−β_s (2−i)^{p_s}) (1 + ε_s cos(φ_b* + ψ_s i))
   with i = 0,1,2 light→heavy, s ∈ {u,d,e}.

2. **CKM** (Wolfenstein, optional φ_b phase on η):
   λ, A, ρ̄, η̄ free; η_eff = η̄ cos(φ_b*) + η̄_sin sin(φ_b*) optional →
   use free η with mild φ_b modulation.

3. **Matrix form** (documentation / optional SVD path):
   Y_ij with braiding phases — used for unitary checks, not primary mass fit.

Gate SM-2 upgrade: structure + χ²(ln m) + χ²(|V|) vs PDG.
FAIL demotes the ansatz, not core locks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG, WG_BASE
from src.sm_mapping import check_locks_frozen, check_three_generations, gate_sm1_report

VEV_GEV: float = 246.2196

# PDG approximate charged-fermion masses [GeV]
PDG_MASSES_GEV: dict[str, float] = {
    "u": 2.16e-3,
    "c": 1.27,
    "t": 172.69,
    "d": 4.67e-3,
    "s": 93.4e-3,
    "b": 4.18,
    "e": 0.51099895e-3,
    "mu": 105.6583755e-3,
    "tau": 1.77686,
}

PDG_LOG_SIGMA: dict[str, float] = {
    "u": 0.30,
    "c": 0.12,
    "t": 0.04,
    "d": 0.30,
    "s": 0.15,
    "b": 0.06,
    "e": 0.02,
    "mu": 0.02,
    "tau": 0.02,
}

PDG_CKM: dict[str, float] = {
    "Vus": 0.2243,
    "Vcb": 0.0408,
    "Vub": 0.00382,
    "Vud": 0.97373,
    "Vcs": 0.9735,
    "Vtb": 0.9991,
}

PDG_CKM_SIGMA: dict[str, float] = {
    "Vus": 0.0008,
    "Vcb": 0.0014,
    "Vub": 0.00030,
    "Vud": 0.00031,
    "Vcs": 0.0016,
    "Vtb": 0.0002,
}

# Pre-registered thresholds
CHI2_MASS_PER_DOF_PASS: float = 9.0
CHI2_CKM_PER_DOF_PASS: float = 100.0
CHI2_MASS_PER_DOF_TIGHT: float = 1.0
CHI2_CKM_PER_DOF_TIGHT: float = 25.0


@dataclass
class YukawaAnsatzParams:
    """Free hierarchy + Wolfenstein params; locks are frozen inputs."""

    # Overall strength ~ heaviest gen Yukawa (dimensionless)
    # Defaults analytic from PDG ratios (ε=0); Optuna may refine with braiding mod.
    y_u: float = 0.991881
    y_d: float = 0.0240087
    y_e: float = 0.0102058
    # Hierarchy tilt: m_i ∝ exp(−β (2−i)^p), i=0 light
    beta_u: float = 4.9125
    beta_d: float = 3.8012
    beta_e: float = 2.8224
    p_u: float = 1.2004
    p_d: float = 0.8384
    p_e: float = 1.5306
    # Braiding modulation (0 = pure hierarchy; φ_b* enters when ε≠0)
    eps_u: float = 0.0
    eps_d: float = 0.0
    eps_e: float = 0.0
    psi_u: float = 0.0
    psi_d: float = 0.0
    psi_e: float = 0.0
    # Off-diagonal matrix (documentation path)
    alpha_u: float = 2.5
    alpha_d: float = 2.0
    alpha_e: float = 3.0
    xi_u: float = 1.0
    xi_d: float = 1.0
    xi_e: float = 0.5
    # Wolfenstein CKM (PDG-like)
    wolfenstein_lambda: float = 0.225
    wolfenstein_A: float = 0.811
    wolfenstein_rho: float = 0.124
    wolfenstein_eta: float = 0.356
    # Frozen locks (not optimized)
    phi_b: float = DEFAULT_BRAIDING
    kappa: float = DEFAULT_KAPPA
    wg: float = LOCKED_WG

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "YukawaAnsatzParams":
        known = set(cls.__dataclass_fields__.keys())
        return cls(**{k: float(v) for k, v in d.items() if k in known})

    def freeze_locks(self) -> "YukawaAnsatzParams":
        self.phi_b = DEFAULT_BRAIDING
        self.kappa = DEFAULT_KAPPA
        self.wg = LOCKED_WG
        return self


def hierarchical_masses(params: YukawaAnsatzParams, sector: str) -> np.ndarray:
    """Three masses light→heavy for sector u|d|e [GeV]."""
    sector = sector.lower()
    y = getattr(params, f"y_{sector}")
    beta = getattr(params, f"beta_{sector}")
    p = max(getattr(params, f"p_{sector}"), 0.3)
    eps = getattr(params, f"eps_{sector}")
    psi = getattr(params, f"psi_{sector}")
    phi = params.phi_b
    scale = VEV_GEV / math.sqrt(2.0)
    # Mild lock dressing (must not move locks)
    dress = 1.0 + 0.005 * (params.kappa - DEFAULT_KAPPA)
    dress *= 1.0 + 1e-5 * (params.wg - LOCKED_WG)

    masses = []
    for i in range(3):  # 0 light … 2 heavy
        gen_factor = math.exp(-beta * ((2 - i) ** p))
        mod = 1.0 + eps * math.cos(phi + psi * i)
        # keep masses positive
        mod = max(mod, 0.05)
        masses.append(scale * y * gen_factor * mod * dress)
    return np.array(masses, dtype=float)


def yukawa_matrix(params: YukawaAnsatzParams, sector: str) -> np.ndarray:
    """3×3 complex Yukawa (braiding phases) for documentation / unitarity."""
    sector = sector.lower()
    y = getattr(params, f"y_{sector}")
    beta = getattr(params, f"beta_{sector}")
    alpha = getattr(params, f"alpha_{sector}")
    xi = getattr(params, f"xi_{sector}")
    eps = getattr(params, f"eps_{sector}")
    psi = getattr(params, f"psi_{sector}")
    phi = params.phi_b
    Y = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            # Align diagonal with hierarchy: larger for large i,j
            gen_tilt = math.exp(-beta * (2 - 0.5 * (i + j)))
            off = math.exp(-alpha * abs(i - j))
            phase = np.exp(1j * xi * phi * (i - j))
            mod = 1.0 + eps * math.cos(phi + psi * (i + j))
            Y[i, j] = y * gen_tilt * off * phase * max(mod, 0.05)
    return Y


def mass_singular_values(Y: np.ndarray, vev: float = VEV_GEV) -> np.ndarray:
    _, sigma, _ = np.linalg.svd(Y)
    return np.sort(np.maximum(vev / math.sqrt(2.0) * np.real(sigma), 1e-30))


def left_mixing_matrix(Y: np.ndarray) -> np.ndarray:
    w = Y @ Y.conj().T
    evals, evecs = np.linalg.eigh(w)
    order = np.argsort(np.real(evals))
    return evecs[:, order]


def ckm_from_yukawas(Yu: np.ndarray, Yd: np.ndarray) -> np.ndarray:
    Uu = left_mixing_matrix(Yu)
    Ud = left_mixing_matrix(Yd)
    return Uu.conj().T @ Ud


def ckm_wolfenstein(params: YukawaAnsatzParams) -> np.ndarray:
    """CKM from Wolfenstein parameters with mild φ_b phase on complex phase."""
    lam = params.wolfenstein_lambda
    A = params.wolfenstein_A
    rho = params.wolfenstein_rho
    eta = params.wolfenstein_eta
    # Braiding phase rotates (ρ,η) slightly (topological dressing)
    c, s = math.cos(params.phi_b), math.sin(params.phi_b)
    rho_eff = rho * c - eta * s * 0.15
    eta_eff = eta * c + rho * s * 0.15

    V = np.zeros((3, 3), dtype=complex)
    V[0, 0] = 1 - 0.5 * lam**2
    V[0, 1] = lam
    V[0, 2] = A * lam**3 * (rho_eff - 1j * eta_eff)
    V[1, 0] = -lam
    V[1, 1] = 1 - 0.5 * lam**2
    V[1, 2] = A * lam**2
    V[2, 0] = A * lam**3 * (1 - rho_eff - 1j * eta_eff)
    V[2, 1] = -A * lam**2
    V[2, 2] = 1.0
    # Re-unitarize via polar-like projection (SVD)
    U, _, Vh = np.linalg.svd(V)
    return U @ Vh


def predict_spectrum(params: YukawaAnsatzParams) -> dict[str, Any]:
    """Primary: hierarchical masses + Wolfenstein CKM."""
    params = params.freeze_locks()
    mu = hierarchical_masses(params, "u")
    md = hierarchical_masses(params, "d")
    me = hierarchical_masses(params, "e")

    masses = {
        "u": float(mu[0]),
        "c": float(mu[1]),
        "t": float(mu[2]),
        "d": float(md[0]),
        "s": float(md[1]),
        "b": float(md[2]),
        "e": float(me[0]),
        "mu": float(me[1]),
        "tau": float(me[2]),
    }

    V = ckm_wolfenstein(params)
    Vabs = np.abs(V)
    ckm = {
        "Vud": float(Vabs[0, 0]),
        "Vus": float(Vabs[0, 1]),
        "Vub": float(Vabs[0, 2]),
        "Vcd": float(Vabs[1, 0]),
        "Vcs": float(Vabs[1, 1]),
        "Vcb": float(Vabs[1, 2]),
        "Vtd": float(Vabs[2, 0]),
        "Vts": float(Vabs[2, 1]),
        "Vtb": float(Vabs[2, 2]),
    }

    Yu = yukawa_matrix(params, "u")
    Yd = yukawa_matrix(params, "d")
    Ye = yukawa_matrix(params, "e")

    return {
        "masses_GeV": masses,
        "ckm_abs": ckm,
        "Yu": _mat_to_list(Yu),
        "Yd": _mat_to_list(Yd),
        "Ye": _mat_to_list(Ye),
        "params": params.to_dict(),
        "locks": {
            "W_g": params.wg,
            "kappa": params.kappa,
            "phi_b": params.phi_b,
            "wg_base": WG_BASE,
        },
        "mass_path": "hierarchical_braiding",
        "ckm_path": "wolfenstein_phi_b_dressing",
    }


def _mat_to_list(M: np.ndarray) -> list[list[list[float]]]:
    out = []
    for i in range(M.shape[0]):
        row = []
        for j in range(M.shape[1]):
            row.append([float(np.real(M[i, j])), float(np.imag(M[i, j]))])
        out.append(row)
    return out


def chi2_log_masses(pred: dict[str, float], pdg: dict[str, float] | None = None) -> dict[str, Any]:
    pdg = pdg or PDG_MASSES_GEV
    terms = {}
    total = 0.0
    n = 0
    for name, m_obs in pdg.items():
        m_pr = max(pred.get(name, 0.0), 1e-30)
        sig = PDG_LOG_SIGMA.get(name, 0.2)
        resid = (math.log(m_pr) - math.log(m_obs)) / sig
        c2 = resid**2
        terms[name] = {
            "m_pred": m_pr,
            "m_pdg": m_obs,
            "log_resid_over_sigma": resid,
            "chi2": c2,
        }
        total += c2
        n += 1
    return {
        "chi2": float(total),
        "n": n,
        "chi2_per_dof": float(total / max(n, 1)),
        "terms": terms,
    }


def chi2_ckm(pred: dict[str, float], keys: tuple[str, ...] | None = None) -> dict[str, Any]:
    keys = keys or ("Vus", "Vcb", "Vub", "Vud", "Vcs", "Vtb")
    terms = {}
    total = 0.0
    n = 0
    for k in keys:
        if k not in PDG_CKM:
            continue
        obs = PDG_CKM[k]
        sig = PDG_CKM_SIGMA.get(k, 0.01)
        pr = pred.get(k, 0.0)
        resid = (pr - obs) / sig
        c2 = resid**2
        terms[k] = {"pred": pr, "pdg": obs, "resid_over_sigma": resid, "chi2": c2}
        total += c2
        n += 1
    return {
        "chi2": float(total),
        "n": n,
        "chi2_per_dof": float(total / max(n, 1)),
        "terms": terms,
    }


def evaluate_yukawa(params: YukawaAnsatzParams | None = None) -> dict[str, Any]:
    p = (params or YukawaAnsatzParams()).freeze_locks()
    spec = predict_spectrum(p)
    c2m = chi2_log_masses(spec["masses_GeV"])
    c2c = chi2_ckm(spec["ckm_abs"])
    return {
        "schema": "invariant_hunt.sm_yukawa.v1",
        "spectrum": spec,
        "chi2_mass": c2m,
        "chi2_ckm": c2c,
        "chi2_total": float(c2m["chi2"] + c2c["chi2"]),
        "locks": check_locks_frozen(),
    }


def _params_from_trial(trial: Any) -> YukawaAnsatzParams:
    return YukawaAnsatzParams(
        y_u=trial.suggest_float("y_u", 0.3, 1.5, log=True),
        y_d=trial.suggest_float("y_d", 1e-3, 0.2, log=True),
        y_e=trial.suggest_float("y_e", 1e-4, 0.05, log=True),
        beta_u=trial.suggest_float("beta_u", 2.0, 10.0),
        beta_d=trial.suggest_float("beta_d", 1.0, 8.0),
        beta_e=trial.suggest_float("beta_e", 2.0, 10.0),
        p_u=trial.suggest_float("p_u", 0.5, 2.0),
        p_d=trial.suggest_float("p_d", 0.5, 2.0),
        p_e=trial.suggest_float("p_e", 0.5, 2.0),
        eps_u=trial.suggest_float("eps_u", 0.0, 0.25),
        eps_d=trial.suggest_float("eps_d", 0.0, 0.25),
        eps_e=trial.suggest_float("eps_e", 0.0, 0.2),
        psi_u=trial.suggest_float("psi_u", -math.pi, math.pi),
        psi_d=trial.suggest_float("psi_d", -math.pi, math.pi),
        psi_e=trial.suggest_float("psi_e", -math.pi, math.pi),
        alpha_u=trial.suggest_float("alpha_u", 0.5, 6.0),
        alpha_d=trial.suggest_float("alpha_d", 0.5, 6.0),
        alpha_e=trial.suggest_float("alpha_e", 0.5, 6.0),
        xi_u=trial.suggest_float("xi_u", -2.0, 2.0),
        xi_d=trial.suggest_float("xi_d", -2.0, 2.0),
        xi_e=trial.suggest_float("xi_e", -2.0, 2.0),
        wolfenstein_lambda=trial.suggest_float("wolfenstein_lambda", 0.20, 0.26),
        wolfenstein_A=trial.suggest_float("wolfenstein_A", 0.6, 1.1),
        wolfenstein_rho=trial.suggest_float("wolfenstein_rho", 0.05, 0.35),
        wolfenstein_eta=trial.suggest_float("wolfenstein_eta", 0.20, 0.50),
        phi_b=DEFAULT_BRAIDING,
        kappa=DEFAULT_KAPPA,
        wg=LOCKED_WG,
    )


def optimize_yukawa(
    *,
    n_trials: int = 64,
    seed: int = 42,
    method: str = "optuna",
) -> dict[str, Any]:
    """Optimize free hierarchy + Wolfenstein params (locks fixed)."""
    rng = np.random.default_rng(seed)

    def loss_of(p: YukawaAnsatzParams) -> float:
        return float(evaluate_yukawa(p)["chi2_total"])

    best_p = YukawaAnsatzParams().freeze_locks()
    best_loss = loss_of(best_p)
    history: list[float] = [best_loss]
    method_used = method

    if method == "optuna":
        try:
            import optuna

            optuna.logging.set_verbosity(optuna.logging.WARNING)

            def objective(trial: "optuna.Trial") -> float:
                return loss_of(_params_from_trial(trial))

            study = optuna.create_study(
                direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed)
            )
            # Seed with default hierarchical + Wolfenstein (must not regress)
            study.enqueue_trial(
                {
                    "y_u": best_p.y_u,
                    "y_d": best_p.y_d,
                    "y_e": best_p.y_e,
                    "beta_u": best_p.beta_u,
                    "beta_d": best_p.beta_d,
                    "beta_e": best_p.beta_e,
                    "p_u": best_p.p_u,
                    "p_d": best_p.p_d,
                    "p_e": best_p.p_e,
                    "eps_u": best_p.eps_u,
                    "eps_d": best_p.eps_d,
                    "eps_e": best_p.eps_e,
                    "psi_u": best_p.psi_u,
                    "psi_d": best_p.psi_d,
                    "psi_e": best_p.psi_e,
                    "alpha_u": best_p.alpha_u,
                    "alpha_d": best_p.alpha_d,
                    "alpha_e": best_p.alpha_e,
                    "xi_u": best_p.xi_u,
                    "xi_d": best_p.xi_d,
                    "xi_e": best_p.xi_e,
                    "wolfenstein_lambda": best_p.wolfenstein_lambda,
                    "wolfenstein_A": best_p.wolfenstein_A,
                    "wolfenstein_rho": best_p.wolfenstein_rho,
                    "wolfenstein_eta": best_p.wolfenstein_eta,
                }
            )
            study.optimize(objective, n_trials=n_trials)
            cand = YukawaAnsatzParams(
                **{k: float(v) for k, v in study.best_params.items()},
                phi_b=DEFAULT_BRAIDING,
                kappa=DEFAULT_KAPPA,
                wg=LOCKED_WG,
            )
            cand_loss = float(study.best_value)
            if cand_loss <= best_loss:
                best_p = cand
                best_loss = cand_loss
            history = [float(t.value) for t in study.trials if t.value is not None]
            method_used = "optuna"
        except Exception:
            method_used = "random"

    if method_used == "random" or method == "random":
        method_used = "random"
        for _ in range(n_trials):
            p = YukawaAnsatzParams(
                y_u=float(np.exp(rng.uniform(math.log(0.3), math.log(1.5)))),
                y_d=float(np.exp(rng.uniform(math.log(1e-3), math.log(0.2)))),
                y_e=float(np.exp(rng.uniform(math.log(1e-4), math.log(0.05)))),
                beta_u=float(rng.uniform(2.0, 10.0)),
                beta_d=float(rng.uniform(1.0, 8.0)),
                beta_e=float(rng.uniform(2.0, 10.0)),
                p_u=float(rng.uniform(0.5, 2.0)),
                p_d=float(rng.uniform(0.5, 2.0)),
                p_e=float(rng.uniform(0.5, 2.0)),
                eps_u=float(rng.uniform(0.0, 0.25)),
                eps_d=float(rng.uniform(0.0, 0.25)),
                eps_e=float(rng.uniform(0.0, 0.2)),
                psi_u=float(rng.uniform(-math.pi, math.pi)),
                psi_d=float(rng.uniform(-math.pi, math.pi)),
                psi_e=float(rng.uniform(-math.pi, math.pi)),
                wolfenstein_lambda=float(rng.uniform(0.20, 0.26)),
                wolfenstein_A=float(rng.uniform(0.6, 1.1)),
                wolfenstein_rho=float(rng.uniform(0.05, 0.35)),
                wolfenstein_eta=float(rng.uniform(0.20, 0.50)),
            ).freeze_locks()
            L = loss_of(p)
            history.append(L)
            if L < best_loss:
                best_loss = L
                best_p = p

    ev = evaluate_yukawa(best_p)
    return {
        "schema": "invariant_hunt.sm_yukawa_optimize.v1",
        "method": method_used,
        "n_trials": n_trials,
        "seed": seed,
        "best_loss": best_loss,
        "best_params": best_p.to_dict(),
        "evaluation": ev,
        "history_tail": history[-20:],
        "history_min": float(min(history)) if history else None,
    }


def gate_sm2_mass_report(
    *,
    n_trials: int = 64,
    seed: int = 42,
    optimize: bool = True,
    params: YukawaAnsatzParams | None = None,
) -> dict[str, Any]:
    """Gate SM-2 upgrade: structure + mass/mixing χ² vs PDG."""
    structure = check_three_generations()
    sm1 = gate_sm1_report()

    if optimize:
        opt = optimize_yukawa(n_trials=n_trials, seed=seed)
        ev = opt["evaluation"]
        best_params = opt["best_params"]
        opt_meta = {
            "method": opt["method"],
            "n_trials": opt["n_trials"],
            "best_loss": opt["best_loss"],
        }
    else:
        ev = evaluate_yukawa(params or YukawaAnsatzParams())
        best_params = ev["spectrum"]["params"]
        opt_meta = {"method": "fixed", "n_trials": 0, "best_loss": ev["chi2_total"]}

    c2m = ev["chi2_mass"]["chi2_per_dof"]
    c2c = ev["chi2_ckm"]["chi2_per_dof"]
    mass_pass = c2m <= CHI2_MASS_PER_DOF_PASS
    ckm_pass = c2c <= CHI2_CKM_PER_DOF_PASS
    mass_tight = c2m <= CHI2_MASS_PER_DOF_TIGHT
    ckm_tight = c2c <= CHI2_CKM_PER_DOF_TIGHT
    locks = check_locks_frozen()

    criteria = {
        "structure": structure["pass"],
        "sm1_still_pass": sm1["pass"],
        "locks_frozen": locks["pass"],
        "mass_chi2_per_dof": mass_pass,
        "ckm_chi2_per_dof": ckm_pass,
    }
    full_pass = all(criteria.values())
    grade = (
        "TIGHT"
        if full_pass and mass_tight and ckm_tight
        else ("LOOSE" if full_pass else "FAIL")
    )

    return {
        "schema": "invariant_hunt.gate_sm2.v1",
        "phase": "2.2",
        "gate": "SM-2",
        "pass": full_pass,
        "grade": grade,
        "criteria": criteria,
        "thresholds": {
            "chi2_mass_per_dof_pass": CHI2_MASS_PER_DOF_PASS,
            "chi2_ckm_per_dof_pass": CHI2_CKM_PER_DOF_PASS,
            "chi2_mass_per_dof_tight": CHI2_MASS_PER_DOF_TIGHT,
            "chi2_ckm_per_dof_tight": CHI2_CKM_PER_DOF_TIGHT,
        },
        "chi2_mass": ev["chi2_mass"],
        "chi2_ckm": ev["chi2_ckm"],
        "chi2_total": ev["chi2_total"],
        "spectrum": {
            "masses_GeV": ev["spectrum"]["masses_GeV"],
            "ckm_abs": ev["spectrum"]["ckm_abs"],
            "pdg_masses_GeV": PDG_MASSES_GEV,
            "pdg_ckm": PDG_CKM,
            "mass_path": ev["spectrum"].get("mass_path"),
            "ckm_path": ev["spectrum"].get("ckm_path"),
        },
        "best_params": best_params,
        "optimize": opt_meta,
        "structure": structure,
        "locks": locks,
        "yukawa_optimized": bool(optimize),
        "note": (
            "Hierarchical braiding masses + Wolfenstein CKM with φ_b dressing. "
            "FAIL demotes this ansatz (not core locks)."
        ),
        "discipline": {
            "locks_not_fitted": True,
            "no_gravity_claim": True,
            "premerger_freeze_untouched": True,
        },
    }


def yukawa_loss_for_meta(params_dict: dict[str, float] | None = None) -> dict[str, Any]:
    if params_dict:
        p = YukawaAnsatzParams.from_dict(params_dict).freeze_locks()
    else:
        p = YukawaAnsatzParams().freeze_locks()
    ev = evaluate_yukawa(p)
    structure = check_three_generations()
    sm1 = gate_sm1_report()
    loss = float(ev["chi2_total"])
    if not structure["pass"]:
        loss += 1e3
    if not sm1["pass"]:
        loss += 1e3
    return {
        "loss": loss,
        "chi2_total": ev["chi2_total"],
        "chi2_mass_per_dof": ev["chi2_mass"]["chi2_per_dof"],
        "chi2_ckm_per_dof": ev["chi2_ckm"]["chi2_per_dof"],
        "sm1_pass": sm1["pass"],
        "sm2_structure_pass": structure["pass"],
        "locks": check_locks_frozen(),
        "discovered_Wg": LOCKED_WG,
        "mode": "sm_yukawa",
        "dry_run": True,
    }
