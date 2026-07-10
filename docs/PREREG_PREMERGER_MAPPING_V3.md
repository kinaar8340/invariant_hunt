# Pre-registration: Pre-merger mapping v3 (non-mass scale)

**Status:** pre-registered — **executed 2026-07-10 → family FALSIFY; bulk PE-power closed**  
**Date:** 2026-07-10  
**Trigger:** Mapping v2 mass-unification **FALSIFY** (`docs/MILESTONE_PREMERGER_MAPPING_V2.md`)  
**Supersedes as predictive claim:** mass-only \(\beta\propto M_{\mathrm{tot}}^p\) (closed)  
**Does not reopen:** Hopf locks; demoted v1 universal α-band; design on GW151012  
**Result milestone:** `docs/MILESTONE_PREMERGER_MAPPING_V3.md`

## Motivation

| Fact | Implication |
|------|-------------|
| V2 mass \(p=1\): \(\beta\) ratio pred. ≈0.98 vs empirical ≈12.4; \(z(\alpha_0)\approx 30\) | Mass-only coupling **closed** |
| PE \(M_{\mathrm{tot}}^{809}/M_{\mathrm{tot}}^{914}\approx 0.98\) | **No** \(M^p\) (any \(p\)) can produce ratio ~12 |
| GW170809 still P-v2 + \(\ln B_{10}\approx +665\) under locked template | Residual **ROBUST_ANOMALY** without shared map |
| V2 secondary slot was SNR scaling (P-v2b) if mass failed | Now the primary non-mass family |

Goal: test whether a **different bulk PE / catalog observable** unifies \(\alpha_0\) between core GW150914 and GW170809, still with locks frozen and a single free amplitude.

## Frozen (unchanged)

| Quantity | Value | Role |
|----------|--------|------|
| \(W_g\) | \(350/\pi\) | Template kernel |
| \(\kappa\) | ≈ 0.85 | Not floated |
| \(\phi_b\) | ≈ 0.8145 | Kernel \(\cos\phi_b\) |
| Residual channel | same as v1/v2 | \(\tau_0=-W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\) |
| \(\alpha_0\) prior | \(\mathcal{N}(0,10^{-3})\) | MAP / BF |
| PE baseline | IMRPhenomD median + S-1 hygiene | Systematics |
| Data | Public GWOSC + GWTC-1 PE | Reproducible |

**Forbidden:** floating locks; re-fitting demoted v1 band; using GW151012 as design anchor; choosing the scale exponent after seeing GW170809 \(\hat\alpha\); promoting post-hoc powers that numerically hit ~12 (see honesty).

## Shared residual form

\[
h(\beta)\approx h_{\mathrm{GR}}+\beta\,\tau_0,\qquad
\beta=\alpha_0\,S,\qquad
\tau_{v3}=\tau_0\cdot S,\qquad
r\approx\alpha_0\,\tau_{v3}
\]

where \(S\) is an **event-fixed scale factor** from a pre-registered bulk observable (not fit jointly with \(\alpha_0\)).

As in v2: \(\beta_{\mathrm{eff}}=\hat\alpha_{v1}\) by construction; v3 tests **shared \(\alpha_0\)**, not a new residual \(\Delta\chi^2\).

## Candidate scale families

### Primary (P-v3a): inverse network SNR — systematics / PE-bias probe

Published GWTC-1 network matched-filter SNR \(\rho_{\mathrm{net}}\) (frozen table below; not re-fit from our PE proxy):

\[
S_{\rho}=\left(\frac{\rho_{\mathrm{ref}}}{\rho_{\mathrm{net}}}\right)^{q},\qquad
\rho_{\mathrm{ref}}=24.4\ \text{(GW150914)},\quad
q=1\ \text{fixed a priori}
\]

**Rationale:** GW170809 is weaker than GW150914 (\(\rho\sim 12.4\) vs \(24.4\)). Larger spurious residual amplitude on lower-SNR events is a classic PE / template-mismatch path. This is the natural successor to V2’s reserved P-v2b slot.

