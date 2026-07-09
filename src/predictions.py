"""
Map locked invariants → concrete, falsifiable observables.

Pipeline stage: InvariantSet / PositionalPhase → PredictionRecord
that can be compared to public datasets (GW, timing, spectra).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .invariants import LOCKED_WG, DEFAULT_KAPPA, InvariantSet, burst_threshold
from .positional import PositionalPhase, phase_to_frequency, phase_to_timing_offset


@dataclass
class PredictionRecord:
    """A single falsifiable forecast with precision and fail-condition."""

    name: str
    domain: str  # e.g. "gw_echo", "qpo", "interferometry"
    quantity: str  # e.g. "echo_delay_s", "peak_freq_hz"
    value: float
    unit: str
    uncertainty: float
    model_version: str = "0.1.0"
    assumptions: dict[str, Any] = field(default_factory=dict)
    falsify_if: str = ""
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def passes(self, observed: float) -> bool:
        """Simple |obs - pred| ≤ uncertainty check."""
        return abs(observed - self.value) <= self.uncertainty


def gw_echo_delay(
    inv: InvariantSet | None = None,
    *,
    mass_solar: float = 30.0,
    lattice_index: int = 1,
    model_version: str = "0.1.0",
) -> PredictionRecord:
    """GW echo / burst delay tied to positional 350/π phase.

    Toy forward model (placeholder for full paper pipeline):
        δt ≈ (G M / c³) · 2π · (n / W_g) · (1 + κ)

    Uses geometric time unit GM/c³ scaled by lattice phase and holonomy κ.
    This is intentionally simple and documented so it can be replaced by
    the full GW_Echo_Derivation mapping without changing the record schema.
    """
    inv = inv or InvariantSet()
    # GM/c³ for 1 M_sun ≈ 4.925490947e-6 s
    t_m = 4.925490947e-6 * mass_solar
    phase = PositionalPhase(wg=inv.wg, lattice_index=lattice_index)
    # holonomy-weighted positional delay
    delay = t_m * 2.0 * math.pi * phase.lattice_phase_unit * (1.0 + inv.kappa)
    # if lattice_phase_unit is tiny for small n/W_g, use fiber fraction explicitly
    if delay < 1e-12:
        delay = t_m * (2.0 * math.pi / inv.wg) * lattice_index * (1.0 + inv.kappa)

    return PredictionRecord(
        name="gw_echo_delay_positional",
        domain="gw_echo",
        quantity="echo_delay_s",
        value=float(delay),
        unit="s",
        uncertainty=float(0.15 * delay),  # 15% provisional
        model_version=model_version,
        assumptions={
            "mass_solar": mass_solar,
            "wg": inv.wg,
            "kappa": inv.kappa,
            "lattice_index": lattice_index,
            "theta_crit": inv.theta_crit,
            "formula": "δt = (GM/c³)·2π·(n/W_g)·(1+κ)",
        },
        falsify_if=(
            f"If measured echo delay differs from {delay:.6e} s by more than "
            f"{0.15 * delay:.6e} s for ~{mass_solar} M_sun remnants at lattice "
            f"index n={lattice_index}, revise positional phase mapping or κ."
        ),
    )


def gw_burst_spectrum(
    inv: InvariantSet | None = None,
    *,
    scale_hz: float = 250.0,
    lattice_index: int = 0,
    model_version: str = "0.1.0",
) -> PredictionRecord:
    """Characteristic burst/echo spectral peak from positional W_g.

    f_peak ≈ scale_hz · W_g / (2π) with mild positional modulation.
    Default scale_hz=250 places the peak near the ~350–600 Hz QPO / ringdown
    overlap band discussed in the project roadmap (tune to instrument band).
    """
    inv = inv or InvariantSet()
    phase = PositionalPhase(wg=inv.wg, lattice_index=lattice_index)
    f_peak = phase_to_frequency(phase, scale_hz=scale_hz, wg=inv.wg)

    return PredictionRecord(
        name="gw_burst_peak_freq",
        domain="gw_echo",
        quantity="peak_freq_hz",
        value=float(f_peak),
        unit="Hz",
        uncertainty=float(0.10 * f_peak),
        model_version=model_version,
        assumptions={
            "scale_hz": scale_hz,
            "wg": inv.wg,
            "kappa": inv.kappa,
            "theta_crit": burst_threshold(inv.kappa),
            "lattice_index": lattice_index,
        },
        falsify_if=(
            f"If no spectral feature is found within 10% of {f_peak:.2f} Hz "
            f"in the calibrated band for the stated scale, discard or retune "
            f"scale_hz / positional modulation."
        ),
    )


def timing_offset_series(
    n_sites: int = 8,
    base_period_s: float = 1.0,
    inv: InvariantSet | None = None,
) -> list[PredictionRecord]:
    """Series of timing offsets for successive lattice alignments."""
    inv = inv or InvariantSet()
    records = []
    for n in range(n_sites):
        p = PositionalPhase(wg=inv.wg, lattice_index=n)
        dt = phase_to_timing_offset(p, base_period=base_period_s)
        records.append(
            PredictionRecord(
                name=f"timing_offset_site_{n}",
                domain="timing",
                quantity="delta_t_s",
                value=float(dt),
                unit="s",
                uncertainty=float(0.05 * base_period_s),
                assumptions={"site": n, "wg": inv.wg, "base_period_s": base_period_s},
                falsify_if=(
                    f"If event timing residuals show no structure near δt={dt:.6f} s "
                    f"(period={base_period_s}s), positional lattice hypothesis weakens."
                ),
            )
        )
    return records


def write_prediction_bundle(
    records: list[PredictionRecord],
    path: str | Path,
) -> Path:
    """Write JSON bundle for reproducibility / external comparison."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "invariant_hunt.prediction_bundle.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_wg": LOCKED_WG,
        "n_predictions": len(records),
        "predictions": [r.to_dict() for r in records],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
