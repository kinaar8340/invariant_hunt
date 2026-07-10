# Pre-registration: Pre-merger mapping v4 (remnant mass scaling)

**Status:** pre-registered — **executed 2026-07-10 → FALSIFY; remnant-mass family closed**  
**Date:** 2026-07-10  
**Trigger:** Bulk PE-power mapping family closed (`docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`)  
**Supersedes as predictive claim:** All previous bulk PE-power scalings  
(\(M_{\mathrm{tot}}\), inverse SNR, distance) — those families remain **closed**  
**Does not reopen:** Hopf locks; demoted v1 universal α-band; design on GW151012  
**Archive of closed family:** `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md`  
**Result milestone:** `docs/MILESTONE_PREMERGER_MAPPING_V4.md`

## Motivation

| Fact | Implication |
|------|-------------|
| v2–v3 bulk PE-power family closed on unification | Need genuinely new physical variable |
| GW170809 remains strong ROBUST_ANOMALY under locked template | Residual preference is real and stable |
| Remnant mass \(M_f\) is the natural final-state scale after energy loss to GWs | Different from pre-merger \(M_{\mathrm{tot}}\); more directly relevant to post-merger / ringdown regime |
| Previous mild powers failed to explain ~12× effect size difference | New variable must be pre-registered with honesty table |

Goal: Test whether scaling the coupling amplitude with **remnant (final) black hole mass** can unify \(\alpha_0\) between core events and GW170809 while keeping all locks frozen.

## Frozen (unchanged)

| Quantity | Value | Role |
|----------|--------|------|
| \(W_g\) | \(350/\pi\) | Template kernel |
| \(\kappa\) | ≈ 0.85 | Not floated |
| \(\phi_b\) | ≈ 0.8145 | Kernel \(\cos\phi_b\) |
| Residual channel | same as v1/v2/v3 | \(\tau_0 = -W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\) |
| \(\alpha_0\) prior | \(\mathcal{N}(0,10^{-3})\) | MAP / Bayes factor |
| PE baseline + S-1 hygiene | IMRPhenomD median + multi-approximant + draws | Systematics control |
| Data | Public GWOSC + GWTC PE | Reproducible |

**Forbidden:** floating locks; re-fitting demoted v1 band; using GW151012 as design anchor; post-hoc exponents chosen to match observed ratio ~12; reopening closed \(M_{\mathrm{tot}}\) / inv-SNR / distance families under a new name.

## Template form (v4)

Shared residual channel (unchanged linearization):

\[
h(\beta)\approx h_{\mathrm{GR}}+\beta\,\tau_0,\qquad
\beta=\alpha_0\cdot S,\qquad
\tau_{v4}=\tau_0\cdot S,\qquad
r\approx\alpha_0\,\tau_{v4}
\]

where the new scale factor is:

\[
S=\left(\frac{M_f}{M_{f,\mathrm{ref}}}\right)^{p}
\]

with:

| Symbol | Definition |
|--------|------------|
| \(M_f\) | Remnant (final) black hole mass [ \(M_\odot\) ] |
| \(M_{f,\mathrm{ref}}\) | Remnant mass of **GW150914**, frozen at first execution |
| \(p\) | **1 fixed a priori** (primary form) |
| \(\alpha_0\) | Single free amplitude |

**Source of \(M_f\) (frozen table at execution):**

1. **Primary:** catalog / GWTC published remnant masses as registered in
   `src/gw_events.py` (`PublicGWEvent.mass_final_solar`) — reproducible without
   re-deriving remnant from detector-frame PE medians alone.  
2. **Optional cross-check:** PE-derived remnant if available in public samples;
   if PE and catalog differ by \(\lt 5\%\), freeze catalog; if larger, document
   both and run primary on catalog.

**Control:** \(p=0\) recovers event-independent α (v1 form).  
**Sensitivity only (not SUCCESS path):** \(p=2\) reported in appendix after primary.

As in v2/v3: \(\beta_{\mathrm{eff}}=\hat\alpha_{v1}\) by construction; v4 tests
**shared \(\alpha_0\)**, not a new residual \(\Delta\chi^2\).

## Frozen catalog \(M_f\) table (pre-registered source)

From `src/gw_events.py` (GWTC-1 class published remnants):

| Event | \(M_f\,[M_\odot]\) | Role |
|-------|---------------------|------|
| GW150914 | 63.1 | Core / \(M_{f,\mathrm{ref}}\) |
| GW170814 | 53.2 | Core sanity |
| GW170809 | 56.3 | Primary target |
| GW151012 | 35.7 | Systematics check only |
| GW170729 | 79.5 | Holdout |

## Pre-run honesty (catalog \(M_f\); re-log at execution before fits)

Empirical target: \(\alpha_{v1}^{809}/\alpha_{v1}^{914}\approx 12.4\)
(from v1/v2/v3 fits; \(\beta_{\mathrm{eff}}\) identical under pure reparameterization).

