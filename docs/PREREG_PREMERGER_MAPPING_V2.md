# Pre-registration: Pre-merger mapping v2 (Gate P-v2)

**Status:** pre-registered — **executed 2026-07-10 → campaign FALSIFY**  
**Date:** 2026-07-10  
**Trigger:** Gate S-1 **ROBUST_ANOMALY** on true held-out **GW170809** only  
**Supersedes as predictive claim:** mapping v1 universal α-band (demoted)  
**Result milestone:** `docs/MILESTONE_PREMERGER_MAPPING_V2.md`  
**Successor pre-reg (not executed):** `docs/PREREG_PREMERGER_MAPPING_V3.md` (inverse SNR / distance; mass closed)

## Motivation (evidence, not free invention)

| Fact | Implication |
|------|-------------|
| True held-outs: 0 SUCCESS / 2 FALSIFY / 1 NULL under v1 band | Universal α ∈ [2.88e-5, 1.15e-4] demoted |
| GW170809 S-1 ROBUST_ANOMALY | Large stable **+α ≈ 8×10^{-4}**, ln B ≫ 0, multi-approx + draws |
| GW151012 S-1 SYSTEMATICS_RISK (n_draws≥12) | Do **not** design for dual-sign pair |
| Core GW150914 | α ≈ +7×10^{-5}, ln B ≈ +11 — smaller than GW170809 |

v1 form \(\Delta\phi=\alpha W_g\Phi_{\mathrm{orb}}\cos\phi_b\) with **event-independent α**
cannot be a universal SUCCESS criterion. v2 tests whether a **mass- or
SNR-scaled coupling** (locks still fixed) unifies core + GW170809 without
fitting GW151012.

## Frozen (unchanged)

| Quantity | Value | Role |
|----------|--------|------|
| \(W_g\) | \(350/\pi\) | Template kernel |
| \(\kappa\) | ≈ 0.85 | Not floated |
| \(\phi_b\) | ≈ 0.8145 | Kernel \(\cos\phi_b\) |
| PE baseline | IMRPhenomD median + S-1 suite | Systematics hygiene |
| Data | Public GWOSC + GWTC PE | Reproducible |

**Forbidden until independent justification:** floating \(W_g\), \(\kappa\), \(\phi_b\);
re-fitting the demoted v1 band; using GW151012 as a design anchor.

## v2 template (candidate form)

### Shared residual channel (unchanged linearization)

\[
h(\beta) \approx h_{\mathrm{GR}} - \beta\cdot\bigl[W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\bigr]\cdot H[h_{\mathrm{GR}}]
= h_{\mathrm{GR}} + \beta\,\tau_0
\]

with \(\tau_0 = -K\Phi_{\mathrm{orb}}H[h_{\mathrm{GR}}]\), \(K=W_g\cos\phi_b\).

### Event-dependent coupling (new)

\[
\beta = \alpha_0 \left(\frac{M_{\mathrm{tot}}}{M_{\mathrm{ref}}}\right)^{p}
\quad\text{or}\quad
\beta = \alpha_0 \left(\frac{\rho_{\mathrm{net}}}{\rho_{\mathrm{ref}}}\right)^{q}
\]

| Symbol | Status | Pre-registered choice |
|--------|--------|------------------------|
| \(\alpha_0\) | **Free** (fit per campaign; or hierarchical) | Prior \(\alpha_0\sim\mathcal{N}(0,\,10^{-3})\) same as BF prior scale |
| \(p\) or \(q\) | **Pre-registered grid** (not free fit after seeing data) | Primary: \(p\in\{0,\,1,\,2\}\) mass-power; secondary optional \(q\in\{0,\,1\}\) SNR-power |
| \(M_{\mathrm{ref}}\) | Fixed | \(60\,M_\odot\) (GW150914-class) |
| \(\rho_{\mathrm{ref}}\) | Fixed | network MF SNR of GW150914 PE fit (measured once, frozen) |
| \(M_{\mathrm{tot}}\) | Fixed from PE median \(m_1+m_2\) | Detector-frame totals |

**Primary campaign form (P-v2a):** mass scaling only,

\[
\beta = \alpha_0 \left(\frac{M_{\mathrm{tot}}}{60\,M_\odot}\right)^{p},\quad p\in\{0,1,2\}
\]

with \(\alpha_0\) the single free amplitude (MAP / BF under same Gaussian prior).  
\(p=0\) recovers v1 (control). \(p=1,2\) test whether GW170809’s larger \(\beta\)
tracks higher total mass relative to core.

