# Pre-registration: Pre-merger mapping v5 (Hopf-lattice geometric quantity)

**Status:** pre-registered — **executed 2026-07-10 → FALSIFY; Hopf-\(\Lambda\) family closed**  
**Date:** 2026-07-10  
**Trigger:** Bulk PE-power + remnant-mass mapping families fully closed  
(`docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`, `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md`)  
**Supersedes as predictive claim:** All previous bulk PE-power and remnant-mass scalings (v1–v4)  
**Does not reopen:** Hopf locks; demoted v1 universal α-band; design on GW151012  
**Archive reference:** `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md`  
**Result milestone:** `docs/MILESTONE_PREMERGER_MAPPING_V5.md`

## Motivation

| Fact | Implication |
|------|-------------|
| v1–v4 bulk PE-power and remnant-mass families closed on unification | Need a genuinely new physical variable |
| GW170809 remains a strong ROBUST_ANOMALY under the locked template | Residual preference is stable and unexplained by previous families |
| Previous scalings were bulk PE powers (\(M_{\mathrm{tot}}\), SNR, \(d_L\), \(M_f^{\pm 1}\)-style) | New variable should be **theory-native** to the gauged Hopf lattice |
| Hopf lattice supplies linking / twist / holonomy structure | Use locked linking saturation + geometric time as coupling scale |

Goal: Test whether a **Hopf-lattice geometric quantity** \(\Lambda\) can serve as the scale
factor that unifies \(\alpha_0\) between core events and GW170809 while keeping all
core locks frozen.

## Frozen (unchanged)

| Quantity | Value | Role |
|----------|--------|------|
| \(W_g\) | \(350/\pi\) | Template kernel + linking formula |
| \(\kappa\) | ≈ 0.85 | Not floated |
| \(\phi_b\) | ≈ 0.8145 | Kernel \(\cos\phi_b\) |
| Residual channel | same as v1–v4 | \(\tau_0=-W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\) |
| \(\alpha_0\) prior | \(\mathcal{N}(0,10^{-3})\) | MAP / Bayes factor |
| PE baseline + S-1 hygiene | IMRPhenomD median + multi-approximant + draws | Systematics control |
| Data | Public GWOSC + GWTC PE | Reproducible |
| Catalog \(M_f\) | Same table as v4 (`PublicGWEvent.mass_final_solar`) | Event geometric time only |

**Forbidden:** floating locks; re-fitting the demoted v1 band; using GW151012 as a design
anchor; post-hoc adjustment of \(\Lambda\) after seeing scores; reopening closed bulk-PE
or remnant-mass **power** families as mild rescues; choosing the form of \(\Lambda\) after
looking at GW170809 \(\hat\alpha\).

## Template form (v5)

Shared residual channel (unchanged linearization):

\[
h(\beta)\approx h_{\mathrm{GR}}+\beta\,\tau_0,\qquad
\beta=\alpha_0\cdot S,\qquad
\tau_{v5}=\tau_0\cdot S,\qquad
r\approx\alpha_0\,\tau_{v5}
\]

with scale factor \(S=\Lambda\) (dimensionless).

### Frozen definition of \(\Lambda\) (primary — fixed a priori)

From the gauged Hopf lattice (`src/invariants.py`):

\[
\Theta_{\mathrm{link}}
  = \frac{2\pi W_g}{2W_g+1}
  \qquad\text{(linking saturation; locks fixed)}
\]

Geometric time for remnant mass: \(t_M = (GM_f/c^3) \propto M_f\).

**Primary form (P-v5):**

\[
\boxed{\;
\Lambda
  = \frac{\Theta_{\mathrm{link}}}{\pi}
    \cdot \frac{t_{M,\mathrm{ref}}}{t_M}
  = \frac{\Theta_{\mathrm{link}}}{\pi}
    \cdot \frac{M_{f,\mathrm{ref}}}{M_f}
\;}
\]