**Control:** \(q=0\) recovers event-independent α (v1 form).  
**Sensitivity only (not SUCCESS path):** \(q=2\) reported separately after primary score.

### Secondary (P-v3b): luminosity distance — only if P-v3a fails SUCCESS

PE-median luminosity distance \(d_L\) (detector-frame PE; freeze medians at first score):

\[
S_{d}=\left(\frac{d_L}{d_{\mathrm{ref}}}\right)^{s},\qquad
d_{\mathrm{ref}}=d_L(\mathrm{GW150914})\ \text{from PE median},\quad
s=1\ \text{fixed a priori}
\]

**Sensitivity only:** \(s=2\) reported separately.  
**Not registered:** \(s=3\) (would numerically approach the empirical α ratio ~12 — see honesty; registering it after that observation would be circular).

### Explicitly deferred / not in this pre-reg

| Family | Why deferred |
|--------|----------------|
| Mass \(M_{\mathrm{tot}}^p\) | Closed by V2 FALSIFY |
| \(\chi_{\mathrm{eff}}\) power | Both 914 and 809 near \(\chi_{\mathrm{eff}}\approx 0\); no dynamic range |
| Mass-ratio \(q\) or asymmetry alone | Mild ratio (~1.3–2.5); cannot reach ~12 with power 1; no independent spin-motivated theory claim yet |
| Free exponent with \(\mathcal{N}(1,0.5)\) prior | Would re-open post-data power selection; needs separate pre-reg if ever wanted |
| Fitting scale on GW170809 | Forbidden |

## Frozen \(\rho_{\mathrm{net}}\) table (GWTC-1 catalog, for P-v3a)

| Event | \(\rho_{\mathrm{net}}\) | Role |
|-------|------------------------|------|
| GW150914 | 24.4 | Core / \(\rho_{\mathrm{ref}}\) |
| GW170814 | 17.2 | Core sanity |
| GW170809 | 12.4 | Primary target |
| GW151012 | 10.0 | Systematics check only |
| GW170729 | 10.8 | Blind-ish holdout |

Sources: GWTC-1 / discovery papers network SNR (standard catalog values). If a published revision differs by \(\lt 5\%\), freeze the values in this table for the campaign rather than re-tuning.

## Pre-run honesty (before any v3 score)

Empirical target: \(\alpha_{v1}^{809}/\alpha_{v1}^{914}\approx 12.4\) (from v1/v2 fits; \(\beta_{\mathrm{eff}}\) identical).

| Scale \(S\) (809/914) | Predicted \(\beta\) ratio if shared \(\alpha_0\) | vs 12.4 |
|----------------------|--------------------------------------------------|---------|
| Mass \(p=1\) (closed) | ≈ 0.98 | fail |
| \(\rho_{\mathrm{ref}}/\rho\) \(q=1\) | ≈ **1.97** | short |
| \(\rho_{\mathrm{ref}}/\rho\) \(q=2\) | ≈ **3.87** | short |
| \(d_L\) \(s=1\) | ≈ **2.34** | short |
| \(d_L\) \(s=2\) | ≈ **5.48** | short |
| \(d_L\) \(s=3\) (not registered) | ≈ 12.8 | numerical match only — **do not adopt** |
| Mass asymmetry ratio | ≈ 2.51 | short |

**Implication:** mild powers of SNR or distance are **unlikely** to pass shared-\(\alpha_0\) unification. That is acceptable — the campaign is designed to **close or confirm** bulk PE-power maps, not to force a success. A clean FALSIFY of P-v3a (and then P-v3b) would mean: **no simple bulk PE power law with pre-registered mild exponents unifies core and GW170809.**

## Event roles

| Role | Events |
|------|--------|
| Design / sanity | GW150914, GW170814 |
| Primary target | **GW170809** |
| Systematics only | GW151012 — report, never optimize |
| Holdout | GW170729 (+ any new BBH under same freeze) |

## Gates

