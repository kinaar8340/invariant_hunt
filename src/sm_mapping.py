"""
Phase 2 — SM particle content mapping from gauged Hopf lattice modes.

Maps lattice / flywheel / braiding excitations onto SM gauge bosons, chiral
fermions, and the Higgs multiplet with textbook quantum numbers under
G = SU(3)_c × SU(2)_L × U(1)_Y.

Discipline
----------
- Core locks (W_g, κ, φ_b) are frozen inputs — not free SM fit parameters.
- Phase 2.1 (Gate SM-1): representations + quantum numbers only.
- Masses, mixings, Yukawa hierarchies → Gate SM-2 (scaffolded, not claimed).
- Anomaly cancellation + RG flow → Gate SM-3 (scaffolded checks available).
- No gravity / full EFT claims.

Hypercharge convention (PDG / Wikipedia weak hypercharge):
  Q = T_3 + Y/2
  with Y(Q_L)=1/3, Y(u_R)=4/3, Y(d_R)=-2/3, Y(L_L)=-1, Y(e_R)=-2, Y(H)=1.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from src.invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
)

# ---------------------------------------------------------------------------
# Quantum-number records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuantumNumbers:
    """SU(3)×SU(2)×U(1)_Y quantum numbers for one multiplet (one generation)."""

    name: str
    su3: str  # "1", "3", "3bar", "8", …
    su2: int  # weak multiplet dimension (1 or 2 typically; 3 for W)
    Y: float  # hypercharge (Q = T3 + Y/2)
    spin: float  # 0, 1/2, 1
    statistics: str  # "boson" | "fermion"
    chirality: str  # "L", "R", "vector", "scalar"
    T3_max: float  # highest T3 in multiplet (for charge table)
    lattice_mode: str  # Hopf-lattice excitation label
    generation: int | None = None  # 1,2,3 or None for force/Higgs
    notes: str = ""

    @property
    def Q_max(self) -> float:
        """Electric charge of the highest T3 component: Q = T3 + Y/2."""
        return self.T3_max + 0.5 * self.Y
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["Q_max"] = self.Q_max
        return d


def _qn(
    name: str,
    su3: str,
    su2: int,
    Y: float,
    spin: float,
    statistics: str,
    chirality: str,
    T3_max: float,
    lattice_mode: str,
    generation: int | None = None,
    notes: str = "",
) -> QuantumNumbers:
    return QuantumNumbers(
        name=name,
        su3=su3,
        su2=su2,
        Y=Y,
        spin=spin,
        statistics=statistics,
        chirality=chirality,
        T3_max=T3_max,
        lattice_mode=lattice_mode,
        generation=generation,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Canonical SM content (one generation) + generation copies
# ---------------------------------------------------------------------------

# Gauge bosons (adjoint / U(1) modes of product YM on the Hopf lattice)
GAUGE_BOSONS: tuple[QuantumNumbers, ...] = (
    _qn(
        "g",
        "8",
        1,
        0.0,
        1.0,
        "boson",
        "vector",
        0.0,
        "ym_adjoint_su3_flux_flywheel",
        notes="SU(3)_c gluons; 8 real vector modes",
    ),
    _qn(
        "W",
        "1",
        3,
        0.0,
        1.0,
        "boson",
        "vector",
        1.0,
        "ym_adjoint_su2_holonomy_wave",
        notes="SU(2)_L weak bosons before EWSB; W±, W3",
    ),
    _qn(
        "B",
        "1",
        1,
        0.0,
        1.0,
        "boson",
        "vector",
        0.0,
        "ym_u1_global_pointer_photon_seed",
        notes="U(1)_Y hypercharge; mixes with W3 → γ, Z after EWSB",
    ),
)

# Higgs doublet — radial modulus of holonomy / pointer VEV sector
# Y_H = 1 so Q = T3 + 1/2 → (H+, H0) charges (1, 0)
HIGGS: QuantumNumbers = _qn(
    "H",
    "1",
    2,
    1.0,
    0.0,
    "boson",
    "scalar",
    0.5,
    "holonomy_modulus_pointer_vev",
    notes="SM Higgs doublet; lattice: amplitude of global pointer VEV",
)

# One-generation chiral fermions (left-handed Weyl multiplets + RH singlets)
# Lattice: Hopfion solitons; generation index = braiding layer / winding family
# Y under Q = T3 + Y/2
_FERMION_TEMPLATES: tuple[tuple[str, str, int, float, str, float, str, str], ...] = (
    # name, su3, su2, Y, chirality, T3_max, lattice_mode_stem, notes
    ("Q_L", "3", 2, 1.0 / 3.0, "L", 0.5, "hopfion_color_weak_doublet", "quark doublet (u,d)_L"),
    ("u_R", "3", 1, 4.0 / 3.0, "R", 0.0, "hopfion_up_singlet", "right-handed up-type"),
    ("d_R", "3", 1, -2.0 / 3.0, "R", 0.0, "hopfion_down_singlet", "right-handed down-type"),
    ("L_L", "1", 2, -1.0, "L", 0.5, "hopfion_lepton_doublet", "lepton doublet (ν,e)_L"),
    ("e_R", "1", 1, -2.0, "R", 0.0, "hopfion_charged_lepton_singlet", "right-handed charged lepton"),
)


def fermion_one_generation(gen: int = 1) -> tuple[QuantumNumbers, ...]:
    """Build one generation of SM chiral fermions with generation-tagged modes."""
    if gen not in (1, 2, 3):
        raise ValueError("generation must be 1, 2, or 3")
    out: list[QuantumNumbers] = []
    for name, su3, su2, Y, chi, T3, stem, notes in _FERMION_TEMPLATES:
        spin = 0.5
        out.append(
            _qn(
                name if gen == 1 else f"{name}^({gen})",
                su3,
                su2,
                Y,
                spin,
                "fermion",
                chi,
                T3,
                f"{stem}_gen{gen}_braid_layer",
                generation=gen,
                notes=notes,
            )
        )
    return tuple(out)


def optional_sterile_nu_R(gen: int = 1) -> QuantumNumbers:
    """Optional sterile ν_R (not required for SM-1 minimal content)."""
    return _qn(
        "nu_R" if gen == 1 else f"nu_R^({gen})",
        "1",
        1,
        0.0,
        0.5,
        "fermion",
        "R",
        0.0,
        f"hopfion_sterile_singlet_gen{gen}",
        generation=gen,
        notes="optional; not required for minimal SM Gate SM-1",
    )


def sm_content(
    *,
    n_generations: int = 3,
    include_sterile: bool = False,
) -> list[QuantumNumbers]:
    """Full SM multiplet list used for Gate SM-1."""
    fields: list[QuantumNumbers] = list(GAUGE_BOSONS) + [HIGGS]
    for g in range(1, n_generations + 1):
        fields.extend(fermion_one_generation(g))
        if include_sterile:
            fields.append(optional_sterile_nu_R(g))
    return fields


# ---------------------------------------------------------------------------
# Electric charge table (Gate SM-1 cross-check)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChargeComponent:
    """Single T3 component of a multiplet with electric charge Q."""

    multiplet: str
    generation: int | None
    T3: float
    Y: float
    Q: float
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def expand_charge_components(qn: QuantumNumbers) -> list[ChargeComponent]:
    """Expand multiplet into T3 components with Q = T3 + Y/2."""
    if qn.su2 == 1:
        t3_vals = [0.0]
    elif qn.su2 == 2:
        t3_vals = [0.5, -0.5]
    elif qn.su2 == 3:
        t3_vals = [1.0, 0.0, -1.0]
    else:
        # generic isospin (dim = 2j+1)
        j = 0.5 * (qn.su2 - 1)
        t3_vals = [j - k for k in range(qn.su2)]

    comps: list[ChargeComponent] = []
    for t3 in t3_vals:
        Q = t3 + 0.5 * qn.Y
        # Labels for common SM cases
        label = f"{qn.name}[T3={t3:g}]"
        if qn.name.startswith("Q_L") and abs(t3 - 0.5) < 1e-12:
            label = "u_L" if qn.generation in (None, 1) else f"u_L^({qn.generation})"
        elif qn.name.startswith("Q_L") and abs(t3 + 0.5) < 1e-12:
            label = "d_L" if qn.generation in (None, 1) else f"d_L^({qn.generation})"
        elif qn.name.startswith("L_L") and abs(t3 - 0.5) < 1e-12:
            label = "nu_L" if qn.generation in (None, 1) else f"nu_L^({qn.generation})"
        elif qn.name.startswith("L_L") and abs(t3 + 0.5) < 1e-12:
            label = "e_L" if qn.generation in (None, 1) else f"e_L^({qn.generation})"
        elif qn.name == "W":
            label = {1.0: "W+", 0.0: "W3", -1.0: "W-"}[t3]
        elif qn.name == "H":
            label = "H+" if t3 > 0 else "H0"
        comps.append(
            ChargeComponent(
                multiplet=qn.name,
                generation=qn.generation,
                T3=t3,
                Y=qn.Y,
                Q=Q,
                label=label,
            )
        )
    return comps


# Expected charges for Gate SM-1 (generation 1 canonical labels)
_EXPECTED_CHARGES: dict[str, float] = {
    "u_L": 2.0 / 3.0,
    "d_L": -1.0 / 3.0,
    "u_R": 2.0 / 3.0,
    "d_R": -1.0 / 3.0,
    "nu_L": 0.0,
    "e_L": -1.0,
    "e_R": -1.0,
    "W+": 1.0,
    "W3": 0.0,
    "W-": -1.0,
    "H+": 1.0,
    "H0": 0.0,
    "g[T3=0]": 0.0,
    "B[T3=0]": 0.0,
}


# ---------------------------------------------------------------------------
# Lattice mode map (flywheel / braiding / Hopf)
# ---------------------------------------------------------------------------


@dataclass
class LatticeModeMap:
    """Association of a lattice excitation class with SM multiplet(s)."""

    mode_class: str
    description: str
    sm_targets: list[str]
    topological_tag: str
    lock_inputs: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_lattice_mode_maps() -> list[LatticeModeMap]:
    """Phase 2.1 canonical mode → SM map (locks as frozen inputs)."""
    locks = {
        "W_g": LOCKED_WG,
        "wg_base": WG_BASE,
        "kappa": DEFAULT_KAPPA,
        "phi_b": DEFAULT_BRAIDING,
    }
    return [
        LatticeModeMap(
            mode_class="ym_adjoint_flux_flywheel",
            description="SU(3) adjoint vector modes of product YM (flux flywheels)",
            sm_targets=["g"],
            topological_tag="adjoint_su3",
            lock_inputs=dict(locks),
        ),
        LatticeModeMap(
            mode_class="ym_adjoint_holonomy_wave",
            description="SU(2) adjoint waves tied to pointer holonomy κ",
            sm_targets=["W"],
            topological_tag="adjoint_su2",
            lock_inputs=dict(locks),
        ),
        LatticeModeMap(
            mode_class="u1_pointer_photon_seed",
            description="U(1)_Y mode from global pointer / mean-field holonomy",
            sm_targets=["B"],
            topological_tag="u1_pointer",
            lock_inputs=dict(locks),
        ),
        LatticeModeMap(
            mode_class="holonomy_modulus",
            description="Amplitude of global pointer VEV → Higgs doublet",
            sm_targets=["H"],
            topological_tag="vev_modulus",
            lock_inputs=dict(locks),
        ),
        LatticeModeMap(
            mode_class="hopfion_soliton_family",
            description="Half-integer Hopfion defects (S³ double cover) → fermions",
            sm_targets=["Q_L", "u_R", "d_R", "L_L", "e_R"],
            topological_tag="hopfion_pi3",
            lock_inputs=dict(locks),
        ),
        LatticeModeMap(
            mode_class="braiding_layer_generation",
            description="Braiding-layer / winding family index n_g=1,2,3 → generations",
            sm_targets=["gen1", "gen2", "gen3"],
            topological_tag=f"braid_phi_b={DEFAULT_BRAIDING}",
            lock_inputs=dict(locks),
        ),
    ]


# ---------------------------------------------------------------------------
# Gate SM-1: representation + quantum-number consistency
# ---------------------------------------------------------------------------


def _is_close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def check_electric_charges(
    fields: Sequence[QuantumNumbers] | None = None,
) -> dict[str, Any]:
    """Verify Q = T3 + Y/2 against expected SM charges (gen-1 labels + W/H/g/B)."""
    fields = list(fields) if fields is not None else sm_content(n_generations=1)
    comps: list[ChargeComponent] = []
    for qn in fields:
        comps.extend(expand_charge_components(qn))

    mismatches: list[dict[str, Any]] = []
    checked = 0
    for c in comps:
        key = c.label
        # Also check multiplet singlets by multiplet name for RH fields
        expected = _EXPECTED_CHARGES.get(key)
        if expected is None and c.multiplet in ("u_R", "d_R", "e_R"):
            expected = _EXPECTED_CHARGES.get(c.multiplet)
            key = c.multiplet
        if expected is None:
            continue
        checked += 1
        if not _is_close(c.Q, expected):
            mismatches.append(
                {"label": key, "Q_computed": c.Q, "Q_expected": expected, "T3": c.T3, "Y": c.Y}
            )

    return {
        "n_components": len(comps),
        "n_checked": checked,
        "mismatches": mismatches,
        "pass": len(mismatches) == 0 and checked >= 10,
        "components": [c.to_dict() for c in comps],
    }


def check_representation_catalog(
    fields: Sequence[QuantumNumbers] | None = None,
    *,
    n_generations: int = 3,
) -> dict[str, Any]:
    """Ensure required multiplet types exist with correct (su3, su2, Y)."""
    fields = list(fields) if fields is not None else sm_content(n_generations=n_generations)

    required_gauge = {
        "g": ("8", 1, 0.0),
        "W": ("1", 3, 0.0),
        "B": ("1", 1, 0.0),
    }
    required_higgs = ("1", 2, 1.0)
    required_fermion = {
        "Q_L": ("3", 2, 1.0 / 3.0),
        "u_R": ("3", 1, 4.0 / 3.0),
        "d_R": ("3", 1, -2.0 / 3.0),
        "L_L": ("1", 2, -1.0),
        "e_R": ("1", 1, -2.0),
    }

    by_name = {f.name: f for f in fields}
    errors: list[str] = []

    for name, (su3, su2, Y) in required_gauge.items():
        f = by_name.get(name)
        if f is None:
            errors.append(f"missing gauge boson {name}")
            continue
        if f.su3 != su3 or f.su2 != su2 or not _is_close(f.Y, Y):
            errors.append(f"bad quantum numbers for {name}: {(f.su3, f.su2, f.Y)}")

    h = by_name.get("H")
    if h is None:
        errors.append("missing Higgs H")
    elif h.su3 != required_higgs[0] or h.su2 != required_higgs[1] or not _is_close(h.Y, required_higgs[2]):
        errors.append(f"bad Higgs quantum numbers: {(h.su3, h.su2, h.Y)}")

    # Fermions: require n_generations copies of each template
    for stem, (su3, su2, Y) in required_fermion.items():
        for gen in range(1, n_generations + 1):
            key = stem if gen == 1 else f"{stem}^({gen})"
            # generation-1 stored as bare stem
            candidates = [
                f
                for f in fields
                if f.generation == gen
                and (
                    f.name == stem
                    or f.name.startswith(stem)
                    or (stem in f.name and f.generation == gen)
                )
            ]
            # tighter: match template by lattice stem or exact names
            matched = [
                f
                for f in fields
                if f.generation == gen
                and (
                    f.name == stem
                    or f.name == f"{stem}^({gen})"
                    or f.lattice_mode.startswith(
                        {
                            "Q_L": "hopfion_color_weak_doublet",
                            "u_R": "hopfion_up_singlet",
                            "d_R": "hopfion_down_singlet",
                            "L_L": "hopfion_lepton_doublet",
                            "e_R": "hopfion_charged_lepton_singlet",
                        }[stem]
                    )
                )
            ]
            if not matched:
                errors.append(f"missing fermion {stem} gen={gen}")
                continue
            f = matched[0]
            if f.su3 != su3 or f.su2 != su2 or not _is_close(f.Y, Y):
                errors.append(f"bad qn {stem} gen={gen}: {(f.su3, f.su2, f.Y)}")
            if f.spin != 0.5 or f.statistics != "fermion":
                errors.append(f"bad spin/statistics {stem} gen={gen}")

    n_fermion = sum(1 for f in fields if f.statistics == "fermion" and f.generation is not None)
    expected_fermion = 5 * n_generations  # without sterile

    return {
        "n_fields": len(fields),
        "n_fermion_multiplets": n_fermion,
        "expected_fermion_multiplets": expected_fermion,
        "n_generations": n_generations,
        "errors": errors,
        "pass": len(errors) == 0 and n_fermion >= expected_fermion,
    }


def check_lattice_mode_coverage(
    fields: Sequence[QuantumNumbers] | None = None,
) -> dict[str, Any]:
    """Every multiplet has a non-empty unique lattice_mode tag; maps cover targets."""
    fields = list(fields) if fields is not None else sm_content()
    modes = [f.lattice_mode for f in fields]
    empty = [f.name for f in fields if not f.lattice_mode]
    # modes should be unique per multiplet instance
    dupes = sorted({m for m in modes if modes.count(m) > 1})

    maps = default_lattice_mode_maps()
    map_targets = set()
    for m in maps:
        map_targets.update(m.sm_targets)

    required_targets = {"g", "W", "B", "H", "Q_L", "u_R", "d_R", "L_L", "e_R", "gen1", "gen2", "gen3"}
    missing_targets = sorted(required_targets - map_targets)

    locks_ok = all(
        _is_close(m.lock_inputs.get("W_g", -1), LOCKED_WG)
        and _is_close(m.lock_inputs.get("kappa", -1), DEFAULT_KAPPA)
        for m in maps
    )

    return {
        "n_modes": len(modes),
        "empty_modes": empty,
        "duplicate_modes": dupes,
        "missing_map_targets": missing_targets,
        "locks_frozen_in_maps": locks_ok,
        "pass": not empty and not dupes and not missing_targets and locks_ok,
        "maps": [m.to_dict() for m in maps],
    }


def check_locks_frozen() -> dict[str, Any]:
    """Confirm SM mapping module does not redefine core locks."""
    return {
        "W_g": LOCKED_WG,
        "wg_base": WG_BASE,
        "kappa": DEFAULT_KAPPA,
        "phi_b": DEFAULT_BRAIDING,
        "pass": (
            _is_close(LOCKED_WG, WG_BASE / math.pi)
            and _is_close(DEFAULT_KAPPA, 0.85)
            and _is_close(DEFAULT_BRAIDING, 0.8145)
        ),
    }


# ---------------------------------------------------------------------------
# Gate SM-3 scaffold: anomaly cancellation (can run early; required later)
# ---------------------------------------------------------------------------


def _hypercharge_anomaly_trace(
    fields: Sequence[QuantumNumbers],
    *,
    generation: int = 1,
) -> dict[str, float]:
    """Chiral anomaly coefficients for one generation (all-LH Weyl convention).

    RH singlets enter as LH conjugates with opposite hypercharge.
    Multiplicity = dim(color) × dim(weak). Standard SM → all traces zero.
    """
    gen_fields = [f for f in fields if f.generation == generation and f.statistics == "fermion"]

    def color_dim(su3: str) -> int:
        return {"1": 1, "3": 3, "3bar": 3, "8": 8}.get(su3, 1)

    su3_su3_u1 = 0.0
    su2_su2_u1 = 0.0
    u1_cube = 0.0
    grav_u1 = 0.0

    for f in gen_fields:
        # LH Weyl hypercharge
        Y = -f.Y if f.chirality == "R" else f.Y
        n_c = color_dim(f.su3)
        n_w = f.su2
        mult = n_c * n_w

        # [SU(3)]² U(1): sum Y over color-triplet Weyl components (each weak component)
        if f.su3 in ("3", "3bar"):
            su3_su3_u1 += Y * n_w
        # [SU(2)]² U(1): sum Y × N_color over weak doublets
        if f.su2 == 2:
            su2_su2_u1 += Y * n_c
        u1_cube += mult * (Y**3)
        grav_u1 += mult * Y

    return {
        "su3_su3_u1": su3_su3_u1,
        "su2_su2_u1": su2_su2_u1,
        "u1_u1_u1": u1_cube,
        "grav_u1": grav_u1,
    }


def check_anomaly_cancellation(
    fields: Sequence[QuantumNumbers] | None = None,
    *,
    n_generations: int = 3,
    tol: float = 1e-9,
) -> dict[str, Any]:
    """Standard SM anomaly coefficients must vanish per generation."""
    fields = list(fields) if fields is not None else sm_content(n_generations=n_generations)
    gen_results = []
    all_ok = True
    for g in range(1, n_generations + 1):
        tr = _hypercharge_anomaly_trace(fields, generation=g)
        # SM analytic targets (all zero)
        ok = all(abs(v) < tol for v in tr.values())
        # Known SM values: su3_su3_u1 = 0, su2_su2_u1 = 0, etc.
        # Our LH conversion: verify against textbook zeros
        gen_results.append({"generation": g, "traces": tr, "pass": ok})
        if not ok:
            all_ok = False

    return {
        "generations": gen_results,
        "pass": all_ok,
        "note": "Gate SM-3 primary; reported early as scaffold consistency for SM content",
    }


# ---------------------------------------------------------------------------
# Gate SM-2 scaffold: generation structure (hierarchy not fitted here)
# ---------------------------------------------------------------------------


def check_three_generations(
    fields: Sequence[QuantumNumbers] | None = None,
) -> dict[str, Any]:
    """Require three identical representation copies (masses not checked)."""
    fields = list(fields) if fields is not None else sm_content(n_generations=3)
    gens = sorted({f.generation for f in fields if f.generation is not None})
    stems_per_gen: dict[int, set[str]] = {}
    for f in fields:
        if f.generation is None:
            continue
        # normalize stem
        stem = f.name.split("^")[0]
        stems_per_gen.setdefault(f.generation, set()).add(stem)

    expected = {"Q_L", "u_R", "d_R", "L_L", "e_R"}
    errors: list[str] = []
    if gens != [1, 2, 3]:
        errors.append(f"generations present: {gens}, expected [1,2,3]")
    for g in (1, 2, 3):
        have = stems_per_gen.get(g, set())
        if have != expected:
            errors.append(f"gen {g} stems {have} != {expected}")

    # Representation equality across gens
    for stem in expected:
        qns = []
        for g in (1, 2, 3):
            for f in fields:
                if f.generation == g and f.name.split("^")[0] == stem:
                    qns.append((f.su3, f.su2, f.Y))
        if len(qns) == 3 and not all(q == qns[0] for q in qns):
            errors.append(f"representation drift for {stem}: {qns}")

    return {
        "generations": gens,
        "stems_per_gen": {k: sorted(v) for k, v in stems_per_gen.items()},
        "errors": errors,
        "pass": len(errors) == 0,
        "masses_fitted": False,
        "note": "Gate SM-2 structure only; Yukawa/mass hierarchy deferred",
    }


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def gate_sm1_report(
    *,
    n_generations: int = 3,
    include_sterile: bool = False,
) -> dict[str, Any]:
    """Full Gate SM-1 report (representations + charges + lattice modes + locks)."""
    fields = sm_content(n_generations=n_generations, include_sterile=include_sterile)
    catalog = check_representation_catalog(fields, n_generations=n_generations)
    charges = check_electric_charges(
        [f for f in fields if f.generation in (None, 1)] + [f for f in fields if f.statistics == "boson"]
    )
    # recompute charges on full list but expectations only for gen1 labels
    charges = check_electric_charges(sm_content(n_generations=1, include_sterile=False))
    modes = check_lattice_mode_coverage(fields)
    locks = check_locks_frozen()

    criteria = {
        "representation_catalog": catalog["pass"],
        "electric_charges": charges["pass"],
        "lattice_mode_coverage": modes["pass"],
        "locks_frozen": locks["pass"],
    }
    return {
        "schema": "invariant_hunt.sm_mapping.v1",
        "phase": "2.1",
        "gate": "SM-1",
        "n_generations": n_generations,
        "include_sterile": include_sterile,
        "n_fields": len(fields),
        "fields": [f.to_dict() for f in fields],
        "catalog": {k: v for k, v in catalog.items() if k != "errors"} | {"errors": catalog["errors"]},
        "charges": {
            "n_components": charges["n_components"],
            "n_checked": charges["n_checked"],
            "mismatches": charges["mismatches"],
            "pass": charges["pass"],
        },
        "lattice_modes": {
            "n_modes": modes["n_modes"],
            "empty_modes": modes["empty_modes"],
            "duplicate_modes": modes["duplicate_modes"],
            "missing_map_targets": modes["missing_map_targets"],
            "locks_frozen_in_maps": modes["locks_frozen_in_maps"],
            "pass": modes["pass"],
            "maps": modes["maps"],
        },
        "locks": locks,
        "criteria": criteria,
        "pass": all(criteria.values()),
        "discipline": {
            "no_mass_claim": True,
            "no_gravity_claim": True,
            "premerger_freeze_untouched": True,
        },
    }


def gate_sm2_report() -> dict[str, Any]:
    """Gate SM-2 structure: three-generation copies (masses via sm_yukawa)."""
    gen = check_three_generations()
    return {
        "schema": "invariant_hunt.sm_mapping.v1",
        "phase": "2.2",
        "gate": "SM-2",
        "structure": gen,
        "pass": gen["pass"],
        "yukawa_optimized": False,
        "note": (
            "Structure only. For mass/mixing χ² upgrade use "
            "src.sm_yukawa.gate_sm2_mass_report or scripts/sm_yukawa_ansatz.py --sweep"
        ),
    }


def gate_sm3_report() -> dict[str, Any]:
    """Gate SM-3: anomaly cancellation + one-loop SM RG (Phase 2.3).

    Delegates full RG checks to ``src.sm_rg.gate_sm3_full_report`` when available;
    always requires anomaly cancellation.
    """
    anom = check_anomaly_cancellation()
    try:
        from src.sm_rg import gate_sm3_full_report

        full = gate_sm3_full_report()
        return {
            "schema": "invariant_hunt.sm_mapping.v1",
            "phase": "2.3",
            "gate": "SM-3",
            "anomaly": anom,
            "rg_flow": {
                "implemented": True,
                "pass": full["criteria"]["rg_consistency"],
                "detail": full.get("rg_criteria_detail"),
            },
            "pass": full["pass"],
            "full": full,
            "note": full.get("note", "Anomaly + one-loop SM RG"),
        }
    except Exception as exc:  # pragma: no cover
        return {
            "schema": "invariant_hunt.sm_mapping.v1",
            "phase": "2.3",
            "gate": "SM-3",
            "anomaly": anom,
            "rg_flow": {"implemented": False, "pass": None, "error": str(exc)},
            "pass": anom["pass"],
            "note": f"Anomaly only (RG import failed: {exc})",
        }


def sm_full_report() -> dict[str, Any]:
    """Combined Phase 2 gate snapshot."""
    sm1 = gate_sm1_report()
    sm2 = gate_sm2_report()
    sm3 = gate_sm3_report()
    return {
        "schema": "invariant_hunt.sm_gates.v1",
        "locks": check_locks_frozen(),
        "SM-1": {"pass": sm1["pass"], "criteria": sm1["criteria"]},
        "SM-2": {"pass": sm2["pass"], "note": sm2["note"]},
        "SM-3": {"pass": sm3["pass"], "note": sm3["note"]},
        "phase_2_1_ready": sm1["pass"],
        "reports": {"SM-1": sm1, "SM-2": sm2, "SM-3": sm3},
    }


def sm_mode_loss_knobs(
    *,
    generation_weight: float = 1.0,
    anomaly_weight: float = 1.0,
) -> dict[str, Any]:
    """Surrogate loss for meta_optimize --sm-mode (locks fixed).

    Returns zero loss when SM-1/2/3 structure checks pass; large penalty otherwise.
    Does not re-fit W_g, κ, φ_b.
    """
    sm1 = gate_sm1_report()
    sm2 = gate_sm2_report()
    sm3 = gate_sm3_report()
    loss = 0.0
    if not sm1["pass"]:
        loss += 100.0
    if not sm2["pass"]:
        loss += 50.0 * generation_weight
    if not sm3["pass"]:
        loss += 50.0 * anomaly_weight
    return {
        "loss": float(loss),
        "sm1_pass": sm1["pass"],
        "sm2_pass": sm2["pass"],
        "sm3_pass": sm3["pass"],
        "locks": check_locks_frozen(),
        "discovered_Wg": LOCKED_WG,
        "dry_run": True,
        "mode": "sm_mode",
    }