| Symbol | Value / source |
|--------|----------------|
| \(W_g\) | \(350/\pi\) (locked) |
| \(\Theta_{\mathrm{link}}/\pi\) | \(\approx 0.9955\) (fixed number once \(W_g\) frozen) |
| \(M_f\) | Catalog remnant mass (same frozen table as v4) |
| \(M_{f,\mathrm{ref}}\) | \(M_f(\mathrm{GW150914})=63.1\,M_\odot\) |

**Theory motivation:** Lattice linking saturation sets the dimensionless weight;
inverse geometric time is the standard Hopf→GR frequency / holonomy-rate map
(\(f_{\mathrm{phys}}\propto 1/t_M\)), **not** a free bulk PE power fit.  
Locks enter only through \(\Theta_{\mathrm{link}}(W_g)\); they are **not** floated.

**Control (reported, not SUCCESS path):**

\[
\Lambda_{\mathrm{ctrl}} = \frac{\Theta_{\mathrm{link}}}{\pi}
\quad\text{(event-independent; recovers v1 reparameterization)}
\]

**Sensitivity only (not SUCCESS path):**

\[
\Lambda_{\mathrm{sens}}
  = \frac{\Theta_{\mathrm{link}}}{\theta_{\mathrm{crit}}}
    \cdot \frac{M_{f,\mathrm{ref}}}{M_f},
\quad
\theta_{\mathrm{crit}}=\pi(1+\kappa)
\]

(same event dependence as primary up to a fixed lock ratio; appendix only).

As in v2–v4: \(\beta_{\mathrm{eff}}=\hat\alpha_{v1}\) by construction; v5 tests
**shared \(\alpha_0\)** under \(\Lambda\), not a new residual \(\Delta\chi^2\).

### Explicit distinction from closed families

| Closed family | Form | v5 primary |
|---------------|------|------------|
| v2 | \((M_{\mathrm{tot}}/M_{\mathrm{ref}})^{+1}\) | Different mass definition + **inverse** geometric time + \(\Theta_{\mathrm{link}}\) weight |
| v4 | \((M_f/M_{\mathrm{ref}})^{+1}\) | **Inverse** \(M_f\) ratio × Hopf linking weight — not a re-run of \(p=+1\) |
| v3 | SNR / \(d_L\) powers | Not used |

If Unify fails, this family still **closes** under discipline (do not flip to \(+p\) or free \(p\) post hoc).

## Pre-run honesty (catalog \(M_f\); re-log at execution before fits)

Empirical target: \(\alpha_{v1}^{809}/\alpha_{v1}^{914}\approx 12.4\).

With \(\Theta_{\mathrm{link}}/\pi\) cancelling in the ratio:

\[
\frac{\Lambda_{809}}{\Lambda_{914}}
  = \frac{M_{f,914}}{M_{f,809}}
  = \frac{63.1}{56.3}
  \approx \mathbf{1.121}
\]

| Scale | Pred. β ratio 809/914 if shared \(\alpha_0\) | vs ~12.4 |
|-------|-----------------------------------------------|----------|
| **P-v5 primary** \(\Lambda\propto \Theta_{\mathrm{link}}/t_M\) | **≈ 1.12** | short |
| Control \(\Lambda_{\mathrm{ctrl}}\) (const) | **1.0** | short (v1-like) |
| Closed v4 \(M_f^{+1}\) | ≈ 0.89 (wrong way) | short |
| Closed inv-SNR \(q=1\) | ≈ 1.97 | short |

**Implication:** Primary \(\Lambda\) predicts only an \(\mathcal{O}(1)\) improvement over
unity (and still far from ~12). Unify **FALSIFY is the expected honest outcome**.
That remains a valid, high-value result: it closes this specific Hopf-geometric
coupling form under pre-registration.

At execution, the scoring script must print \(\Lambda\) per event and this honesty
block **before** any fit.

## Event roles

