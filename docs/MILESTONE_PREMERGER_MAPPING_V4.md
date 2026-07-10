# Milestone: Pre-merger mapping v4 (remnant mass \(M_f\))

**Status:** executed — campaign **FALSIFY**; remnant-mass family **closed**  
**Date:** 2026-07-10  
**Pre-reg:** `docs/PREREG_PREMERGER_MAPPING_V4.md`  
**Artifact:** `outputs/mapping_v4/mapping_v4_latest.json`

## What was tested

Frozen locks \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\).  
Single free \(\alpha_0\sim\mathcal{N}(0,10^{-3})\).  
Primary form (**\(p=1\) fixed**):

\[
S=\left(\frac{M_f}{M_{f,\mathrm{ref}}}\right)^{1},\qquad
\tau_{v4}=\tau_0\cdot S,\qquad
r\approx\alpha_0\,\tau_{v4}
\]

with catalog \(M_f\) from `PublicGWEvent.mass_final_solar` / frozen PREREG table  
(\(M_{f,\mathrm{ref}}=63.1\,M_\odot\) for GW150914).  
Closed v2/v3 bulk PE families **not** reopened. GW151012 systematics only.

## Pre-run honesty

| Quantity | Value |
|----------|--------|
| \(M_f^{809}\) | 56.3 \(M_\odot\) |
| \(M_f^{914}\) | 63.1 \(M_\odot\) |
| Pred. β ratio \(p=1\) | **0.892** (wrong way) |
| Pred. β ratio \(p=2\) | **0.796** (sensitivity) |
| Empirical \(\alpha_{v1}\) ratio | ≈ **12.4** |

## Per-event results (IMRPhenomD, H1+L1)

| Event | \(M_f\) | \(S\) | \(\hat\alpha_0\) | \(\beta_{\mathrm{eff}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | P-v4 |
|-------|---------|-------|------------------|--------------------------|------------------|----------------|------|
| GW150914 | 63.1 | 1.000 | \(6.93\times10^{-5}\) | \(6.93\times10^{-5}\) | 30.4 | +10.8 | PASS |
| GW170814 | 53.2 | 0.843 | \(8.84\times10^{-5}\) | \(7.45\times10^{-5}\) | 16.0 | +4.2 | PASS |
| **GW170809** | 56.3 | 0.892 | \(9.62\times10^{-4}\) | \(8.58\times10^{-4}\) | 1338 | +665 | PASS |
| GW151012† | 35.7 | 0.566 | \(-1.41\times10^{-4}\) | \(-7.96\times10^{-5}\) | 8.8 | +1.3 | PASS |
| GW170729 | 79.5 | 1.260 | \(6.02\times10^{-5}\) | \(7.58\times10^{-5}\) | 2.5 | −2.0 | fail |

† Systematics-risk; not used for SUCCESS.

## Campaign verdict

| Check | Result |
|-------|--------|
| GW170809 P-v4 | **PASS** |
| GW170809 \(\ln B_{10}>5\) | **PASS** (+665) |
| Unify \(z(\alpha_0^{809}-\alpha_0^{914})\) | **30.63** ≫ 3 |
| β ratio vs scale | 12.38 vs **0.892** |

```text
CAMPAIGN VERDICT: FALSIFY
  remnant-mass p=1 fails unification
  → remnant-mass scaling family CLOSED under this pre-reg
```

## Interpretation

1. Remnant mass scaling fails Unify as honesty predicted (wrong-way ratio).  
2. Residual strength on GW170809 unchanged (\(\Delta\chi^2\sim 1338\)); only \(\alpha_0\) reparameterized.  
3. Locks remain frozen; v2/v3 bulk PE families remain closed.  
4. GW170809 stands as ROBUST_ANOMALY **without** shared \(\alpha_0\) under \(M_f^p\).  
5. Do not adopt post-hoc powers of \(M_f\) to force ratio ~12.

## Code / repro

```bash
python -m pytest tests/test_premerger_mapping_v4.py -q
python scripts/premerger_mapping_v4_score.py
```

| Path | Role |
|------|------|
| `src/premerger_mapping_v4.py` | Model, fit, campaign evaluator |
| `scripts/premerger_mapping_v4_score.py` | Score script |
| `tests/test_premerger_mapping_v4.py` | Unit tests |

## Next

| Item | Status |
|------|--------|
| Remnant-mass family | **Closed** |
| Score-only under frozen template | Active |
| New mapping | Fresh PREREG with a **new** physical variable only |