| Scale | Pred. β ratio 809/914 if shared \(\alpha_0\) | vs ~12.4 | Comment |
|-------|-----------------------------------------------|----------|---------|
| Remnant \(p=1\) | \(56.3/63.1\approx\mathbf{0.892}\) | short / **wrong way** | Primary registered form |
| Remnant \(p=2\) | \(\approx\mathbf{0.796}\) | worse | Sensitivity only |
| Closed \(M_{\mathrm{tot}}\) \(p=1\) | ≈ 0.98 | short | Already FALSIFY |
| Closed inv-SNR \(q=1\) | ≈ 1.97 | short | Already FALSIFY |
| Closed \(d_L\) \(s=1\) | ≈ 2.34 | short | Already FALSIFY |

**Implication:** Catalog \(M_f^{809}<M_f^{914}\), so remnant-mass power laws with
\(p>0\) predict a **smaller** coupling on GW170809 than on the core — opposite
the observed residual amplitude ratio ~12. Unification **FALSIFY is the expected
honest outcome** unless PE-refined \(M_f\) reverse the ordering (they are not
expected to by enough to reach ~12). This pre-reg still **must be run** once
accepted: a predicted failure is a valid, high-value result that closes the
remnant-mass family under discipline.

At execution, the scoring script must print this honesty block **before** any fit.

## Event roles

| Role | Events |
|------|--------|
| Design / sanity | GW150914, GW170814 |
| Primary target | **GW170809** (ROBUST_ANOMALY) |
| Systematics only | GW151012 — report only, never optimize on it |
| Holdout | GW170729 + any future BBH under same freeze |

## Gates (identical structure to v2/v3)

| Gate | Rule |
|------|------|
| **P-v4** | Network \(\Delta\chi^2\ge 6\), \(\lvert\hat\alpha_0\rvert>2\sigma\), same sign on H1/L1 if both significant |
| **B-v4** | \(\ln B_{10}>5\) on GW170809 under \(\alpha_0\sim\mathcal{N}(0,10^{-3})\) |
| **S-1** | Already established ROBUST_ANOMALY on GW170809 (re-check only if template channel changes — it does not) |
| **Unify** | Shared \(\alpha_0\): \(z=\lvert\alpha_0^{809}-\alpha_0^{914}\rvert/\sqrt{\sigma_{809}^2+\sigma_{914}^2}\le 3\) |
| **FAIL-v4** | Sign flip under mass jitter or approximant-only survival |

## SUCCESS / FALSIFY / NULL (v4 campaign)

| Verdict | Condition |
|---------|-----------|
| **SUCCESS (primary)** | GW170809: P-v4 PASS + \(\ln B_{10}>5\) **and** Unify PASS under remnant-mass scaling (\(p=1\)) |
| **FALSIFY** | GW170809 residual-strong but Unify fails, or BF fails |
| **NULL** | Gate P-v4 fails on GW170809 |
| **Family closed** | If primary form FALSIFYs on Unify → remnant-mass scaling family **closed** under this pre-reg |

No SUCCESS from sensitivity \(p=2\) alone.

## Implementation plan (when execution opens)

1. `src/premerger_mapping_v4.py` — `PremergerPhaseModelV4` with remnant-mass scaling  
2. Reuse existing network fit + Bayes factor machinery (v2/v3 pattern)  
3. `scripts/premerger_mapping_v4_score.py` — score with pre-run honesty block  
4. `tests/test_premerger_mapping_v4.py` — unit tests (no PE)  
5. Milestone: `docs/MILESTONE_PREMERGER_MAPPING_V4.md`  
6. Optional appendix: \(p=2\) sensitivity  

## Explicit non-goals

- Not restoring any previous bulk PE-power family  
- Not designing on GW151012  
- Not floating locks or using post-hoc exponents  
- Not claiming discovery from a single robust anomaly  
- Not treating \(M_f\) as a synonym for closed \(M_{\mathrm{tot}}\) if both fail — each is a separate pre-reg, but both can be closed  

## Go / no-go

| Condition | Action |
|-----------|--------|
| This pre-reg accepted | Implement v4 + execute primary \(p=1\) form |
| Primary form SUCCESS | Optional holdouts under same freeze |
| Primary form FALSIFY on Unify | Close remnant-mass scaling family; stop unless new variable pre-registered |
| GW151012 “improves” | Ignore for SUCCESS |

## Approval stamp

Pre-registered on 2026-07-10.  
Execution only when explicitly requested  
(“implement mapping v4” / “run V4 remnant mass”).

Until then: **no new template runs** under this form. Score-only and archival
re-runs of closed v2/v3 remain allowed.

## Cross-links

| Doc | Role |
|-----|------|
| `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Closed v1–v3 family |
| `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md` | Archive index |
| `docs/MILESTONE_FALSIFY_SYSTEMATICS.md` | S-1; GW170809 ROBUST_ANOMALY |
| `docs/PREDICTION_MODE.md` | Score-only discipline |
| `docs/PREREG_PREMERGER_MAPPING_V2.md` | Closed mass \(M_{\mathrm{tot}}\) |
| `docs/PREREG_PREMERGER_MAPPING_V3.md` | Closed inv-SNR / distance |
