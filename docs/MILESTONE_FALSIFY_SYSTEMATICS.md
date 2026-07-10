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
| PE posterior draws | GWTC-1 draws → α distribution (**use n_draws≥12** for S-1 claims) |
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

## GW151012 result (sign − FALSIFY) — draw-count sensitive

```bash
# Canonical (more thorough PE draws):
python scripts/premerger_falsify_systematics.py --events GW170809,GW151012 --n-draws 12
# Shorter run can flip verdict (under-powered draws):
python scripts/premerger_falsify_systematics.py --event GW151012 --n-draws 8 --plot
```

| Probe | Outcome |
|-------|---------|
| Approximants | **3/4** Gate P PASS (SEOBNRv4_opt **fail**, Δχ²=3.45); α ≈ (−4.6…−8.0)×10^{-5} |
| ln B_10 | Mixed: +0.8 / −2.0 / +0.7 / −0.3 (not “very_strong”) |
| PE jitter (6/6) | PASS; α stays **negative**; mass jitter deepens |α| |
| PE draws **n=8** | 7/8 PASS → **ROBUST_ANOMALY** (earlier run; under-powered) |
| PE draws **n=12** (canonical) | **5/12 PASS (frac=0.42)** → hard flag `posterior_draw_pass_frac_low` |
| corr(r,τ) | |corr| ≲ 0.02 (low) |
| **Gate S-1 (canonical n=12)** | **SYSTEMATICS_RISK** |

### Joint reading (canonical)

| Event | Sign | |α| vs band | BF | S-1 (n_draws≥12) |
|-------|------|------------|-----|------------------|
| GW170809 | **+** | ≫ upper | huge | **ROBUST_ANOMALY** |
| GW151012 | **−** | wrong sign | marginal | **SYSTEMATICS_RISK** |
| GW170729 | + (near band) | — | favors GR | Gate P **NULL** |

Interpretation:

1. **Universal positive band** remains **demoted**.  
2. **GW170809** is the only held-out with **stable** multi-approx + PE-draw residual preference (still not a band SUCCESS).  
3. **GW151012** fails S-1 under thorough PE draws → prefer **systematics / unstable α** narrative; do **not** use it as a second robust anomaly for a new mapping.  
4. n=8 vs n=12 on GW151012 shows PE-draw variance — **n_draws≥12 is required** for S-1 claims on marginal events.  
5. New pre-registered mapping is **not** justified by a dual robust pair; only GW170809 is ROBUST_ANOMALY.

## Next after S-1

1. ~~S-1 on GW170809~~ → ROBUST_ANOMALY (stable)  
2. ~~S-1 on GW151012~~ → **SYSTEMATICS_RISK** at n_draws=12 (canonical)  
3. Optional: more PE draws / systematics on GW170809 only before any new mapping design  
4. **Do not** open a dual-sign “robust pair” mapping narrative  
5. Archival / narrative close-out  
