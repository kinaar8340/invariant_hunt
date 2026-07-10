"""
Public GW event catalog for mapping positional echo ladders.

Parameters are approximate published values (not PE posterior samples).
Sources: LIGO/Virgo discovery papers / GWOSC event pages.
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
    duration_pre_s: float = 0.05
    """Pre-merger context for noise estimation."""
    notes: str = ""

    @property
    def t_m(self) -> float:
        """GM/c³ for remnant [s]."""
        return T_M_SUN * self.mass_final_solar

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["t_m_s"] = self.t_m
        return d


# --- Catalog -----------------------------------------------------------------

GW150914 = PublicGWEvent(
    name="GW150914",
    gps=1126259462.4,
    mass_final_solar=63.1,  # GWTC-1 PE median final_mass_source
    mass1_solar=35.6,  # source-frame PE median (catalog); detector-frame from PE file
    mass2_solar=30.6,
    f_ring_hz=250.0,
    detectors=("H1", "L1"),
    duration_post_s=0.20,
    duration_pre_s=0.25,  # enough pre-merger for IMR PE template fit
    notes=(
        "First BBH detection. Public 32 s @ 4096 Hz release on GWOSC. "
        "GWTC-1 PE: M_final≈63.1 M_sun, d_L≈440 Mpc; ringdown ~250 Hz. "
        "Echo searches often probe post-merger ms–tens-of-ms delays."
    ),
)

GW170817 = PublicGWEvent(
    name="GW170817",
    gps=1187008882.4,
    mass_final_solar=2.8,
    mass1_solar=1.46,
    mass2_solar=1.27,
    f_ring_hz=2000.0,  # placeholder; BNS remnant uncertain
    detectors=("H1", "L1", "V1"),
    duration_post_s=0.50,
    notes="BNS; echo ladder less standard — kept for future extension.",
)

CATALOG: dict[str, PublicGWEvent] = {
    GW150914.name: GW150914,
    GW170817.name: GW170817,
}


def get_event(name: str) -> PublicGWEvent:
    key = name.strip().upper()
    # allow gw150914 / GW150914
    for k, ev in CATALOG.items():
        if k.upper() == key:
            return ev
    known = ", ".join(sorted(CATALOG))
    raise KeyError(f"Unknown event {name!r}. Known: {known}")


# GWOSC 32 s release filenames (4 kHz) for offline cache
GWOSC_32S: dict[str, dict[str, str]] = {
    "GW150914": {
        "H1": "H-H1_LOSC_4_V2-1126259446-32.hdf5",
        "L1": "L-L1_LOSC_4_V2-1126259446-32.hdf5",
        "base_url": "https://gwosc.org/GW150914data/",
        "gps_start": 1126259446,
        "duration": 32,
        "sample_rate": 4096,
    },
}
