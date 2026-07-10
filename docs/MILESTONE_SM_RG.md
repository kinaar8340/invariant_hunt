# Milestone: Phase 2.3 SM Gauge RG Flow (Gate SM-3 complete)

**Status:** Gate SM-3 **PASS** (anomaly + one-loop SM RG)  
**Date:** 2026-07-09  
**Phase:** 2.3

## Goal

Complete Gate SM-3 with:

1. **Anomaly cancellation** (already from SM content map)  
2. **Numeric one-loop RG flow** of SM gauge couplings \(g_1,g_2,g_3\) (GUT-normalized)

## Frozen core (unchanged)

| Lock | Role |
|------|------|
| \(W_g=350/\pi\) | Not a free β-function parameter (mild dress only) |
| \(\kappa\approx 0.85\) | Same |
| \(\phi_b^\star\approx 0.8145\) | Same |

Pre-merger freeze untouched. **No unification or gravity claim.**

## One-loop SM β-functions

\[
\frac{\mathrm{d}\,\alpha_i^{-1}}{\mathrm{d}\ln\mu}
= -\frac{b_i}{2\pi},
\qquad
b = \Bigl(\tfrac{41}{10},\, -\tfrac{19}{6},\, -7\Bigr)
\quad (n_g=3,\; n_H=1).
\]

Boundary at \(M_Z\): \(\alpha_{\mathrm{em}}\), \(\sin^2\theta_W\), \(\alpha_s\) → \((\alpha_1,\alpha_2,\alpha_3)\).

## Deliverables

| Item | Path |
|------|------|
| RG library | `src/sm_rg.py` |
| CLI | `scripts/sm_rg_flow.py` |
| Gate SM-3 full | `gate_sm3_full_report` / `sm_gate_check.py` |
| Tests | `tests/test_sm_rg.py` |
| This milestone | `docs/MILESTONE_SM_RG.md` |

## Gate SM-3

```bash
python scripts/sm_rg_flow.py --plot
python scripts/sm_gate_check.py --gates SM-3 --require SM-3
```

| Criterion | Pass |
|-----------|------|
| Anomaly coeffs ≈ 0 per generation | yes |
| SM β coefficients \((41/10,-19/6,-7)\) | yes |
| \(\alpha_s\) asymptotically free | yes |
| No Landau pole on \([M_Z,\,10^{16}\,\mathrm{GeV}]\) (1-loop SM) | yes |
| Round-trip \(M_Z\to 10^{10}\to M_Z\) within tolerances | yes |
| Locks frozen; SM-1 still pass | yes |

Artifact: `outputs/sm_rg/sm_rg_latest.json`.

## What this is *not*

- Not a claim that couplings unify at a single scale  
- Not two-loop / threshold-resummed precision EW  
- Not gravity or emergent \(G_N\) (Phase 3)  
- Not a fit of \(W_g,\kappa,\phi_b\) from running  

## Phase 2 close-out

| Step | Gate | Status |
|------|------|--------|
| 2.1 Representations | SM-1 | PASS |
| 2.2 Yukawa / masses | SM-2 mass | PASS (TIGHT) |
| 2.3 Anomaly + RG | SM-3 | **PASS** |

Next major phase: **Phase 3** (emergent gravity + precision tests), still gated.
