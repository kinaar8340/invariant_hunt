# Milestone: Gate S-1 PE/systematics deep-dive (FALSIFY follow-up)

**Status:** executable  
**Date:** 2026-07-10  
**Priority:** highest after true held-out FALSIFY + large \(B_{10}\)

## Why

GW170809 shows Gate P PASS, huge \(\Delta\chi^2\) / \(\ln B_{10}\), but \(\hat\alpha\)
far **above** the demoted band. That is either:

| (a) | Real but **different** mapping (needs new pre-registration) |
| (b) | Unmodeled **PE residual systematics** absorbed by the linear template |

Gate S-1 decides (a) vs (b) under frozen locks and **no band re-fit**.

## Protocol

```bash
python scripts/premerger_falsify_systematics.py --event GW170809 --plot
python scripts/premerger_falsify_systematics.py --events GW170809,GW151012 --n-draws 12
```

| Probe | Tools reused |
|-------|----------------|
| Multi-approximant | IMRPhenomD, SEOBNRv4_opt, IMRPhenomXAS, IMRPhenomXP |
| PE mass/distance jitter | ±3% mass, ±15% distance |
| PE posterior draws | GWTC-1 draws → α distribution |
| corr(r, τ) | GW170608-style systematics flag (\(\lvert\mathrm{corr}\rvert\gtrsim 0.1\)) |
| Time-cut robustness | \(t_{\mathrm{end}}\in\{-0.2,-0.1,-0.05,-0.02\}\) |
| Bayes factor | \(\ln B_{10}\) per approximant |

## Gate S-1 verdicts

| Verdict | Meaning |
|---------|---------|
| **SYSTEMATICS_RISK** | Fails robustness cuts → prefer systematics/NULL narrative |
| **ROBUST_ANOMALY** | Survives cuts → mapping revision under **new** freeze only |
| **INCONCLUSIVE** | Incomplete or mixed |

Flags include: low approx pass frac, sign flip under mass jitter, high corr(r,τ),
α spread, low posterior-draw pass frac.

## Discipline

- Locks \(W_g,\kappa,\phi_b\) frozen  
- Demoted α band **not** re-fit  
- SYSTEMATICS_RISK does not restore the band as SUCCESS  
- ROBUST_ANOMALY does not auto-open a new template without pre-registration  

Artifact: `outputs/systematics/falsify_systematics_latest.json`.

## GW170809 result (first deep-dive)

| Probe | Outcome |
|-------|---------|
| Approximants (4/4) | Gate P PASS; α ≈ (8.6–9.2)×10^{-4}; ln B ≳ 660 |
| PE jitter (6/6) | PASS; no mass sign flip |
| PE draws (8/8) | PASS; frac(+)=1; mean α ≈ 8.0×10^{-4} |
| corr(r,τ) H1 | 0.37 (**soft** flag only — expected for loud τ projection) |
| **Gate S-1** | **ROBUST_ANOMALY** |

Interpretation: residual preference for the locked template is **not** removed by
approximant/jitter/draws. That strengthens the case for a **different mapping**
(new pre-registration), while the **universal α-band SUCCESS claim stays demoted**
(α remains ≫ band). Soft high corr does not alone reclassify as SYSTEMATICS_RISK
when hard flags are empty.

## Next after S-1

1. If SYSTEMATICS_RISK on FALSIFY events → document; no new mapping.  
2. If ROBUST_ANOMALY → design **new** pre-registered template + freeze cycle.  
3. Run S-1 on GW151012 (sign-FALSIFY) for comparison.  
4. Archival / narrative close-out remains lower urgency.  
