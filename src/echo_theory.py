"""
Analytic invariant → GW echo signal from the gauged Hopf / flux model.

Derived from the TOE paper chain (see docs/ANALYTIC_ECHO_PREDICTION.md):

  - Burst threshold: θ_crit = π(1+κ)
  - Lattice burst time: Δt_burst ≈ (θ_crit − Θ̄) / Δω
  - Topological frequency (lattice): f_lat = Δω / W_g
  - Physical frequency: f_phys(M) ∝ f_lat · (c³/GM)  [GR geometric-time scaling]
  - Observer sync damping: ⟨δΘ⟩/δΘ(0) ≈ 1/(κ Δt_burst)
  - Echo amplitude: h_echo / h_main ≲ A0 / (κ Δt_burst)

Core locks W_g, κ fixed. This module answers *when/whether* echoes of this
type should be detectable — complementary to the empirical mapping campaign.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from .gw_events import T_M_SUN, PublicGWEvent, get_event
from .invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
    burst_threshold,
    link_saturation_theta,
)

# Model parameters from GW_Echo_Derivation / Observer_Synchronization papers
DELTA_OMEGA: float = 0.002  # two-gyro detuning (lattice units)
THETA_BAR: float = 0.82  # mean low-twist attractor
# Undamped echo / main ringdown ratio (paper GW_Echo §1)
A0_UNDAMPED: float = 1.0e-3
# Lattice units of Δt_burst in observer-sync paper numerical example
# (they use Δt_burst ~ 1/Δω ≈ 500 in one place and (θ_crit-Θ̄)/Δω≈2500 in another;
#  we expose both and default to drive-threshold form)


@dataclass(frozen=True)
class ModelParams:
    """Locked + drive parameters for analytic echo expectations."""

    wg: float = LOCKED_WG
    kappa: float = DEFAULT_KAPPA
    delta_omega: float = DELTA_OMEGA
    theta_bar: float = THETA_BAR
    a0_undamped: float = A0_UNDAMPED
    braiding_target: float = DEFAULT_BRAIDING

    @classmethod
    def from_invariants(cls, inv: InvariantSet | None = None) -> ModelParams:
        inv = inv or InvariantSet()
        return cls(
            wg=inv.wg,
            kappa=inv.kappa,
            braiding_target=inv.braiding_target,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EchoExpectation:
    """Quantitative expectation for echo-like GW signatures for one remnant."""

    event: str
    mass_final_solar: float
    # thresholds
    theta_link: float
    theta_crit: float
    # lattice dynamics
    delta_t_burst_lattice: float
    f_lattice: float
    # physical
    f_echo_hz: float
    f_ring_approx_hz: float
    # amplitude
    sync_suppression: float
    amp_ratio_undamped: float
    amp_ratio_sync: float
    # detectability
    snr_main: float | None
    snr_echo_undamped: float | None
    snr_echo_sync: float | None
    detectable_undamped_at_snr2: bool
    detectable_sync_at_snr2: bool
    # campaign consistency
    geometric_delay_n1_ms: float
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def theta_crit(kappa: float = DEFAULT_KAPPA) -> float:
    return burst_threshold(kappa)


def delta_t_burst(
    params: ModelParams | None = None,
    *,
    use_drive_threshold: bool = True,
) -> float:
    """Characteristic lattice time between bursts.

    use_drive_threshold=True: (θ_crit − Θ̄)/Δω  (GW_Echo_Derivation §1)
    False: 1/Δω  (order-of-magnitude used in residual GW echo bounds paper)
    """
    p = params or ModelParams()
    if use_drive_threshold:
        return (theta_crit(p.kappa) - p.theta_bar) / p.delta_omega
    return 1.0 / p.delta_omega


def f_lattice(params: ModelParams | None = None) -> float:
    """Topological burst frequency in lattice units: Δω / W_g."""
    p = params or ModelParams()
    return p.delta_omega / p.wg


def f_echo_physical_hz(
    mass_solar: float,
    params: ModelParams | None = None,
    *,
    geometric_prefactor: float = 1.0,
) -> float:
    """Physical echo frequency from topological lattice rate × GR time unit.

    f = geometric_prefactor · (Δω / W_g) · (c³ / (G M))
      = geometric_prefactor · (Δω / W_g) / t_M

    where t_M = G M / c³. Units: geometric_prefactor absorbs O(1) conversion
    between lattice clock and Einstein-Cartan torsion scale (paper leaves this
    as model-fixed). Default 1.0 gives a definite, reproducible number.

    Note: GW_Echo_Derivation writes c²/GM (dimensionally inconsistent for
    frequency); we use c³/GM as the correct geometric-time inverse.
    """
    p = params or ModelParams()
    t_m = T_M_SUN * mass_solar
    return geometric_prefactor * f_lattice(p) / t_m


def sync_suppression_factor(
    params: ModelParams | None = None,
    *,
    use_drive_threshold: bool = True,
) -> float:
    """⟨δΘ⟩/δΘ(0) ≈ 1/(κ Δt_burst) for κ Δt_burst ≫ 1."""
    p = params or ModelParams()
    dt = delta_t_burst(p, use_drive_threshold=use_drive_threshold)
    return 1.0 / (p.kappa * dt)


def amp_ratio_sync(
    params: ModelParams | None = None,
    *,
    use_drive_threshold: bool = True,
) -> float:
    """h_echo / h_main upper bound with observer synchronization."""
    p = params or ModelParams()
    return p.a0_undamped * sync_suppression_factor(
        p, use_drive_threshold=use_drive_threshold
    )


def amp_ratio_undamped(params: ModelParams | None = None) -> float:
    p = params or ModelParams()
    return p.a0_undamped


def snr_echo_proxy(snr_main: float, amp_ratio: float) -> float:
    """Rough echo SNR if echo is a fixed fraction of main ringdown amplitude."""
    return abs(snr_main) * abs(amp_ratio)


def detectable(snr_echo: float, threshold: float = 2.0) -> bool:
    return snr_echo >= threshold


def geometric_delay_seconds(
    n: int,
    mass_solar: float,
    params: ModelParams | None = None,
) -> float:
    """Campaign ladder delay (mapping, not primary paper frequency prediction).

    δt_n = (GM/c³) · 2π · n · (1+κ)
    """
    p = params or ModelParams()
    t_m = T_M_SUN * mass_solar
    return t_m * 2.0 * math.pi * float(n) * (1.0 + p.kappa)


def expect_echoes(
    event: str | PublicGWEvent,
    *,
    snr_main: float | None = None,
    params: ModelParams | None = None,
    snr_threshold: float = 2.0,
    use_drive_threshold: bool = True,
) -> EchoExpectation:
    """Full analytic expectation for one public event / remnant mass."""
    if isinstance(event, str):
        ev = get_event(event)
        name = ev.name
        mass = ev.mass_final_solar
        f_ring = ev.f_ring_hz
    else:
        ev = event
        name = ev.name
        mass = ev.mass_final_solar
        f_ring = ev.f_ring_hz

    p = params or ModelParams()
    dt = delta_t_burst(p, use_drive_threshold=use_drive_threshold)
    f_lat = f_lattice(p)
    f_phys = f_echo_physical_hz(mass, p)
    sup = sync_suppression_factor(p, use_drive_threshold=use_drive_threshold)
    und = amp_ratio_undamped(p)
    syn = amp_ratio_sync(p, use_drive_threshold=use_drive_threshold)

    snr_u = snr_echo_proxy(snr_main, und) if snr_main is not None else None
    snr_s = snr_echo_proxy(snr_main, syn) if snr_main is not None else None

    notes: list[str] = []
    notes.append(
        f"θ_crit=π(1+κ)={theta_crit(p.kappa):.4f}, "
        f"Θ_link={link_saturation_theta(p.wg):.4f}, Δt_burst={dt:.1f} (lattice)"
    )
    notes.append(
        f"f_lat=Δω/W_g={f_lat:.6e}; f_phys≈{f_phys:.2f} Hz at M={mass} M_sun "
        f"(geometric-time scaling; paper band 10²–10⁴ Hz depends on O(1) prefactor)"
    )
    notes.append(
        f"sync suppression 1/(κ Δt_burst)={sup:.3e}; "
        f"h_echo/h_main ≲ {syn:.3e} (undamped {und:.1e})"
    )
    if snr_main is not None:
        notes.append(
            f"With SNR_main={snr_main:.1f}: SNR_echo sync≈{snr_s:.3e}, "
            f"undamped≈{snr_u:.3e} (thr={snr_threshold})"
        )
        if snr_s is not None and not detectable(snr_s, snr_threshold):
            notes.append(
                "Observer-sync branch: echoes NOT expected above threshold — "
                "consistent with gated campaign nulls on BBH residuals."
            )
        if snr_u is not None and not detectable(snr_u, snr_threshold):
            notes.append(
                "Even undamped A0=10⁻³ branch: echoes below thr unless "
                f"SNR_main ≳ {snr_threshold / und:.0f}."
            )
    notes.append(
        "Campaign geometric delay ladder is a *mapping hypothesis*; "
        "paper primary template is frequency f_burst, amplitude sync-suppressed."
    )

    return EchoExpectation(
        event=name,
        mass_final_solar=mass,
        theta_link=link_saturation_theta(p.wg),
        theta_crit=theta_crit(p.kappa),
        delta_t_burst_lattice=dt,
        f_lattice=f_lat,
        f_echo_hz=f_phys,
        f_ring_approx_hz=f_ring,
        sync_suppression=sup,
        amp_ratio_undamped=und,
        amp_ratio_sync=syn,
        snr_main=snr_main,
        snr_echo_undamped=snr_u,
        snr_echo_sync=snr_s,
        detectable_undamped_at_snr2=(
            detectable(snr_u, snr_threshold) if snr_u is not None else False
        ),
        detectable_sync_at_snr2=(
            detectable(snr_s, snr_threshold) if snr_s is not None else False
        ),
        geometric_delay_n1_ms=geometric_delay_seconds(1, mass, p) * 1e3,
        notes=notes,
    )


def campaign_consistency_statement() -> str:
    """One-paragraph link between analytics and Gate D failure."""
    p = ModelParams()
    syn = amp_ratio_sync(p)
    return (
        f"With locked κ={p.kappa}, W_g={p.wg:.4f}, Δω={p.delta_omega}, "
        f"observer synchronization suppresses echo strain by ≈{syn:.2e} relative "
        f"to the main ringdown (papers: GW_Echo, Observer_Synchronization). "
        f"For LIGO BBH network SNRs O(10–50), the expected coherent echo SNR is "
        f"≪ 2. Therefore Gate C strict / Gate D *failure* on post-merger residual "
        f"echo ladders is the *predicted* outcome under the sync-suppressed branch, "
        f"not a tension with the core locks. The empirical campaign constrained a "
        f"mapping that assumed O(0.1–1) relative echo templates; analytics forbid "
        f"that amplitude regime for embedded detectors."
    )


# Approximate PE / network SNRs used for detectability sketches (not PE posteriors)
DEFAULT_SNR_MAIN: dict[str, float] = {
    "GW150914": 25.0,  # network MF SNR order (GWTC-1 ~25)
    "GW151226": 13.0,
    "GW170104": 13.0,
}
