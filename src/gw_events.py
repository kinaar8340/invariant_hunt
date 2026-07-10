"""
Public GW event catalog for mapping positional echo ladders.

Parameters are approximate published values (not PE posterior samples).
Sources: LIGO/Virgo discovery papers / GWOSC event pages / GWTC-1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# Geometric time for 1 M_sun: GM/c³ [s]
T_M_SUN: float = 4.925490947e-6


@dataclass(frozen=True)
class PublicGWEvent:
    """Minimal public-event descriptor for echo-ladder mapping."""

    name: str
    gps: float
    """Merger GPS time (approx)."""
    mass_final_solar: float
    """Approximate remnant mass [M_sun]."""
    mass1_solar: float
    mass2_solar: float
    f_ring_hz: float
    """Approximate ringdown frequency [Hz]."""
    detectors: tuple[str, ...]
    """Preferred public strain detectors."""
    duration_post_s: float = 0.20
    """Post-merger analysis window length."""
    duration_pre_s: float = 0.25
    """Pre-merger context for noise estimation / PE fit."""
    f_low_hz: float = 50.0
    """Analysis band low edge for whitening / residual."""
    f_high_hz: float = 300.0
    """Analysis band high edge (event-dependent for lighter BBHs)."""
    notes: str = ""

    @property
    def t_m(self) -> float:
        """GM/c³ for remnant [s]."""
        return T_M_SUN * self.mass_final_solar

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["t_m_s"] = self.t_m
        return d


def _f_ring_scale(m_final: float, ref_m: float = 63.1, ref_f: float = 250.0) -> float:
    """Rough ringdown scale ∝ 1/M_final from GW150914 reference."""
    return ref_f * (ref_m / max(m_final, 1.0))


# --- Catalog -----------------------------------------------------------------

GW150914 = PublicGWEvent(
    name="GW150914",
    gps=1126259462.4,
    mass_final_solar=63.1,
    mass1_solar=35.6,
    mass2_solar=30.6,
    f_ring_hz=250.0,
    detectors=("H1", "L1"),
    duration_post_s=0.20,
    duration_pre_s=0.25,
    f_low_hz=50.0,
    f_high_hz=300.0,
    notes=(
        "First BBH detection. GWTC-1 PE: M_final≈63.1 M_sun, d_L≈440 Mpc."
    ),
)

GW151226 = PublicGWEvent(
    name="GW151226",
    gps=1135136350.6,
    mass_final_solar=20.5,
    mass1_solar=13.7,
    mass2_solar=7.7,
    f_ring_hz=round(_f_ring_scale(20.5), 1),  # ~768 Hz
    detectors=("H1", "L1"),
    duration_post_s=0.20,
    duration_pre_s=0.25,
    f_low_hz=50.0,
    f_high_hz=900.0,  # higher band for lighter remnant
    notes=(
        "Second BBH. GWTC-1: M_final≈20.5 M_sun, network SNR≈13. "
        "Higher ringdown frequency → wider analysis band."
    ),
)

GW170104 = PublicGWEvent(
    name="GW170104",
    gps=1167559936.6,
    mass_final_solar=48.9,
    mass1_solar=30.8,
    mass2_solar=20.0,
    f_ring_hz=round(_f_ring_scale(48.9), 1),  # ~322 Hz
    detectors=("H1", "L1"),
    duration_post_s=0.20,
    duration_pre_s=0.25,
    f_low_hz=50.0,
    f_high_hz=400.0,
    notes=(
        "Third BBH. GWTC-1: M_final≈48.9 M_sun, d_L≈990 Mpc, network SNR≈13."
    ),
)

GW170817 = PublicGWEvent(
    name="GW170817",
    gps=1187008882.4,
    mass_final_solar=2.8,
    mass1_solar=1.46,
    mass2_solar=1.27,
    f_ring_hz=2000.0,
    detectors=("H1", "L1", "V1"),
    duration_post_s=0.50,
    notes="BNS; echo ladder less standard — kept for future extension.",
)

CATALOG: dict[str, PublicGWEvent] = {
    GW150914.name: GW150914,
    GW151226.name: GW151226,
    GW170104.name: GW170104,
    GW170817.name: GW170817,
}


def get_event(name: str) -> PublicGWEvent:
    key = name.strip().upper()
    for k, ev in CATALOG.items():
        if k.upper() == key:
            return ev
    known = ", ".join(sorted(CATALOG))
    raise KeyError(f"Unknown event {name!r}. Known: {known}")


# GWOSC 32 s @ 4 kHz HDF5 (public event releases)
# URLs from eventapi JSON (GWTC-1-confident)
GWOSC_32S: dict[str, dict[str, Any]] = {
    "GW150914": {
        "H1": "H-H1_LOSC_4_V2-1126259446-32.hdf5",
        "L1": "L-L1_LOSC_4_V2-1126259446-32.hdf5",
        "urls": {
            "H1": "https://gwosc.org/GW150914data/H-H1_LOSC_4_V2-1126259446-32.hdf5",
            "L1": "https://gwosc.org/GW150914data/L-L1_LOSC_4_V2-1126259446-32.hdf5",
        },
        "base_url": "https://gwosc.org/GW150914data/",
        "gps_start": 1126259446,
        "duration": 32,
        "sample_rate": 4096,
    },
    "GW151226": {
        "H1": "H-H1_GWOSC_4KHZ_R1-1135136335-32.hdf5",
        "L1": "L-L1_GWOSC_4KHZ_R1-1135136335-32.hdf5",
        "urls": {
            "H1": "https://gwosc.org/eventapi/json/GWTC-1-confident/GW151226/v2/H-H1_GWOSC_4KHZ_R1-1135136335-32.hdf5",
            "L1": "https://gwosc.org/eventapi/json/GWTC-1-confident/GW151226/v2/L-L1_GWOSC_4KHZ_R1-1135136335-32.hdf5",
        },
        "gps_start": 1135136335,
        "duration": 32,
        "sample_rate": 4096,
    },
    "GW170104": {
        "H1": "H-H1_GWOSC_4KHZ_R1-1167559921-32.hdf5",
        "L1": "L-L1_GWOSC_4KHZ_R1-1167559921-32.hdf5",
        "urls": {
            "H1": "https://gwosc.org/eventapi/json/GWTC-1-confident/GW170104/v2/H-H1_GWOSC_4KHZ_R1-1167559921-32.hdf5",
            "L1": "https://gwosc.org/eventapi/json/GWTC-1-confident/GW170104/v2/L-L1_GWOSC_4KHZ_R1-1167559921-32.hdf5",
        },
        "gps_start": 1167559921,
        "duration": 32,
        "sample_rate": 4096,
    },
}
