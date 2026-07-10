# Milestone: CI for locks + prediction schema

**Status:** complete  
**Date:** 2026-07-10  

## Goal

Automate residual checks on frozen core locks and structural validation of
prediction / report schemas — without PE downloads, torch, or pycbc.

## Deliverables

| Path | Role |
|------|------|
| `src/ci_checks.py` | Lock residuals, schema name pattern, prediction bundle validation |
| `scripts/ci_check.py` | CLI + optional CI pytest subset |
| `tests/test_ci_locks_schema.py` | Unit tests for the suite |
| `requirements-ci.txt` | Minimal CI deps |
| `.github/workflows/ci.yml` | GitHub Actions on push/PR to `main` |

## What is checked

1. **Locks:** \(W_g=350/\pi\), \(\kappa\), \(\phi_b\); residual zero at canonical set  
2. **Schema names:** `invariant_hunt.<segments>.vN`  
3. **PredictionRecord / prediction_bundle.v1** structure + non-empty `falsify_if`  
4. **Action-principle report** schema `v2` and Gate A-P pass (no PDE suite)  
5. **Pytest subset** of pure-unit modules (mappings v2–v5 scaffolding, SM, gravity, …)

## Local run

```bash
pip install -r requirements-ci.txt
pip install -e .
python scripts/ci_check.py          # locks + schema only
python scripts/ci_check.py --pytest # + unit subset
```

## Not in CI (by design)

- PE residual / whitened network / full GWOSC runs  
- pycbc / torch conduit epochs  
- arXiv PDF build  

## Discipline

CI failure on lock drift is a **hard stop** — do not “fix” by widening
`LOCKED_WG` without a theory process and explicit milestone.
