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

## GW170809 result (strong +α FALSIFY)

| Probe | Outcome |
|-------|---------|
| Approximants (4/4) | Gate P PASS; α ≈ (8.6–9.2)×10^{-4}; ln B ≳ 660 |
| PE jitter (6/6) | PASS; no mass sign flip |
| PE draws (8/8) | PASS; frac(+)=1; mean α ≈ 8.0×10^{-4} |
| corr(r,τ) H1 | 0.37 (**soft** flag only — expected for loud τ projection) |
| **Gate S-1** | **ROBUST_ANOMALY** |

## GW151012 result (sign − FALSIFY)

```bash
python scripts/premerger_falsify_systematics.py --event GW151012 --n-draws 8 --plot
```

| Probe | Outcome |
|-------|---------|
| Approximants | **3/4** Gate P PASS (SEOBNRv4_opt **fail**, Δχ²=3.45); α ≈ (−4.6…−8.0)×10^{-5} |
| ln B_10 | Mixed: +0.8 / −2.0 / +0.7 / −0.3 (not “very_strong”) |
| PE jitter (6/6) | PASS; α stays **negative**; mass jitter deepens |α| |
| PE draws | 7/8 PASS; mean α ≈ −1.1×10^{-4}; frac(+)=0.25 |
| corr(r,τ) | |corr| ≲ 0.02 (low) |
| **Gate S-1** | **ROBUST_ANOMALY** (hard flags empty; majority approx + jitter + draws) |

### Joint reading (both FALSIFY events)

| Event | Sign | |α| vs band | BF | S-1 |
|-------|------|------------|-----|-----|
| GW170809 | **+** | ≫ upper | huge | ROBUST_ANOMALY |
| GW151012 | **−** | wrong sign | marginal | ROBUST_ANOMALY |
| GW170729 | + (near band) | — | favors GR | Gate P **NULL** (no S-1 needed) |

Interpretation:

1. **Universal positive band** remains **demoted** (opposite signs on two robust held-outs).  
2. Residual–τ coupling is **not** wiped by PE approximant/jitter alone on either FALSIFY.  
3. The two robust anomalies **disagree in sign** → argues against a single universal α, and against treating either as SUCCESS.  
4. Next mapping (if any) must be a **new pre-registered** form; soft SEOBNR weakness on GW151012 is a caveat for that design.

## Next after S-1

1. ~~S-1 on GW170809~~ → ROBUST_ANOMALY  
2. ~~S-1 on GW151012~~ → ROBUST_ANOMALY (negative α)  
3. **New pre-registered mapping** only if designed to handle sign structure / not revive demoted band  
4. Archival / narrative close-out  
