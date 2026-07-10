"""
Lightweight CI checks: frozen locks + prediction / report schema hygiene.

No PE data, torch, or pycbc. Safe for GitHub Actions with minimal deps.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .invariants import (
    DEFAULT_BRAIDING,
    DEFAULT_KAPPA,
    DEFAULT_LOCK_TOL,
    LOCKED_WG,
    WG_BASE,
    InvariantSet,
    burst_threshold,
    link_saturation_theta,
)
from .predictions import (
    PredictionRecord,
    gw_burst_spectrum,
    gw_echo_delay,
    write_prediction_bundle,
)

# Canonical absolute tolerances for CI (tight; locks must not drift)
WG_ABS_TOL: float = 1e-12
KAPPA_ABS_TOL: float = 1e-12
BRAIDING_ABS_TOL: float = 1e-12

SCHEMA_RE = re.compile(r"^invariant_hunt\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\.v\d+$")

PREDICTION_RECORD_REQUIRED = frozenset(
    {
        "name",
        "domain",
        "quantity",
        "value",
        "unit",
        "uncertainty",
        "model_version",
        "assumptions",
        "falsify_if",
        "timestamp_utc",
    }
)

PREDICTION_BUNDLE_REQUIRED = frozenset(
    {
        "schema",
        "created_utc",
        "canonical_wg",
        "n_predictions",
        "predictions",
    }
)

# Known schema strings that modules must keep stable
KNOWN_SCHEMAS: dict[str, str] = {
    "prediction_bundle": "invariant_hunt.prediction_bundle.v1",
    "action_principle": "invariant_hunt.action_principle.v2",
    "premerger_mapping_v2": "invariant_hunt.premerger_mapping_v2.v1",
    "premerger_mapping_v3": "invariant_hunt.premerger_mapping_v3.v1",
    "premerger_mapping_v4": "invariant_hunt.premerger_mapping_v4.v1",
    "premerger_mapping_v5": "invariant_hunt.premerger_mapping_v5.v1",
    "integration_status": "invariant_hunt.integration_status.v1",
    "ci_suite": "invariant_hunt.ci_suite.v1",
}


def check_lock_residuals(
    inv: InvariantSet | None = None,
    *,
    tol: float = DEFAULT_LOCK_TOL,
) -> dict[str, Any]:
    """Verify canonical locks and residual magnitudes."""
    inv = inv or InvariantSet()
    residuals = inv.lock_residuals()
    issues: list[str] = []

    if abs(LOCKED_WG - WG_BASE / math.pi) > WG_ABS_TOL:
        issues.append("LOCKED_WG != WG_BASE/π")
    if abs(inv.wg - LOCKED_WG) > WG_ABS_TOL:
        issues.append(f"InvariantSet.wg residual {residuals.get('wg_vs_350_over_pi')}")
    if abs(inv.wg_base - WG_BASE) > WG_ABS_TOL:
        issues.append(f"wg_base residual {residuals.get('wg_base_vs_350')}")
    if abs(inv.kappa - DEFAULT_KAPPA) > KAPPA_ABS_TOL:
        issues.append(f"kappa drift: {inv.kappa} != {DEFAULT_KAPPA}")
    if abs(inv.braiding_target - DEFAULT_BRAIDING) > BRAIDING_ABS_TOL:
        issues.append(
            f"braiding_target drift: {inv.braiding_target} != {DEFAULT_BRAIDING}"
        )
    if not inv.is_locked(tol=tol):
        issues.append("InvariantSet.is_locked() is False at default tolerance")

    # Geometric identities
    th_link = link_saturation_theta(LOCKED_WG)
    if abs(th_link - math.pi) / math.pi > 0.01:
        issues.append(f"Θ_link not near π: {th_link}")
    th_crit = burst_threshold(DEFAULT_KAPPA)
    if abs(th_crit - math.pi * (1.0 + DEFAULT_KAPPA)) > 1e-12:
        issues.append("θ_crit formula mismatch")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "locks": {
            "W_g": LOCKED_WG,
            "wg_base": WG_BASE,
            "kappa": DEFAULT_KAPPA,
            "phi_b": DEFAULT_BRAIDING,
        },
        "residuals": residuals,
        "theta_link": th_link,
        "theta_crit": th_crit,
        "is_locked": inv.is_locked(tol=tol),
    }


def validate_schema_name(schema: str) -> bool:
    """Return True if schema matches invariant_hunt.<segments>.vN."""
    if not isinstance(schema, str):
        return False
    return bool(SCHEMA_RE.match(schema))


def validate_prediction_record(rec: PredictionRecord | dict[str, Any]) -> dict[str, Any]:
    """Structural validation of a PredictionRecord (dict or dataclass)."""
    d = rec.to_dict() if isinstance(rec, PredictionRecord) else dict(rec)
    issues: list[str] = []
    missing = PREDICTION_RECORD_REQUIRED - set(d.keys())
    if missing:
        issues.append(f"missing keys: {sorted(missing)}")
    for key in ("value", "uncertainty"):
        if key in d and not isinstance(d[key], (int, float)):
            issues.append(f"{key} not numeric")
        elif key in d and not math.isfinite(float(d[key])):
            issues.append(f"{key} not finite")
    if "uncertainty" in d and float(d["uncertainty"]) < 0:
        issues.append("uncertainty < 0")
    if not d.get("falsify_if"):
        issues.append("falsify_if empty")
    if not d.get("name"):
        issues.append("name empty")
    if not d.get("domain"):
        issues.append("domain empty")
    if not d.get("quantity"):
        issues.append("quantity empty")
    if not d.get("unit"):
        issues.append("unit empty")
    return {"pass": len(issues) == 0, "issues": issues, "name": d.get("name")}


def validate_prediction_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate write_prediction_bundle JSON payload."""
    issues: list[str] = []
    missing = PREDICTION_BUNDLE_REQUIRED - set(payload.keys())
    if missing:
        issues.append(f"missing bundle keys: {sorted(missing)}")
    schema = payload.get("schema", "")
    if not validate_schema_name(str(schema)):
        issues.append(f"bad schema name: {schema!r}")
    if schema != KNOWN_SCHEMAS["prediction_bundle"]:
        issues.append(
            f"schema != canonical {KNOWN_SCHEMAS['prediction_bundle']}: {schema}"
        )
    if abs(float(payload.get("canonical_wg", -1)) - LOCKED_WG) > WG_ABS_TOL:
        issues.append("canonical_wg does not match LOCKED_WG")
    preds = payload.get("predictions")
    if not isinstance(preds, list):
        issues.append("predictions not a list")
        preds = []
    if int(payload.get("n_predictions", -1)) != len(preds):
        issues.append("n_predictions mismatch")
    rec_issues: list[dict[str, Any]] = []
    for i, p in enumerate(preds):
        vr = validate_prediction_record(p)
        if not vr["pass"]:
            rec_issues.append({"index": i, **vr})
    if rec_issues:
        issues.append(f"{len(rec_issues)} invalid prediction records")
    return {
        "pass": len(issues) == 0 and not rec_issues,
        "issues": issues,
        "record_issues": rec_issues,
        "schema": schema,
        "n_predictions": len(preds),
    }