| Gate | Rule |
|------|------|
| **P-v3** | Same as P-v2: network \(\Delta\chi^2\ge 6\), \(\lvert\hat\alpha_0\rvert>2\sigma\), H1/L1 same sign if both >2σ |
| **B-v3** | \(\ln B_{10}>5\) on GW170809 under \(\alpha_0\sim\mathcal{N}(0,10^{-3})\) |
| **S-1** | Existing ROBUST_ANOMALY on GW170809 (already established; re-check only if template channel changes — it does not) |
| **Unify** | Shared \(\alpha_0\): \(z=\lvert\alpha_0^{809}-\alpha_0^{914}\rvert/\sqrt{\sigma_{809}^2+\sigma_{914}^2}\le 3\) |
| **FAIL-v3** | Sign flip under PE mass ±3% or approximant-only survival (reuse S-1 style if re-run) |

## SUCCESS / FALSIFY / NULL

| Verdict | Condition |
|---------|-----------|
| **SUCCESS (P-v3a)** | GW170809: P-v3 PASS + \(\ln B_{10}>5\) **and** Unify PASS under **inverse SNR \(q=1\)** |
| **FALSIFY (P-v3a)** | GW170809 residual-strong (P-v3 + BF) but Unify fail under \(q=1\); **or** P-v3 pass with BF fail |
| **NULL** | Gate P-v3 fail on GW170809 |
| **Then P-v3b** | Only if P-v3a is FALSIFY/NULL: repeat with \(s=1\) distance; same SUCCESS/FALSIFY rules |
| **Family closed** | If **both** P-v3a and P-v3b FALSIFY on Unify: declare **bulk PE-power mapping family closed** under this pre-reg; residual anomaly stands without shared map |

No SUCCESS may be claimed from sensitivity \(q=2\) or \(s=2\) alone. Those are appendix-only.

## Implementation plan (when execution opens)

1. `src/premerger_mapping_v3.py` — `PremergerPhaseModelV3` with scale mode `inv_snr` | `distance`, frozen tables  
2. Reuse `phase_basis_template` / network stack pattern from v2 (`τ_v3 = τ_0 · S`)  
3. `scripts/premerger_mapping_v3_score.py` — score core + GW170809 + systematics + holdout  
4. Pre-run honesty block printed **before** fits (as in v2 script)  
5. Milestone: `docs/MILESTONE_PREMERGER_MAPPING_V3.md`  
6. Optional appendix: \(q=2\), \(s=2\) sensitivity only

## Explicit non-goals

- Not restoring mass-only or v1 SUCCESS band  
- Not designing on GW151012  
- Not floating locks or free exponents after seeing 809  
- Not claiming discovery from one residual anomaly  
- Not adopting \(d_L^3\) because it numerically matches ~12  

## Go / no-go

| Condition | Action |
|-----------|--------|
| This pre-reg accepted | Implement v3 + score **P-v3a \(q=1\)** first |
| P-v3a SUCCESS | Optional holdouts under same freeze; no lock float |
| P-v3a FALSIFY | Run pre-registered **P-v3b \(s=1\)** only |
| Both FALSIFY on Unify | Close bulk PE-power family; stop mapping stretch unless new physical variable is pre-registered |
| GW151012 “improves” | Ignore for SUCCESS |

**Executed outcome:** both families FALSIFY → stretch **stopped**  
(`docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`). No further bulk PE-power mapping
without a new physical-variable pre-reg.

## Approval stamp

Pre-registered on 2026-07-10; executed same day → family FALSIFY.  
Further bulk PE-power runs under this form are **closed** (score-only archival OK).

## Cross-links

| Doc | Role |
|-----|------|
| `docs/PREREG_PREMERGER_MAPPING_V2.md` | Mass campaign (executed FALSIFY) |
| `docs/MILESTONE_PREMERGER_MAPPING_V2.md` | V2 results |
| `docs/MILESTONE_FALSIFY_SYSTEMATICS.md` | S-1; GW170809 ROBUST_ANOMALY; GW151012 SYSTEMATICS_RISK |
| `docs/PREDICTION_MODE.md` | Prediction discipline |
