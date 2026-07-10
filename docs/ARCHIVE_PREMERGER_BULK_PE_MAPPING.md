# Archive: Pre-merger bulk PE-power mapping stretch

**Status:** archived  
**Date:** 2026-07-10  
**Close-out:** `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`  
**Mode after archive:** score-only under frozen locks; no new bulk PE-power map without fresh PREREG

## Archival declaration

This document freezes the **pre-merger bulk PE-power mapping** chapter of
invariant_hunt. The campaign was executed under pre-registration, returned
clear FALSIFY (or demotion) on every mild bulk-PE unification claim, and is
now **closed for further stretch** under those forms.

It does **not** archive Phases 1–3 scaffolding, Gate S-1 diagnostics, or the
right to re-score residuals under the locked template.

## Timeline (logical order)

| Step | Artifact | Outcome |
|------|----------|---------|
| Predictive freeze | `docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md` | Core band + SUCCESS/FALSIFY/NULL |
| True held-outs | `docs/MILESTONE_HELD_OUT_TRUE_BBH.md` | 0 SUCCESS / 2 FALSIFY / 1 NULL → band **demoted** |
| Gate S-1 | `docs/MILESTONE_FALSIFY_SYSTEMATICS.md` | GW170809 **ROBUST_ANOMALY**; GW151012 **SYSTEMATICS_RISK** |
| Bayes factor | `docs/PREMERGER_BAYES_FACTOR.md` | \(\ln B_{10}\) machinery; 809 very strong |
| Mapping v2 pre-reg + run | `docs/PREREG_PREMERGER_MAPPING_V2.md`, `docs/MILESTONE_PREMERGER_MAPPING_V2.md` | Mass \(p=1\) **FALSIFY** (\(z\approx 30\)) |
| Mapping v3 pre-reg + run | `docs/PREREG_PREMERGER_MAPPING_V3.md`, `docs/MILESTONE_PREMERGER_MAPPING_V3.md` | Inv-SNR + distance **FALSIFY**; family closed |
| Stretch stop | `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Bulk PE-power family **stopped** |
| **This archive** | (here) | Narrative + repro index frozen |

## Verdict table (canonical)

| Campaign | Form | Verdict | Key number |
|----------|------|---------|------------|
| v1 universal band | Event-independent α | **Demoted** | 0 SUCCESS on true held-outs |
| v2 mass \(p=1\) | \(\beta\propto M_{\mathrm{tot}}\) | **FALSIFY** | \(z\approx 30\) |
| v3a inv-SNR \(q=1\) | \(\beta\propto 1/\rho\) | **FALSIFY** | \(z\approx 21\) |
| v3b distance \(s=1\) | \(\beta\propto d_L\) | **FALSIFY** | \(z\approx 18.5\) |

**Family verdict:** mild bulk PE-power mapping **closed**.

## What is preserved

| Item | Status |
|------|--------|
| \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\) | Frozen |
| Residual channel \(\tau_0\) | Unchanged (score-only OK) |
| GW170809 ROBUST_ANOMALY | Standing; no shared \(\alpha_0\) map |
| GW151012 SYSTEMATICS_RISK | Not a design anchor |
| Demoted v1 band | Historical; not re-fit |
| Phases 1–3 gates | Untouched by this archive |

## Code index (reproducible)

| Path | Role |
|------|------|
| `src/premerger_mapping_v2.py` | Mass-scaled β fit + campaign evaluator |
| `src/premerger_mapping_v3.py` | Inv-SNR / distance fit + family evaluator |
| `scripts/premerger_mapping_v2_score.py` | Execute v2 score |
| `scripts/premerger_mapping_v3_score.py` | Execute v3 score (a then b if a fails) |
| `tests/test_premerger_mapping_v2.py` | Unit tests (no PE) |
| `tests/test_premerger_mapping_v3.py` | Unit tests (no PE) |
| `scripts/premerger_core_predict.py` | Score-only band rule (historical demotion) |
| `scripts/premerger_bayes_factor.py` | \(\ln B_{10}\) |
| `scripts/premerger_falsify_systematics.py` | Gate S-1 |

```bash
python -m pytest tests/test_premerger_mapping_v2.py tests/test_premerger_mapping_v3.py -q
python scripts/premerger_mapping_v2_score.py   # archival re-run OK
python scripts/premerger_mapping_v3_score.py   # archival re-run OK
```

JSON score dumps land under `outputs/mapping_v2/` and `outputs/mapping_v3/`
(gitignored; regenerate locally).

## Operational rules after archive

1. **Do not** open mass / inv-SNR / distance mild-power mapping as a new “fix.”  
2. **Do not** adopt unregistered exponents (e.g. \(d_L^3\)) to hit α ratio ~12.  
3. **Do not** design on GW151012.  
4. **Do** re-score under frozen template for consistency or new BBHs (score-only).  
5. **Do** require a new `docs/PREREG_*.md` naming a **new physical variable** before any mapping v4+.

## What this archive is *not*

- Not a claim that the GW170809 residual is non-physical  
- Not a demotion of Hopf locks  
- Not multi-event discovery  
- Not Phase 4 / arXiv packaging (separate)

## Pointers

| Doc | Role |
|-----|------|
| `docs/PREDICTION_MODE.md` | Active score-only rules |
| `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Decision freeze |
| `ROADMAP.md` | Project status after archive |
