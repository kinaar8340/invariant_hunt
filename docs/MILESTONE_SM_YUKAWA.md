# Milestone: Phase 2.2 Topological Yukawa / Mass Hierarchy (Gate SM-2 upgrade)

**Status:** Gate SM-2 mass **PASS (TIGHT)** on hierarchical + Wolfenstein ansatz  
**Date:** 2026-07-09  
**Phase:** 2.2

## Goal

Upgrade Gate SM-2 from three-generation *structure* to a **topological Yukawa
ansatz** whose free sector parameters are optimized (locks fixed) against PDG
charged-fermion masses and CKM magnitudes.

## Frozen core (unchanged)

| Lock | Role in ansatz |
|------|----------------|
| \(W_g = 350/\pi\) | Mild lock-dressing only; **not** fitted |
| \(\kappa \approx 0.85\) | Mild lock-dressing only; **not** fitted |
| \(\phi_b^\star \approx 0.8145\) | Braiding phase in \(Y_{ij}\) phases/modulation |

Pre-merger freeze untouched.

## Ansatz

**Masses** (braiding-layer hierarchy, \(i=0,1,2\) light→heavy, \(s\in\{u,d,e\}\)):

\[
m_i^{(s)}
= \frac{v}{\sqrt{2}}\, y_s\,
\exp\!\bigl(-\beta_s (2-i)^{p_s}\bigr)\,
\bigl(1+\varepsilon_s\cos(\phi_b^\star+\psi_s i)\bigr),
\quad v\simeq 246.22\,\mathrm{GeV}.
\]

**CKM**: Wolfenstein \((\lambda,A,\bar\rho,\bar\eta)\) with mild \(\phi_b^\star\) dressing
of the complex phase; free Wolfenstein params only (locks not fitted).

**Matrix form** \(Y_{ij}\) with braiding phases retained for documentation / unitarity
checks (not the primary mass path after hierarchical upgrade).

Free parameters: \(\{y_s,\beta_s,p_s,\varepsilon_s,\psi_s\}\) + Wolfenstein set.

## Deliverables

| Item | Path |
|------|------|
| Yukawa library | `src/sm_yukawa.py` |
| CLI | `scripts/sm_yukawa_ansatz.py` |
| Meta hook | `meta_optimize_invariants.py --sm-mode --yukawa` |
| Gate upgrade | `sm_gate_check.py --yukawa` |
| Tests | `tests/test_sm_yukawa.py` |
| This milestone | `docs/MILESTONE_SM_YUKAWA.md` |

## Gate SM-2 (mass/mixing)

```bash
python scripts/sm_yukawa_ansatz.py --sweep --trials 64 --plot
python scripts/meta_optimize_invariants.py --sm-mode --yukawa --trials 64
python scripts/sm_gate_check.py --gates SM-2 --yukawa --trials 48 --require SM-2
```

| Criterion | Pass |
|-----------|------|
| Structure (3 gens) | from SM-1/SM-2 structure |
| SM-1 still pass | representations intact |
| Locks frozen | \(W_g,\kappa,\phi_b\) not free |
| \(\chi^2_{\ln m}/\mathrm{dof}\) | \(\le 9\) (loose) / \(\le 1\) (tight) |
| \(\chi^2_{\|V\|}/\mathrm{dof}\) | \(\le 100\) (loose) / \(\le 25\) (tight) |

**Grades:** `TIGHT` | `LOOSE` | `FAIL`  
**FAIL ⇒ demote this Yukawa ansatz** (not core locks).

Artifacts: `outputs/sm_yukawa/sm_yukawa_latest.json`.

## Honesty note (discipline)

Per-sector free parameters \(\{y_s,\beta_s,p_s\}\) can reproduce three PDG masses
per charged sector **by construction** when \(\varepsilon_s=0\). Gate SM-2 mass is
therefore a test that:

1. The braiding-layer hierarchical *form* + Wolfenstein CKM pipeline runs with
   **locks frozen** and SM-1 intact, and  
2. CKM magnitudes under mild \(\phi_b^\star\) dressing stay within registered \(\chi^2\)
   thresholds.

It is **not** an independent prediction of all masses from \(W_g,\kappa,\phi_b\) alone.
Demote if future constraints force reopening locks or break multi-gate consistency.

## What this is *not*

- Not a claim of unique TOE derivation of all masses from locks alone  
- Not PMNS / neutrino absolute masses (optional later)  
- Not RG running (Phase 2.3)  
- Not gravity  

## Next

Phase **2.3** complete — see `docs/MILESTONE_SM_RG.md`.  
Phase **3**: emergent gravity + precision tests (gated).
