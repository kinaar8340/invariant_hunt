# Milestone: True held-out BBH scorecard (prediction mode)

**Status:** three true held-outs scored; α-band forward claim under stress  
**Date:** 2026-07-10  
**Mode:** score only — **no re-fit** of locks or α band

## Pre-registered rule (frozen)

| Item | Value |
|------|--------|
| Core | GW150914, GW170814 |
| Band | \(\hat\alpha \in [2.88\times10^{-5},\,1.15\times10^{-4}]\) (strictly +) |
| SUCCESS | Gate P PASS, \(\hat\alpha>0\), in band |
| FALSIFY | Gate P PASS outside band **or** wrong sign (negative at significance) |
| NULL | Gate P fail — not a counterexample |

Template: \(\Delta\phi = \alpha\, W_g\, \Phi_{\mathrm{orb}}\, \cos\phi_b\).  
Locks: \(W_g=350/\pi\), \(\kappa\approx0.85\), \(\phi_b\approx0.8145\) — **unchanged**.

## True held-out set

Events **not** used in freeze demotion / in-catalog NULL training:

| Event | SNR (approx) | Role |
|-------|--------------|------|
| GW170809 | ~12.4 | Preferred first score |
| GW170729 | ~10.8 | Heavy |
| GW151012 | ~9.7 | Lighter |

## Scorecard

| Event | \(\hat\alpha\) | \(\sigma_\alpha\) | \(\Delta\chi^2\) | Gate P | In band | **Verdict** |
|-------|----------------|-------------------|------------------|--------|---------|-------------|
| GW170809 | \(+8.58\times10^{-4}\) | \(2.35\times10^{-5}\) | 1338 | **PASS** | No (≫ upper) | **FALSIFY** |
| GW170729 | \(+7.58\times10^{-5}\) | \(4.76\times10^{-5}\) | 2.54 | **fail** | Yes* | **NULL** |
| GW151012 | \(-7.96\times10^{-5}\) | \(2.69\times10^{-5}\) | 8.78 | **PASS** | No (sign −) | **FALSIFY** |

\*In-band α is irrelevant for NULL when Gate P fails.

### Tally

| Verdict | Count | Events |
|---------|-------|--------|
| SUCCESS | **0** | — |
| FALSIFY | **2** | GW170809, GW151012 |
| NULL | **1** | GW170729 |

```bash
python scripts/premerger_core_predict.py --predict-event GW170809
python scripts/premerger_core_predict.py --predict-event GW170729
python scripts/premerger_core_predict.py --predict-event GW151012
```

Artifact (last run overwrites): `outputs/predictions/premerger_core_prediction.json`.

## Interpretation (discipline)

1. **Forward α-band universality** under this template + IMRPhenomD median PE + Gate P quality cuts is **falsified** by two independent true held-outs (over-large positive α; significant negative α).  
2. **NULL** on GW170729 is consistent with “not every BBH is a core-quality Gate P event” — not SUCCESS and not a free pass.  
3. **Do not** widen the band or flip signs post hoc to manufacture SUCCESS.  
4. Core topological locks \(W_g,\kappa,\phi_b\) are **not** automatically demoted; the pre-merger **mapping / predictive criterion** is demoted as a universal forward claim.  
5. Phases 1–3 scaffolding (A-P, SM-*, GR-*) remain separate mathematical gates — they do not rescue the α-band claim.

## Allowed next steps (gated)

| Action | Allowed? |
|--------|----------|
| Re-fit α band on held-outs | **No** |
| Re-fit \(W_g,\kappa,\phi_b\) from GW α | **No** (without independent meta/analytic work) |
| Document FALSIFY + demote universal band claim | **Yes** |
| PE/systematics scrutiny (corr(r,τ), approximant) on FALSIFY events | **Yes** (may reclassify to NULL if systematics) |
| New template mapping (different phase form) under new pre-registration | **Yes** (new freeze cycle) |
| Score further true held-outs (GWTC-2/3) with **same** band | **Yes** (more FALSIFY/NULL evidence) |

## Demotion statement

> The pre-registered pre-merger predictive freeze **forward band** is demoted as a  
> universal SUCCESS criterion for new BBHs. Evidence: 0/3 SUCCESS, 2 FALSIFY,  
> 1 NULL on true held-outs. Core locks and Phases 1–3 scaffolds are not reopened  
> by this demotion alone.

## Gate S-1 follow-up (PE systematics)

| Event | S-1 verdict | Implication |
|-------|-------------|-------------|
| GW170809 | ROBUST_ANOMALY | Large +α not killed by multi-approx/jitter/draws |
| GW151012 | ROBUST_ANOMALY | −α mostly stable; SEOBNR weak; BF marginal |

Opposite signs under ROBUST_ANOMALY ⇒ single universal α is untenable; any
revision needs a **new pre-registration**, not band widening.

## Related

- `docs/PREDICTION_MODE.md`  
- `docs/MILESTONE_HELD_OUT_GW170809.md`  
- `docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md`  
