# Archive: Pre-merger mapping stretch (v1–v5)

**Status:** archived  
**Date:** 2026-07-10  
**Close-out:** `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`  
**Mode after archive:** score-only under frozen locks; no new map without fresh PREREG  
**Scope:** mapping campaigns **v1–v5** fully closed

## Archival declaration

This document freezes the **pre-merger mapping stretch** of invariant_hunt
(campaigns **v1–v5**): bulk PE-power, remnant-mass, and Hopf-lattice geometric
\(\Lambda\). Every campaign was executed under pre-registration and returned a
clear FALSIFY (or demotion) on shared-\(\alpha_0\) unification. The stretch is
**closed for further work** under those forms.

It does **not** archive Phases 1–3 scaffolding, Gate S-1 diagnostics, or the
right to re-score residuals under the locked template. It does **not** demote
core locks \(W_g\), \(\kappa\), \(\phi_b\).

## Timeline (logical order)

| Step | Artifact | Outcome |
|------|----------|---------|
| Predictive freeze | `docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md` | Core band + SUCCESS/FALSIFY/NULL |
| True held-outs | `docs/MILESTONE_HELD_OUT_TRUE_BBH.md` | 0 SUCCESS / 2 FALSIFY / 1 NULL → band **demoted** |
| Gate S-1 | `docs/MILESTONE_FALSIFY_SYSTEMATICS.md` | GW170809 **ROBUST_ANOMALY**; GW151012 **SYSTEMATICS_RISK** |
| Bayes factor | `docs/PREMERGER_BAYES_FACTOR.md` | \(\ln B_{10}\) machinery; 809 very strong |
| Mapping v2 | `docs/PREREG_PREMERGER_MAPPING_V2.md`, `docs/MILESTONE_PREMERGER_MAPPING_V2.md` | Mass \(p=1\) **FALSIFY** (\(z\approx 30\)) |
| Mapping v3 | `docs/PREREG_PREMERGER_MAPPING_V3.md`, `docs/MILESTONE_PREMERGER_MAPPING_V3.md` | Inv-SNR + distance **FALSIFY** |
| Mapping v4 | `docs/PREREG_PREMERGER_MAPPING_V4.md`, `docs/MILESTONE_PREMERGER_MAPPING_V4.md` | Remnant \(M_f\) **FALSIFY** (\(z\approx 30.6\)) |
| Mapping v5 | `docs/PREREG_PREMERGER_MAPPING_V5.md`, `docs/MILESTONE_PREMERGER_MAPPING_V5.md` | Hopf \(\Lambda\) **FALSIFY** (\(z\approx 28.5\)) |
| Full close-out v1–v5 | `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Stretch **fully closed** |
| **This archive** | (here) | Narrative + repro index frozen |

## Verdict table (canonical)

| Campaign | Form | Verdict | Key number |
|----------|------|---------|------------|
| v1 universal band | Event-independent α | **Demoted** | 0 SUCCESS on true held-outs |
| v2 mass \(p=1\) | \(\beta\propto M_{\mathrm{tot}}\) | **FALSIFY** | \(z\approx 30\) |
| v3a inv-SNR \(q=1\) | \(\beta\propto 1/\rho\) | **FALSIFY** | \(z\approx 21\) |
| v3b distance \(s=1\) | \(\beta\propto d_L\) | **FALSIFY** | \(z\approx 18.5\) |
| v4 remnant \(p=1\) | \(\beta\propto M_f^{+1}\) | **FALSIFY** | \(z\approx 30.6\); scale ~0.89 wrong way |
| v5 Hopf \(\Lambda\) | \(\Lambda=(\Theta_{\mathrm{link}}/\pi)(M_{f,\mathrm{ref}}/M_f)\) | **FALSIFY** | \(z\approx 28.5\); scale ~1.12 |

**Family verdict:** pre-merger mapping stretch **v1–v5 fully closed**.  
GW170809 remains a residual **ROBUST_ANOMALY** without a shared \(\alpha_0\) map
from any tested family.

## What is preserved

| Item | Status |
|------|--------|
| \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\) | Frozen |
| Residual channel \(\tau_0\) | Unchanged (score-only OK) |
| GW170809 ROBUST_ANOMALY | Standing; no shared \(\alpha_0\) from v1–v5 |
| GW151012 SYSTEMATICS_RISK | Not a design anchor |
| Demoted v1 band | Historical; not re-fit |
| Phases 1–3 gates | Untouched by this archive |

## Code index (reproducible)

| Path | Role |
|------|------|
| `src/premerger_mapping_v2.py` | Mass-scaled β fit + campaign evaluator |
| `src/premerger_mapping_v3.py` | Inv-SNR / distance fit + family evaluator |
| `src/premerger_mapping_v4.py` | Remnant-mass fit + campaign evaluator |
| `src/premerger_mapping_v5.py` | Hopf-\(\Lambda\) fit + campaign evaluator |
| `scripts/premerger_mapping_v2_score.py` | Execute v2 score |
| `scripts/premerger_mapping_v3_score.py` | Execute v3 score |
| `scripts/premerger_mapping_v4_score.py` | Execute v4 score |
| `scripts/premerger_mapping_v5_score.py` | Execute v5 score |
| `tests/test_premerger_mapping_v2.py` | Unit tests (no PE) |
| `tests/test_premerger_mapping_v3.py` | Unit tests (no PE) |
| `tests/test_premerger_mapping_v4.py` | Unit tests (no PE) |
| `tests/test_premerger_mapping_v5.py` | Unit tests (no PE) |
| `scripts/premerger_core_predict.py` | Score-only band rule (historical demotion) |
| `scripts/premerger_bayes_factor.py` | \(\ln B_{10}\) |
| `scripts/premerger_falsify_systematics.py` | Gate S-1 |

```bash
python -m pytest tests/test_premerger_mapping_v{2,3,4,5}.py -q
python scripts/premerger_mapping_v2_score.py   # archival re-run OK
python scripts/premerger_mapping_v3_score.py
python scripts/premerger_mapping_v4_score.py
python scripts/premerger_mapping_v5_score.py
```

JSON score dumps land under `outputs/mapping_v{2,3,4,5}/`
(gitignored; regenerate locally).

## Operational rules after archive

1. **Do not** re-open mass / inv-SNR / distance / remnant / closed Hopf-\(\Lambda\) mapping as a new “fix.”  
2. **Do not** adopt unregistered exponents (e.g. \(d_L^3\)) to hit α ratio ~12.  
3. **Do not** design on GW151012.  
4. **Do** re-score under frozen template for consistency or new BBHs (score-only).  
5. **Do** require a new `docs/PREREG_*.md` naming a **genuinely new physical variable** before any further mapping.

## What this archive is *not*

- Not a claim that the GW170809 residual is non-physical  
- Not a demotion of Hopf locks or \(\Theta_{\mathrm{link}}\) as lattice structure  
- Not multi-event discovery  
- Not Phase 4 / arXiv packaging (separate)

## Pointers

| Doc | Role |
|-----|------|
| `docs/PREDICTION_MODE.md` | Active score-only rules |
| `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Decision freeze (v1–v5) |
| `ROADMAP.md` | Project status after archive |
