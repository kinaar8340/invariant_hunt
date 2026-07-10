# Milestone: Pre-merger mapping v2 (mass-scaled β)

**Status:** executed — campaign **FALSIFY**  
**Date:** 2026-07-10  
**Pre-reg:** `docs/PREREG_PREMERGER_MAPPING_V2.md`  
**Artifact:** `outputs/mapping_v2/mapping_v2_latest.json`

## What was tested

Frozen locks \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\).  
Single free amplitude \(\alpha_0\sim\mathcal{N}(0,10^{-3})\).  
Primary form (**p=1 fixed a priori**):

\[
\beta = \alpha_0 \left(\frac{M_{\mathrm{tot}}}{60\,M_\odot}\right)^{1},\qquad
\tau_{v2}=\tau_0\cdot\frac{M_{\mathrm{tot}}}{60\,M_\odot},\qquad
r \approx \alpha_0\,\tau_{v2}
\]

with \(\tau_0 = -W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\) (same residual channel as v1).  
GW151012 scored only as systematics check — **not** a design anchor.

## Pre-run honesty (logged before scores)

| Quantity | Value |
|----------|--------|
| Mass β ratio if shared \(\alpha_0\) (p=1) | ≈ 0.89 |
| Empirical v1 \(\alpha_{809}/\alpha_{914}\) | ≈ 12.4 |
| Implication | Mass-only scaling predicts \(\mathcal{O}(1)\) ratio, not ~12 |

## Per-event results (IMRPhenomD PE median, H1+L1)

| Event | \(M_{\mathrm{tot}}\) | scale | \(\hat\alpha_0\) | \(\beta_{\mathrm{eff}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | P-v2 |
|-------|----------------------|-------|------------------|--------------------------|------------------|----------------|------|
| GW150914 | 72.38 | 1.206 | \(5.74\times10^{-5}\) | \(6.93\times10^{-5}\) | 30.4 | +10.6 | PASS |
| GW170814 | 62.60 | 1.043 | \(7.14\times10^{-5}\) | \(7.45\times10^{-5}\) | 16.0 | +4.0 | PASS |
| **GW170809** | 70.65 | 1.177 | \(7.29\times10^{-4}\) | \(8.58\times10^{-4}\) | 1338 | +665 | PASS |
| GW151012† | 44.69 | 0.745 | \(-1.07\times10^{-4}\) | \(-7.96\times10^{-5}\) | 8.8 | +1.1 | PASS |
| GW170729 | 125.7 | 2.095 | \(3.62\times10^{-5}\) | \(7.58\times10^{-5}\) | 2.5 | −2.5 | fail |

† Systematics-risk event; not used for SUCCESS.

Note: \(\beta_{\mathrm{eff}}=\hat\alpha_{v1}\) by construction (scale absorbed into \(\tau\)); v2 changes the **shared-\(\alpha_0\)** claim, not residual \(\Delta\chi^2\).

## Campaign verdict

| Check | Result |
|-------|--------|
| GW170809 P-v2 | **PASS** |
| GW170809 \(\ln B_{10}>5\) | **PASS** (+665) |
| Shared \(\alpha_0\): \(z(\alpha_0^{809}-\alpha_0^{914})\) | **29.86** ≫ 3 |
| \(\beta_{\mathrm{eff}}\) ratio 809/914 | **12.38** vs mass-scale ratio **0.98** |

**Verdict: FALSIFY** — GW170809 is residual-strong under the frozen template, but mass-only \(p=1\) does **not** unify \(\alpha_0\) with the core. Pre-registered allowed failure of the mass-scaling hypothesis.

```text
CAMPAIGN VERDICT: FALSIFY
  GW170809 residual-strong but α_0 not shared with core (z=29.86>3)
  — mass-only p=1 scaling fails unification
```

## Interpretation (discipline)

1. **Core locks not reopened.** FALSIFY applies to the **mass-scaled coupling claim**, not \(W_g,\kappa,\phi_b\).  
2. **v1 universal band remains demoted.** v2 does not restore it.  
3. **GW170809 residual remains a robust anomaly** under S-1 / Gate P / BF; mapping still does not explain *why* \(\alpha\) is ~12× core.  
4. **p=2 cannot fix this either** without floating something else: even \(p\sim \ln(12)/\ln(M_{809}/M_{914})\) is ill-conditioned (masses are *closer* for 809 vs 914 in PE totals used here, ratio ~0.98), so pure \(M_{\mathrm{tot}}^p\) cannot produce ratio ~12.  
5. **Do not** design next mapping on GW151012 (SYSTEMATICS_RISK).  
6. **Secondary grid** \(p\in\{0,1,2\}\) is sensitivity only; it cannot rescue mass-only unification given the PE mass ordering.

## Code / repro

```bash
python -m pytest tests/test_premerger_mapping_v2.py -q
python scripts/premerger_mapping_v2_score.py
# → outputs/mapping_v2/mapping_v2_latest.json
```

| Path | Role |
|------|------|
| `src/premerger_mapping_v2.py` | Model, fit, campaign evaluator |
| `scripts/premerger_mapping_v2_score.py` | Score core + held-outs |
| `tests/test_premerger_mapping_v2.py` | Unit tests |

## Explicit non-claims

- Not a multi-event discovery  
- Not a license to float Hopf locks  
- Not a post-hoc redefinition of SUCCESS after seeing z=29.86  
- Not an endorsement of SNR-scaling without a new pre-reg (secondary P-v2b only if separately approved)

## Next (gated)

| Option | Status |
|--------|--------|
| Mapping v3 (inv-SNR + distance) | **Executed → family FALSIFY** — `docs/MILESTONE_PREMERGER_MAPPING_V3.md` |
| Bulk PE-power stretch | **Stopped** — `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` |
| GW170809 ROBUST_ANOMALY without shared α | Standing |
| Sensitivity \(p\in\{0,1,2\}\) | Optional appendix only; does not reopen family |