**Secondary (P-v2b, only if P-v2a fails pre-registered SUCCESS rule):** SNR scaling
\(q\in\{0,1\}\), same \(\alpha_0\) prior — still locks fixed.

## Pre-registered scoring protocol

### Event roles

| Role | Events |
|------|--------|
| **Design / sanity** | GW150914 (core), GW170814 (core) — check consistency, not free fit of locks |
| **Primary target** | **GW170809** (true held-out ROBUST_ANOMALY) |
| **Null / systematics** | GW151012 (SYSTEMATICS_RISK) — expect weak/unstable; do not optimize on it |
| **Blind-ish holdouts** | GW170729 (NULL under v1), plus any new BBH not used in design |

### Gates (must all be stated before first v2 score)

| Gate | Rule |
|------|------|
| **P-v2** | Network \(\Delta\chi^2\ge 6\), \(\lvert\hat\beta\rvert>2\sigma_\beta\), H1/L1 same sign if both >2σ |
| **S-1** | ROBUST_ANOMALY (or better) on GW170809 under multi-approx + **n_draws≥12** |
| **B-v2** | \(\ln B_{10}>0\) on GW170809 with \(\alpha_0\sim\mathcal{N}(0,10^{-3})\) (reuse BF machinery) |
| **Cross** | Core GW150914: \(\hat\beta\) and \(\hat\alpha_0\) finite; no requirement that \(\beta\) match demoted v1 band |
| **FAIL-v2** | S-1 SYSTEMATICS_RISK on GW170809 under v2, or sign flip under mass ±3%, or SEOBNR-only survival |

### SUCCESS / FALSIFY / NULL (v2 campaign)

| Verdict | Condition |
|---------|-----------|
| **SUCCESS** | On **GW170809**: P-v2 PASS + S-1 ROBUST_ANOMALY + \(\ln B_{10}>5\); **and** \(p^\star\) (pre-registered grid pick by max evidence on **core only** before held-out) improves GW170809 \(\ln B\) over \(p=0\) by \(\Delta\ln B>2\) **without** using GW170809 to pick \(p\) |
| **FALSIFY** | GW170809 P-v2 PASS but S-1 SYSTEMATICS_RISK, or core-only \(p\) selection fails \(\Delta\ln B>2\) on GW170809, or \(\alpha_0\) posterior inconsistent with zero only on one approximant |
| **NULL** | Gate P-v2 fail on GW170809 |

**Critical hygiene:** Choose \(p\) by **core-only** (GW150914+GW170814) evidence **before** looking at GW170809 v2 scores, or fix \(p=1\) a priori in code before any v2 run. Prefer **fix \(p=1\) a priori** to avoid any selection bias:

> **Default executed form:** \(p=1\) fixed (not grid-selected on data).  
> Grid \(p\in\{0,1,2\}\) only as **secondary sensitivity**, reported separately.

## Implementation plan (when execution opens)

1. `src/premerger_theory.py` — `PremergerPhaseModelV2` with `mass_power=p`, `m_ref=60`  
2. `phase_basis_template_v2` = \(\tau_0 \times (M_{\mathrm{tot}}/M_{\mathrm{ref}})^p\) absorbed into effective τ  
3. Reuse `fit_premerger_phase_network`, `premerger_bayes_factor`, `premerger_falsify_systematics`  
4. Script `scripts/premerger_mapping_v2_score.py` — score core + GW170809 + GW151012 under v2  
5. Milestone after first run: `docs/MILESTONE_PREMERGER_MAPPING_V2.md`

## Explicit non-goals

- Not restoring v1 SUCCESS band  
- Not fitting α to absorb GW151012  
- Not floating Hopf locks  
- Not a multi-event discovery claim from one ROBUST_ANOMALY  

## Go / no-go

| Condition | Action |
|-----------|--------|
| This pre-reg accepted | Implement v2 code + score with **p=1 fixed** |
| GW170809 fails S-1 under v2 | Stop; no further mapping stretch |
| GW170809 passes v2 gates | Optional: score GW170729 / new BBHs under same pre-reg |
| GW151012 “improves” | Ignore for SUCCESS; report only as systematics check |

## Approval stamp

Pre-registered on 2026-07-10 for execution when explicitly requested  
(“implement mapping v2” / “run P-v2”). Until then: **score-only under demoted v1 band remains historical; no new template runs.**
