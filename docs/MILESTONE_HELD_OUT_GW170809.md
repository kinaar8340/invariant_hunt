# Milestone: True held-out score — GW170809

**Status:** scored under pre-merger predictive freeze  
**Date:** 2026-07-10  
**Mode:** prediction only (no re-fit of locks or α band)

## Event class

**True held-out BBH** — not in freeze core, demotion list, or in-catalog NULL set  
(GW151012 / GW170729 / GW170809 registered for prediction mode).

## Pre-registered rule (unchanged)

| Item | Value |
|------|--------|
| Core | GW150914, GW170814 |
| Band | \(\hat\alpha \in [2.88\times10^{-5},\,1.15\times10^{-4}]\) |
| SUCCESS | Gate P PASS, \(\hat\alpha>0\), in band |
| FALSIFY | Gate P PASS outside band or strongly negative |
| NULL | Gate P fail |

```bash
python scripts/premerger_core_predict.py --predict-event GW170809
```

## Result

| Quantity | Value |
|----------|--------|
| \(\hat\alpha\) | \(8.58\times10^{-4} \pm 2.35\times10^{-5}\) |
| \(\Delta\chi^2\) | 1338.07 |
| Gate P | **PASS** |
| In band? | **No** (\(\hat\alpha \gg 1.15\times10^{-4}\)) |
| **Verdict** | **FALSIFY** |

Artifact: `outputs/predictions/premerger_core_prediction.json`.

## Discipline interpretation

- **FALSIFY** applies to the **pre-registered forward α-band claim** for new BBHs under this template and quality cuts — **not** an automatic demotion of core topological locks \(W_g\), \(\kappa\), \(\phi_b\).  
- Do **not** widen the band post hoc to absorb GW170809.  
- Allowed responses (gated): revise pre-merger **mapping** (template, PE systematics, quality cuts), demote “universal α band,” or require multi-held-out corroboration before reopening freeze.  
- Phases 1–3 scaffolding gates (A-P, SM-*, GR-*) remain separate; they are not reopened by this score.

## Full true held-out set (scored)

| Event | Verdict |
|-------|---------|
| GW170809 | **FALSIFY** (this milestone) |
| GW170729 | **NULL** (Gate P fail) |
| GW151012 | **FALSIFY** (Gate P PASS, negative α) |

See `docs/MILESTONE_HELD_OUT_TRUE_BBH.md` for the joint scorecard and demotion statement.

## What this is *not*

- Not a re-fit of \(W_g\) or the freeze band  
- Not a claim that α is confirmed physics (band already under stress)  
- Not a license to ignore Gate P quality systematics on large \(\Delta\chi^2\)  