def check_known_schema_constants() -> dict[str, Any]:
    """Ensure published schema strings remain parseable and listed."""
    issues: list[str] = []
    for key, schema in KNOWN_SCHEMAS.items():
        if not validate_schema_name(schema):
            issues.append(f"{key}: invalid pattern {schema}")
    # Spot-check modules that hardcode schemas
    from .action_principle import action_principle_report

    rep = action_principle_report(n_stability=4, seed=0, include_pde=False)
    if rep.get("schema") != KNOWN_SCHEMAS["action_principle"]:
        issues.append(
            f"action_principle_report schema drift: {rep.get('schema')}"
        )
    if not rep.get("gate_A_P", {}).get("pass"):
        issues.append("action_principle Gate A-P failed in CI check")
    locks = rep.get("locks_frozen") or {}
    if abs(float(locks.get("W_g", -1)) - LOCKED_WG) > WG_ABS_TOL:
        issues.append("action report locks_frozen.W_g drift")
    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "known_schemas": dict(KNOWN_SCHEMAS),
        "action_schema": rep.get("schema"),
        "gate_A_P": rep.get("gate_A_P", {}).get("pass"),
    }


def build_sample_prediction_bundle() -> dict[str, Any]:
    """Build a minimal in-memory prediction bundle for schema tests."""
    import json
    import tempfile
    from pathlib import Path

    recs = [
        gw_echo_delay(mass_solar=30.0, lattice_index=1),
        gw_burst_spectrum(scale_hz=250.0, lattice_index=0),
    ]
    with tempfile.TemporaryDirectory() as td:
        path = write_prediction_bundle(recs, Path(td) / "bundle.json")
        return json.loads(path.read_text(encoding="utf-8"))


def run_ci_suite() -> dict[str, Any]:
    """Run all lightweight CI checks; return combined report."""
    locks = check_lock_residuals()
    schemas = check_known_schema_constants()
    bundle = build_sample_prediction_bundle()
    bundle_v = validate_prediction_bundle(bundle)
    overall = bool(locks["pass"] and schemas["pass"] and bundle_v["pass"])
    return {
        "schema": "invariant_hunt.ci_suite.v1",
        "pass": overall,
        "locks": locks,
        "schemas": schemas,
        "prediction_bundle": bundle_v,
    }
