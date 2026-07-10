# Milestone: Pre-merger predictive freeze

**Status:** frozen predictive criterion (in-catalog campaign closed)  
**Date:** 2026-07-09

## What is frozen

After PE draws, B-P injection, approximant/mass scrutiny, and core lock, the
pre-merger phase campaign is closed at a **forward prediction rule**, not a
detection claim.

| Item | Locked value |
|------|----------------|
| Template | \(\Delta\phi = \alpha \cdot W_g \cdot \Phi_{\mathrm{orb}} \cdot \cos(\phi_b)\) |
| Core locks | \(W_g = 350/\pi\), \(\kappa \approx 0.85\), \(\phi_b \approx 0.8145\) |
| Credible core | **GW150914**, **GW170814** only |
| Median PE \(\hat\alpha\) | \(\sim (7\text{–}8)\times 10^{-5}\) (positive) |
| Forward band (3×width) | \(\hat\alpha \in [2.88\times 10^{-5},\, 1.15\times 10^{-4}]\) |

### Demotions (do not reopen without new evidence)

| Event | Reason |
|-------|--------|
| GW170608 | High corr(r, τ); approximant \(\Delta\chi^2\) swing; mass +3% sign flip |
| GW170818 | PE posterior draws only 4/8 Gate P |

In-catalog NULL / fail: GW170104, GW151226, GW170823 (Gate P fail — not falsifying).

## Pre-registered scoring rule

```bash
python scripts/premerger_core_predict.py
python scripts/premerger_core_predict.py --predict-event <NEW_BBH>
```

| Verdict | Condition |
|---------|-----------|
| **SUCCESS** | Gate P PASS, \(\hat\alpha > 0\), and \(\hat\alpha\) inside the band |
| **FALSIFY** | Gate P PASS with \(\hat\alpha\) outside the band, or significantly negative |
| **NULL** | Gate P fail (sign inconsistency / weak α) — **not** a counterexample |

Quality cuts: H1+L1 present; network Gate P (incl. same-sign rule); IMRPhenomD median PE unless otherwise stated.

Artifact: `outputs/predictions/premerger_core_prediction.json`.

## Evidence stack (summary)

| Check | Core (150914, 814) | Notes |
|-------|--------------------|-------|
| Gate P | PASS | Same-sign H1/L1 |
| PE draws | 9/10, 7/8 | Stable under posterior sampling |
| Gate B-P | noise FP clean | Real α near thr on 814; low corr(r,τ) |
| Mass-scale β | tight on core | No claim of mass-universal β beyond core |
| Meta dry-run | \(w_{g,\mathrm{base}}\to 350\) | Sanity; locks already fixed |

Supporting milestones: `MILESTONE_PREMERGER_FOLLOWUP.md`, `MILESTONE_GW170608_SCRUTINY.md`, `PREMERGER_PHASE.md`.

## What this is *not*

- Not a claim that \(\alpha\) is a confirmed astrophysical coupling.  
- Not a revival of O(1) post-merger residual ladders (sync branch still predicts \(\sim 10^{-6}\)).  
- Not a license to re-promote demoted events without new PE-systematics checks.

## Reopen only if

1. A **true held-out** BBH (not used in demotion/NULL above) is scored with
   `premerger_core_predict.py` → SUCCESS or FALSIFY.  
2. Quiet post-merger matched filter at \(f_{\mathrm{phys}}(M)\) (roadmap “later”).  
3. New PE/data products change corr(r, τ) or approximant stability on a demoted event.

Until then: **stop here** — clean predictive criterion is the deliverable.

---

## Prediction-mode updates (post Phase 3 close-out)

True held-outs: **GW151012**, **GW170729**, **GW170809** (`docs/PREDICTION_MODE.md`).

| Event | Verdict | Notes |
|-------|---------|--------|
| GW170823 | NULL | In-catalog reaffirmation |
| GW170809 | **FALSIFY** | Gate P PASS; α ≫ band upper |
| GW170729 | **NULL** | Gate P fail; α near core but not PASS |
| GW151012 | **FALSIFY** | Gate P PASS; α negative |

**Tally: 0 SUCCESS / 2 FALSIFY / 1 NULL → forward α-band claim demoted.**  
**Do not re-fit the band.** Scorecard: `docs/MILESTONE_HELD_OUT_TRUE_BBH.md`.
