# Milestone: Phase 1.2 Locks-Fixed Holonomy / Gauge Meta-Sweep

**Status:** Gate H-S executable  
**Date:** 2026-07-09  
**Phase:** 1.2 (holonomy / braiding stability under gauged perturbations)

## Goal

Demonstrate that frozen core locks

\[
W_g = 350/\pi,\quad \kappa^\star \approx 0.85,\quad \phi_b^\star \approx 0.8145
\]

remain intact when holonomy *probes* and gauge knobs

\[
g_3,\; g_2,\; g_1,\; D,\; c_H,\; J_{\mathrm{gauge}},\; \kappa_{\mathrm{scale}}
\]

are swept. Locks are **not** free Optuna parameters in this mode.

## Deliverables

| Item | Path | Status |
|------|------|--------|
| Sweep library | `src/gauged_meta_sweep.py` | done |
| CLI integration | `scripts/meta_optimize_invariants.py --locks-fixed` | done |
| Tests | `tests/test_gauged_meta_sweep.py` | done |
| This milestone | `docs/MILESTONE_GAUGED_META_SWEEP.md` | done |

## Gate H-S (holonomy / gauge stability)

```bash
# Optuna over gauge knobs (locks frozen)
python scripts/meta_optimize_invariants.py --locks-fixed --dry-run --trials 40

# Monte Carlo sample
python scripts/meta_optimize_invariants.py --locks-fixed --monte-carlo --samples 64

# Optional short PDE probe in loss
python scripts/meta_optimize_invariants.py --locks-fixed --monte-carlo --samples 32 --pde-probe
```

| Criterion | Pass |
|-----------|------|
| \(W_g\) residual | \(\max \|W_g - 350/\pi\| = 0\) |
| Ghost-free fraction | \(= 1\) over sampled band |
| Holonomy restoring | eigenvalue \(-\kappa_{\mathrm{eff}} < 0\) for all trials |
| Braiding pin | minimum at \(\phi_b^\star\) for all trials |
| Loss | finite and \(< 10^3\) (no explosion) |

Artifact: `outputs/meta_optimize/meta_optimize_locks_fixed_latest.json`.

## What is free vs frozen

| Frozen | Free (jitter / sweep) |
|--------|------------------------|
| `wg_base = 350` | `g3, g2, g1` |
| \(\phi_b^\star\) | `D`, `hopf_coupling` |
| nominal \(\kappa^\star\) | `gauge_flux`, `kappa_scale` probe |

`kappa_scale` multiplies \(\kappa^\star\) for *stability probing only* — it does not redefine the lock or re-open free search over \(\kappa\).

## What this is *not*

- Not re-fitting \(W_g\), \(\kappa\), or \(\phi_b\) from data  
- Not Phase 2 SM spectrum / running couplings  
- Not a claim that default \(g_i=1\) are physical SM values  

## Relation to Gate A-P

Gate A-P (Phase 1.1) is symbolic / single-point health of the action.  
Gate H-S is multi-sample stability of locks under gauged knobs (meta-sweep).

Both must pass before promoting new gauge/Hopf deformations.

## Next

- **1.3** Relativistic Completion `.tex` aligned with `eq:unified-action`  
- Keep `premerger_core_predict.py` for held-out BBHs  
