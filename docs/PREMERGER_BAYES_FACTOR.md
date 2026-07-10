# Pre-merger Bayes factor (topo vs GR)

**Status:** implemented (gated complement to \(\Delta\chi^2\) / Gate P)  
**Date:** 2026-07-10

## Models

| Hypothesis | Residual model |
|------------|----------------|
| **H0 (GR)** | \(r = n\) after PE subtraction (whitened, \(\sigma=1\)) |
| **H1 (topo)** | \(r = \alpha\,\tau + n\), \(\tau = -K\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\) |

Locks fixed: \(K = W_g\cos\phi_b\). Only \(\alpha\) is free under H1.

## Pre-registered prior

\[
\alpha \sim \mathcal{N}(0,\,\sigma_p^2), \qquad \sigma_p = 10^{-3}
\]

Covers the former freeze band \(\sim 10^{-4}\) without re-fitting it; allows
\(|\alpha|\sim 10^{-3}\) if data demand it. **Does not revive the demoted
universal band as a SUCCESS criterion.**

## Exact Gaussian marginal BF

\[
\ln B_{10}
= -\tfrac12\log(\sigma_p^2 H) + \frac{b^2}{2H},
\quad
H=\|\tau\|^2+\sigma_p^{-2},
\quad
b=\tau\cdot r
\]

Cross-checks: Savage–Dickey (exact match for this model), BIC
\(\ln B \approx \tfrac12(\Delta\chi^2 - \log N)\).

## Usage

```bash
python scripts/premerger_bayes_factor.py --event GW150914 --calibrate
python scripts/premerger_bayes_factor.py --events GW170809,GW170729,GW151012
```

Artifact: `outputs/bayes/premerger_bayes_latest.json`.

## Kass–Raftery grades (on \(2\ln B\))

Reported string grades: `very_strong_topo` / `strong_topo` / … /
`very_strong_GR` (sign of \(\ln B_{10}\): + favors topo).

## Relation to held-out demotion

True held-out α-band claim remains **demoted** (0 SUCCESS / 2 FALSIFY / 1 NULL).  
Bayes factors **complement** \(\Delta\chi^2\); they do not re-open core locks or
the band. Large \(B_{10}\) with \(\hat\alpha\) outside the old band is still
consistent with FALSIFY of *band universality*, not SUCCESS of the freeze rule.

### Snapshot scores (σ_p=10^{-3}, IMRPhenomD medians)

| Event | \(\hat\alpha_{\mathrm{MLE}}\) | \(\Delta\chi^2\) | \(\ln B_{10}\) | Grade | Gate P |
|-------|-------------------------------|------------------|----------------|-------|--------|
| GW150914 (core) | \(+6.93\times10^{-5}\) | 30.4 | +10.8 | very_strong_topo | PASS |
| GW170809 (held-out) | \(+8.58\times10^{-4}\) | 1338 | +665 | very_strong_topo | PASS |
| GW170729 (held-out) | \(+7.58\times10^{-5}\) | 2.5 | −1.8 | positive_GR | fail |
| GW151012 (held-out) | \(-7.96\times10^{-5}\) | 8.8 | +0.8 | barely_topo | PASS |

Calibration (white noise on GW150914 stack): α_inj=0 → lnB≈−4 (favors GR);
α_inj=10^{-4} → lnB≈+29 (favors topo).

## Discipline

| Allowed | Not allowed |
|---------|-------------|
| Report \(\ln B_{10}\) on any BBH | Re-fit \(\sigma_p\) or band after seeing held-outs |
| Calibrate with injections | Treat BF as discovery without PE systematics |
| Compare to Gate P | Demote \(W_g,\kappa,\phi_b\) from BF alone |
