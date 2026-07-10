# Milestone: Pre-merger mapping v5 (Hopf-lattice geometric \(\Lambda\))

**Status:** executed — campaign **FALSIFY**; Hopf-\(\Lambda\) family **closed**  
**Date:** 2026-07-10  
**Pre-reg:** `docs/PREREG_PREMERGER_MAPPING_V5.md`  
**Artifact:** `outputs/mapping_v5/mapping_v5_latest.json`

## What was tested

Frozen locks \(W_g=350/\pi\), \(\kappa\approx 0.85\), \(\phi_b\approx 0.8145\).  
Single free \(\alpha_0\sim\mathcal{N}(0,10^{-3})\).  
Primary form (**frozen in pre-reg**):

\[
\Theta_{\mathrm{link}}=\frac{2\pi W_g}{2W_g+1},\qquad
\Lambda=\frac{\Theta_{\mathrm{link}}}{\pi}\cdot\frac{M_{f,\mathrm{ref}}}{M_f}
\]

\[
\tau_{v5}=\tau_0\cdot\Lambda,\qquad r\approx\alpha_0\,\tau_{v5}
\]

with catalog \(M_f\) (same table as v4), \(M_{f,\mathrm{ref}}=63.1\,M_\odot\).  
Closed v1–v4 families **not** reopened. GW151012 systematics only.

## Pre-run honesty

| Quantity | Value |
|----------|--------|
| \(\Theta_{\mathrm{link}}\) | 3.127556 |
| \(\Lambda_0=\Theta_{\mathrm{link}}/\pi\) | 0.995532 |
| \(\Lambda_{809}/\Lambda_{914}\) | **1.121** |
| Empirical \(\alpha_{v1}\) ratio | ≈ **12.4** |

## Per-event results (IMRPhenomD, H1+L1)

| Event | \(M_f\) | \(\Lambda\) | \(\hat\alpha_0\) | \(\beta_{\mathrm{eff}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | P-v5 |
|-------|---------|-------------|------------------|--------------------------|------------------|----------------|------|
| GW150914 | 63.1 | 0.9955 | \(6.96\times10^{-5}\) | \(6.93\times10^{-5}\) | 30.4 | +10.8 | PASS |
| GW170814 | 53.2 | 1.1808 | \(6.31\times10^{-5}\) | \(7.45\times10^{-5}\) | 16.0 | +3.9 | PASS |
| **GW170809** | 56.3 | 1.1158 | \(7.69\times10^{-4}\) | \(8.58\times10^{-4}\) | 1338 | +665 | PASS |
| GW151012† | 35.7 | 1.7596 | \(-4.52\times10^{-5}\) | \(-7.96\times10^{-5}\) | 8.8 | +0.2 | PASS |
| GW170729 | 79.5 | 0.7902 | \(9.59\times10^{-5}\) | \(7.58\times10^{-5}\) | 2.5 | −1.6 | fail |

† Systematics-risk; not used for SUCCESS.

## Campaign verdict

| Check | Result |
|-------|--------|
| GW170809 P-v5 | **PASS** |
| GW170809 \(\ln B_{10}>5\) | **PASS** (+665) |
| Unify \(z(\alpha_0^{809}-\alpha_0^{914})\) | **28.52** ≫ 3 |
| β ratio vs \(\Lambda\) ratio | 12.38 vs **1.121** |

```text
CAMPAIGN VERDICT: FALSIFY
  Hopf Λ fails unification
  → Hopf-lattice geometric scaling family CLOSED under this pre-reg
```

## Interpretation

1. Primary \(\Lambda\) fails Unify as honesty predicted (\(\mathcal{O}(1)\) scale vs ~12 residual ratio).  
2. Residual strength on GW170809 unchanged; only \(\alpha_0\) reparameterized.  
3. Locks remain frozen; v1–v4 bulk PE / remnant families remain closed.  
4. This **specific** Hopf-geometric coupling form is closed — not a demotion of Hopf locks or \(\Theta_{\mathrm{link}}\) itself.  
5. Do not flip to post-hoc powers of \(\Lambda\) or free functional forms of PE parameters.

## Code / repro

```bash
python -m pytest tests/test_premerger_mapping_v5.py -q
python scripts/premerger_mapping_v5_score.py
```

| Path | Role |
|------|------|
| `src/premerger_mapping_v5.py` | Model, fit, campaign evaluator |
| `scripts/premerger_mapping_v5_score.py` | Score script |
| `tests/test_premerger_mapping_v5.py` | Unit tests |

## Next

| Item | Status |
|------|--------|
| Hopf-\(\Lambda\) family | **Closed** |
| Score-only under frozen template | Active |
| Further mapping | Fresh PREREG with a **new** physical variable only |