| Role | Events |
|------|--------|
| Design / sanity | GW150914, GW170814 |
| Primary target | **GW170809** (ROBUST_ANOMALY) |
| Systematics only | GW151012 — report only, never optimize |
| Holdout | GW170729 + any future BBH under same freeze |

## Gates

| Gate | Rule |
|------|------|
| **P-v5** | Network \(\Delta\chi^2\ge 6\), \(\lvert\hat\alpha_0\rvert>2\sigma\), same sign on H1/L1 if both significant |
| **B-v5** | \(\ln B_{10}>5\) on GW170809 under \(\alpha_0\sim\mathcal{N}(0,10^{-3})\) |
| **S-1** | Already established ROBUST_ANOMALY on GW170809 (re-check only if template channel changes) |
| **Unify** | Shared \(\alpha_0\): \(z=\lvert\alpha_0^{809}-\alpha_0^{914}\rvert/\sqrt{\sigma_{809}^2+\sigma_{914}^2}\le 3\) |
| **FAIL-v5** | Sign flip under mass jitter or approximant-only survival |

## SUCCESS / FALSIFY / NULL (v5 campaign)

| Verdict | Condition |
|---------|-----------|
| **SUCCESS** | GW170809: P-v5 PASS + \(\ln B_{10}>5\) **and** Unify PASS under primary \(\Lambda\) |
| **FALSIFY** | GW170809 residual-strong but Unify fails, or BF fails |
| **NULL** | Gate P-v5 fails on GW170809 |
| **Family closed** | If primary FALSIFYs on Unify → Hopf-lattice geometric scaling family **closed** under this pre-reg (new variable required for any v6) |

No SUCCESS from control or sensitivity forms alone.

## Implementation plan (when execution opens)

1. `src/premerger_mapping_v5.py` — `PremergerPhaseModelV5` with frozen \(\Lambda\) formula above  
2. Freeze \(\Theta_{\mathrm{link}}\) from `link_saturation_theta(LOCKED_WG)`; \(M_f\) from v4 catalog table  
3. Reuse network fit + Bayes factor machinery  
4. `scripts/premerger_mapping_v5_score.py` — honesty block **before** fits  
5. `tests/test_premerger_mapping_v5.py` — unit tests (no PE)  
6. Milestone: `docs/MILESTONE_PREMERGER_MAPPING_V5.md`  

## Explicit non-goals

- Not restoring any closed bulk-PE or remnant-mass power families  
- Not designing on GW151012  
- Not floating locks or post-hoc adjustment of \(\Lambda\)  
- Not claiming discovery from a single robust anomaly  
- Not treating \(\Lambda\) as an unrestricted free function of PE parameters  
- Not flipping to \(\Lambda\propto M_f^{+p}\) after seeing wrong-way / short ratios  

## Go / no-go

| Condition | Action |
|-----------|--------|
| This pre-reg accepted | Implement v5 + execute primary \(\Lambda\) |
| Primary form SUCCESS | Optional holdouts under same freeze |
| Primary form FALSIFY on Unify | Close this geometric-quantity family; new pre-reg required for any further mapping |
| GW151012 “improves” | Ignore for SUCCESS |

## Approval stamp

Pre-registered on 2026-07-10.  
Execution only when explicitly requested  
(“implement mapping v5” / “run V5 Hopf-lattice geometric quantity”).

Until then: **no new template runs** under this form. Score-only archival re-runs of
closed v1–v4 remain allowed.

## Cross-links

| Doc | Role |
|-----|------|
| `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` | Closure of v1–v4 |
| `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md` | Full archive of bulk-PE stretch |
| `docs/MILESTONE_FALSIFY_SYSTEMATICS.md` | S-1 (GW170809 ROBUST_ANOMALY) |
| `docs/PREDICTION_MODE.md` | Score-only discipline |
| `src/invariants.py` | `link_saturation_theta`, locks |
