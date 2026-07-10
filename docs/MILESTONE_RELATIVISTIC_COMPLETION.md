# Milestone: Phase 1.3 Relativistic Completion Paper

**Status:** peer-ready `.tex` scaffold complete  
**Date:** 2026-07-09  
**Phase:** 1.3

## Goal

Publish-ready equations for the relativistic lift of the free-energy / conduit theory,
**aligned with** Phase 1.1 `eq:unified-action` and Gate A-P / H-S discipline.

## Deliverable

| Item | Path |
|------|------|
| Relativistic completion (LaTeX) | `papers/Relativistic_Completion.tex` |
| Cross-linked Lagrangian | `papers/Lagrangian_Derivation.tex` |
| Symbolic densities | `src/action_principle.py` |

## Alignment checklist

| Sector | Label | Matches Lagrangian / code |
|--------|-------|---------------------------|
| Unified action | `eq:unified-action` | yes |
| \(S_\sigma\) | `eq:sigma` | yes |
| Skyrme | `eq:skyrme` | yes |
| YM SU(3)×SU(2)×U(1) | `eq:ym` | yes |
| Hopf | `eq:hopf` | yes |
| Holonomy + braiding | `eq:hol` | yes |
| Drive / burst | `eq:drive`, `eq:burst` | yes |
| Gravity scaffold | `eq:grav` | yes (Phase 3 claim deferred) |
| Conduit limit | `eq:conduit` | yes (+ optional \(J_{\mathrm{gauge}}\)) |
| Path integral outline | `eq:path-int` | yes (Phase 4 gate) |
| \(G_N\) schema | `eq:GN-schema` | **target only** — not a precision claim |

## Gates referenced in paper

```bash
python scripts/action_principle_check.py          # Gate A-P
python scripts/meta_optimize_invariants.py --locks-fixed --dry-run --trials 40  # Gate H-S
python scripts/premerger_core_predict.py          # independent freeze
```

## Discipline

- Locks frozen; no reopening of pre-merger freeze  
- QED/GR low-energy limits labeled **provisional / Phase 2–3**  
- Historical \(\alpha\), \(m_e\) identifications demoted to notes until mass/mixing gates  

## Phase 1 close-out

| Step | Status |
|------|--------|
| 1.1 Unified action + Gate A-P | done |
| 1.2 Locks-fixed meta-sweep + Gate H-S | done |
| 1.3 Relativistic Completion `.tex` | **this milestone** |

Next major phase: **Phase 2** (SM spectrum map) — only after continuing discipline on locks and gates.
