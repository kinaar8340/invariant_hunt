# Milestone: Pre-merger mapping v3 (inverse SNR + distance)

**Status:** executed — family **FALSIFY**; bulk PE-power mapping **closed**  
**Date:** 2026-07-10  
**Pre-reg:** `docs/PREREG_PREMERGER_MAPPING_V3.md`  
**Artifact:** `outputs/mapping_v3/mapping_v3_latest.json`

## What was tested

Frozen locks \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\).  
Single free amplitude \(\alpha_0\sim\mathcal{N}(0,10^{-3})\).  
Same residual channel as v1/v2: \(\tau_0=-W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\).

| Family | Form | Power | Role |
|--------|------|-------|------|
| **P-v3a** | \(S=(\rho_{\mathrm{ref}}/\rho_{\mathrm{net}})^q\) | \(q=1\) fixed | Primary |
| **P-v3b** | \(S=(d_L/d_{\mathrm{ref}})^s\) | \(s=1\) fixed | Secondary (run after a FALSIFY) |

Mass scaling remains **closed** (v2). GW151012 scored only as systematics check.  
\(d_L^3\) **not** registered (post-hoc numerical match to α ratio ~12).

## Pre-run honesty

| Scale | Pred. β ratio 809/914 if shared \(\alpha_0\) | vs ~12.4 |
|-------|-----------------------------------------------|----------|
| Inv-SNR \(q=1\) | **1.97** | short |
| Distance \(s=1\) | **2.34** | short |
| \(d_L^3\) (not registered) | 12.8 | curiosity only |

## Results

### P-v3a — inverse SNR \(q=1\)

| Event | \(\rho_{\mathrm{net}}\) | \(S\) | \(\hat\alpha_0\) | \(\beta_{\mathrm{eff}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | P-v3 |
|-------|-------------------------|-------|------------------|--------------------------|------------------|----------------|------|
| GW150914 | 24.4 | 1.000 | \(6.93\times10^{-5}\) | \(6.93\times10^{-5}\) | 30.4 | +10.8 | PASS |
| GW170814 | 17.2 | 1.419 | \(5.25\times10^{-5}\) | \(7.45\times10^{-5}\) | 16.0 | +3.7 | PASS |
| **GW170809** | 12.4 | 1.968 | \(4.36\times10^{-4}\) | \(8.58\times10^{-4}\) | 1338 | +665 | PASS |
| GW151012† | 10.0 | 2.440 | \(-3.26\times10^{-5}\) | \(-7.96\times10^{-5}\) | 8.8 | −0.1 | PASS |
| GW170729 | 10.8 | 2.259 | \(3.36\times10^{-5}\) | \(7.58\times10^{-5}\) | 2.5 | −2.6 | fail |

**Unify:** \(z(\alpha_0^{809}-\alpha_0^{914})=21.18\gg 3\); β ratio 12.38 vs scale 1.97.  
**Verdict: FALSIFY** (unification).

### P-v3b — distance \(s=1\)

| Event | \(d_L\) (Mpc) | \(S\) | \(\hat\alpha_0\) | \(\beta_{\mathrm{eff}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | P-v3 |
|-------|---------------|-------|------------------|--------------------------|------------------|----------------|------|
| GW150914 | 439.3 | 1.000 | \(6.93\times10^{-5}\) | \(6.93\times10^{-5}\) | 30.4 | +10.8 | PASS |
| GW170814 | 596.9 | 1.359 | \(5.48\times10^{-5}\) | \(7.45\times10^{-5}\) | 16.0 | +3.7 | PASS |
| **GW170809** | 1028 | 2.341 | \(3.67\times10^{-4}\) | \(8.58\times10^{-4}\) | 1338 | +664 | PASS |
| GW151012† | 1081 | 2.461 | \(-3.23\times10^{-5}\) | \(-7.96\times10^{-5}\) | 8.8 | −0.1 | PASS |
| GW170729 | 2845 | 6.476 | \(1.17\times10^{-5}\) | \(7.58\times10^{-5}\) | 2.5 | −3.7 | fail |

**Unify:** \(z=18.50\gg 3\); β ratio 12.38 vs scale 2.34.  
**Verdict: FALSIFY** (unification).

† Systematics-risk; not used for SUCCESS.

## Family verdict

```text
FAMILY VERDICT: FALSIFY
  Both P-v3a (inv_snr q=1) and P-v3b (distance s=1) FALSIFY on Unify
  — bulk PE-power mapping family closed under this pre-reg
```

| Check | Result |
|-------|--------|
| GW170809 residual strength | Still extreme (\(\Delta\chi^2\sim 1338\), \(\ln B\sim +665\)) |
| Shared \(\alpha_0\) under inv-SNR | **No** (\(z=21\)) |
| Shared \(\alpha_0\) under distance | **No** (\(z=18.5\)) |
| Mass (v2) | Already closed |
| **Bulk PE-power family** | **CLOSED** |

Note: \(\beta_{\mathrm{eff}}=\hat\alpha_{v1}\) always; scaling only reparameterizes \(\alpha_0\). Residual \(\Delta\chi^2\) is unchanged from v1.

## Interpretation (discipline)

1. **Mild bulk PE powers do not unify** core and GW170809. Inv-SNR and distance fail the same way mass failed.  
2. **Core locks not reopened.** FALSIFY is about the shared-coupling map, not \(W_g,\kappa,\phi_b\).  
3. **GW170809 remains ROBUST_ANOMALY** under the locked template without a universal/shared \(\alpha\) map.  
4. **Do not** adopt \(d_L^3\) or free exponents post hoc to hit ratio ~12.  
5. **Do not** design next mapping on GW151012.  
6. **Stop bulk PE-power mapping stretch** under this pre-reg unless a *new physical variable* is separately pre-registered (not a rescue power).

## Code / repro

```bash
python -m pytest tests/test_premerger_mapping_v3.py -q
python scripts/premerger_mapping_v3_score.py          # both families
python scripts/premerger_mapping_v3_score.py --mode inv_snr
```

| Path | Role |
|------|------|
| `src/premerger_mapping_v3.py` | Model, fit, campaign + family evaluator |
| `scripts/premerger_mapping_v3_score.py` | Score script |
| `tests/test_premerger_mapping_v3.py` | Unit tests |
| `outputs/mapping_v3/mapping_v3_latest.json` | Full JSON |

## Explicit non-claims

- Not a multi-event discovery  
- Not license to float locks or re-fit v1 band  
- Not endorsement of unregistered \(d_L^3\)  
- Not a claim that the residual is non-physical — only that **shared bulk PE-power maps fail**

## Next (gated)

| Option | Status |
|--------|--------|
| Stop bulk PE-power mapping stretch | **Done** — `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` |
| Residual as unexplained ROBUST_ANOMALY | Standing (score-only) |
| New pre-reg | Only independent physical variable — not mild PE power rescue |
| Sensitivity \(q=2\), \(s=2\) | Optional appendix only; not SUCCESS path; not required |
