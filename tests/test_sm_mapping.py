"""Tests for Phase 2 SM particle mapping (Gate SM-1 + scaffolds)."""

from __future__ import annotations

from src.invariants import DEFAULT_BRAIDING, DEFAULT_KAPPA, LOCKED_WG
from src.sm_mapping import (
    GAUGE_BOSONS,
    HIGGS,
    check_anomaly_cancellation,
    check_electric_charges,
    check_lattice_mode_coverage,
    check_locks_frozen,
    check_representation_catalog,
    check_three_generations,
    expand_charge_components,
    fermion_one_generation,
    gate_sm1_report,
    gate_sm2_report,
    gate_sm3_report,
    sm_content,
    sm_mode_loss_knobs,
)


def test_gauge_boson_counts():
    assert len(GAUGE_BOSONS) == 3
    names = {g.name for g in GAUGE_BOSONS}
    assert names == {"g", "W", "B"}
    assert GAUGE_BOSONS[0].su3 == "8"


def test_higgs_charges():
    comps = expand_charge_components(HIGGS)
    by_label = {c.label: c.Q for c in comps}
    assert abs(by_label["H+"] - 1.0) < 1e-12
    assert abs(by_label["H0"] - 0.0) < 1e-12


def test_fermion_gen1_charges():
    fields = fermion_one_generation(1)
    all_c = []
    for f in fields:
        all_c.extend(expand_charge_components(f))
    by = {c.label: c.Q for c in all_c}
    assert abs(by["u_L"] - 2.0 / 3.0) < 1e-12
    assert abs(by["d_L"] + 1.0 / 3.0) < 1e-12
    assert abs(by["nu_L"] - 0.0) < 1e-12
    assert abs(by["e_L"] + 1.0) < 1e-12
    e_r_q = by.get("e_R", by.get("e_R[T3=0]"))
    assert e_r_q is not None and abs(e_r_q + 1.0) < 1e-12


def test_sm_content_three_gen():
    fields = sm_content(n_generations=3)
    # 3 gauge + 1 Higgs + 5*3 fermions
    assert len(fields) == 3 + 1 + 15
    gens = {f.generation for f in fields if f.generation is not None}
    assert gens == {1, 2, 3}


def test_electric_charges_gate():
    r = check_electric_charges(sm_content(n_generations=1))
    assert r["pass"]
    assert r["mismatches"] == []


def test_representation_catalog():
    r = check_representation_catalog()
    assert r["pass"], r["errors"]


def test_lattice_mode_coverage():
    r = check_lattice_mode_coverage()
    assert r["pass"]
    assert r["locks_frozen_in_maps"]


def test_locks_frozen():
    r = check_locks_frozen()
    assert r["pass"]
    assert abs(r["W_g"] - LOCKED_WG) < 1e-15
    assert abs(r["kappa"] - DEFAULT_KAPPA) < 1e-15
    assert abs(r["phi_b"] - DEFAULT_BRAIDING) < 1e-15


def test_gate_sm1_pass():
    r = gate_sm1_report()
    assert r["gate"] == "SM-1"
    assert r["pass"], r["criteria"]
    assert r["discipline"]["no_mass_claim"]
    assert r["discipline"]["premerger_freeze_untouched"]


def test_gate_sm2_structure():
    r = gate_sm2_report()
    assert r["pass"]
    assert r["yukawa_optimized"] is False


def test_gate_sm3_anomaly():
    r = gate_sm3_report()
    assert r["pass"]
    anom = check_anomaly_cancellation()
    assert anom["pass"]


def test_three_generations():
    assert check_three_generations()["pass"]


def test_sm_mode_loss_zero():
    r = sm_mode_loss_knobs()
    assert r["loss"] == 0.0
    assert r["sm1_pass"] and r["sm2_pass"] and r["sm3_pass"]
    assert abs(r["discovered_Wg"] - LOCKED_WG) < 1e-15
