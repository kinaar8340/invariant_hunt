"""CI suite: frozen locks + prediction/report schema validation."""

from __future__ import annotations

import math

from src.ci_checks import (
    KNOWN_SCHEMAS,
    PREDICTION_RECORD_REQUIRED,
    build_sample_prediction_bundle,
    check_known_schema_constants,
    check_lock_residuals,
    run_ci_suite,
    validate_prediction_bundle,
    validate_prediction_record,
    validate_schema_name,
)
from src.invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
)
from src.predictions import gw_echo_delay


def test_schema_name_pattern():
    assert validate_schema_name("invariant_hunt.prediction_bundle.v1")
    assert validate_schema_name("invariant_hunt.action_principle.v2")
    assert validate_schema_name("invariant_hunt.premerger_mapping_v5.v1")
    assert not validate_schema_name("prediction_bundle.v1")
    assert not validate_schema_name("invariant_hunt.foo")
    assert not validate_schema_name("invariant_hunt.foo.v")
    assert not validate_schema_name("")


def test_known_schemas_parse():
    for name, schema in KNOWN_SCHEMAS.items():
        assert validate_schema_name(schema), name


def test_lock_residuals_default():
    r = check_lock_residuals()
    assert r["pass"], r["issues"]
    assert r["is_locked"]
    assert abs(r["locks"]["W_g"] - LOCKED_WG) < 1e-15
    assert abs(r["locks"]["kappa"] - DEFAULT_KAPPA) < 1e-15
    assert abs(r["locks"]["phi_b"] - DEFAULT_BRAIDING) < 1e-15
    assert r["residuals"]["wg_vs_350_over_pi"] == 0.0


def test_lock_residual_detects_drift():
    inv = InvariantSet(wg_base=351.0)
    r = check_lock_residuals(inv)
    assert not r["pass"]
    assert any("wg" in i.lower() or "residual" in i.lower() or "locked" in i.lower()
               for i in r["issues"])


def test_prediction_record_schema():
    rec = gw_echo_delay(mass_solar=30.0, lattice_index=1)
    d = rec.to_dict()
    assert PREDICTION_RECORD_REQUIRED <= set(d.keys())
    v = validate_prediction_record(rec)
    assert v["pass"], v["issues"]
    assert rec.falsify_if
    assert rec.uncertainty > 0
    assert math.isfinite(rec.value)


def test_prediction_bundle_schema():
    bundle = build_sample_prediction_bundle()
    v = validate_prediction_bundle(bundle)
    assert v["pass"], v["issues"]
    assert bundle["schema"] == KNOWN_SCHEMAS["prediction_bundle"]
    assert abs(bundle["canonical_wg"] - LOCKED_WG) < 1e-15
    assert bundle["n_predictions"] >= 1


def test_prediction_bundle_rejects_bad_schema():
    bundle = build_sample_prediction_bundle()
    bundle["schema"] = "not_a_valid_schema"
    v = validate_prediction_bundle(bundle)
    assert not v["pass"]


def test_action_principle_schema_constant():
    r = check_known_schema_constants()
    assert r["pass"], r["issues"]
    assert r["gate_A_P"] is True
    assert r["action_schema"] == KNOWN_SCHEMAS["action_principle"]


def test_run_ci_suite():
    report = run_ci_suite()
    assert report["schema"] == "invariant_hunt.ci_suite.v1"
    assert report["pass"], report
    assert abs(WG_BASE - 350.0) < 1e-15
