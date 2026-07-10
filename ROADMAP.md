# Invariant Hunt — Roadmap to a predictive model

This roadmap preserves the topological/geometric spirit of the TOE framework
while enforcing the structure needed for prediction and scientific credibility.

Empirical success is independent of any metaphysical framing: the model stands
or falls on quantitative, falsifiable forecasts.

## 1. Formalize core invariants (beyond numerical locking)

- [x] Canonical constants module (`src/invariants.py`): \(W_g \approx 350/\pi\), κ, braiding
- [x] Positional/phase map of \(350/\pi\) (`src/positional.py`, `docs/positional_350_pi.md`)
- [x] Meta-optimizer with positional residual (`scripts/meta_optimize_invariants.py`)
- [ ] Analytic stability proof / derivation of why \(W_g\) locks (not only numerics)
- [ ] Wide sweeps: topologies, perturbations, seeds (`epoch_bake_sweep`, `pde_relaxation`)

### Phase 1 — Action principle (SM/GR gap roadmap)

- [x] **1.1** Unified action scaffold: SU(3)×SU(2)×U(1) + Hopf + holonomy/braiding  
      (`src/action_principle.py`, `scripts/action_principle_check.py`, Gate A-P)  
      → `docs/MILESTONE_ACTION_PRINCIPLE.md`, `papers/Lagrangian_Derivation.tex`
- [x] **1.2** Holonomy / gauge meta-sweeps with locks fixed (Gate H-S)  
      (`src/gauged_meta_sweep.py`, `meta_optimize_invariants.py --locks-fixed`)  
      → `docs/MILESTONE_GAUGED_META_SWEEP.md`
- [x] **1.3** Relativistic completion peer-ready `.tex` aligned with `eq:unified-action`  
      → `papers/Relativistic_Completion.tex`, `docs/MILESTONE_RELATIVISTIC_COMPLETION.md`

## 2. Derive invariants → observables

- [x] Prediction record schema + GW delay/spectrum stubs (`src/predictions.py`)
- [x] Lagrangian free-energy + unified action symbolic densities (Phase 1.1)
- [x] **Phase 2.1** SM representations + lattice mode map (Gate SM-1)  
      (`src/sm_mapping.py`, `scripts/sm_gate_check.py`)  
      → `docs/MILESTONE_SM_PARTICLE_MAPPING.md`, `papers/SM_Derivation.tex`
- [x] **Phase 2.2** Topological Yukawa + PDG χ² (Gate SM-2 mass upgrade)  
      (`src/sm_yukawa.py`, `scripts/sm_yukawa_ansatz.py`)  
      → `docs/MILESTONE_SM_YUKAWA.md`
- [x] **Phase 2.3** One-loop SM gauge RG + Gate SM-3 complete  
      (`src/sm_rg.py`, `scripts/sm_rg_flow.py`)  
      → `docs/MILESTONE_SM_RG.md`
- [ ] Expand GW echo paper formulas into code with full coefficients

## 3. Generate specific, falsifiable predictions

- [x] Positional GW echo delay ladder + spectral peak (`scripts/forward_gw_signal.py`)
- [ ] Non-local / observer-synchronization experimental designs
- [ ] High-precision deviation forecasts (clocks, interferometry) with timestamps

## 4. Test against existing data

- [x] Synthetic head-to-head scaffold (`scripts/compare_benchmark.py`)
- [x] Map ladder → GW150914 + public GWOSC H1 strain (`map_event_echoes`, `--event GW150914`)
- [x] PE residual baseline: GWTC-1 medians → IMRPhenomD (`--baseline pe`)
- [ ] Whitened likelihood with official PSD; multi-detector coherence
- [ ] Full bilby/LALInference posterior predictive waveforms (vs median point estimate)
- [ ] Pulsar timing / QPO bands (~350–600 Hz overlap) statistical comparison

## 5. Propose new tests

- [ ] Instrument-ready proposals (LIGO upgrades, PTAs, tabletop gravity)
- [ ] Phase-dependent signatures unique to Hopf-lattice holonomy

## 6. Reproducibility and transparency

- [x] Open scripts, configs, JSON prediction bundles
- [x] Versioned schema (`invariant_hunt.*.v1`)
- [ ] Automated CI tests for lock residuals and prediction schema
- [ ] Modular: optimizer → prediction generator (partially done)

## 7. Iterate with falsification

Each prediction carries a `falsify_if` string. Example checkpoints:

| Prediction | Fail condition | Component to revise |
|------------|----------------|---------------------|
| Echo delay ladder | No structure within uncertainty at \(\delta t_n\) | Positional map / κ |
| Peak frequency | No feature within 10% of \(f_{\mathrm{peak}}\) | `scale_hz` / winding map |
| Meta lock | Best \(w_{g,\mathrm{base}}\) far from 350 under wide priors | Island loss / conduit |

## Campaign status

**Positional post-merger echo-ladder mapping: closed** — constrained, not supported under gated multi-event analysis.  
See `docs/CAMPAIGN_ECHO_MAPPING.md`.

| Done | Outcome |
|------|---------|
| PE residual, coherent, LEE | Marginal / fail Gate A on H1 |
| Whitened H1+L1 + injections | Sensitive (B-net pass); C strict mostly fail |
| Multi-event Gate D | **Fail** (1/3; GW151226 fails band stress) |
| Amp-structure v3 | Low leverage; Gate D still fail |

### Analytic phase (done)

- ~~Analytic invariant → echo signal~~ (`src/echo_theory.py`, `docs/ANALYTIC_ECHO_PREDICTION.md`)  
  Sync branch predicts undetectable residual ladders; campaign nulls consistent.

### Active: pre-merger topological phase (Gate P)

1. ~~Form + Gate P + scanner~~  
2. ~~Injection recovery (Gate B-P)~~  
3. ~~PE approximant robustness~~ (GW150914)  
4. ~~Expanded multi-event + PE draws~~ — P-D **PASS** 4/7  
5. ~~Follow-up draws/B-P~~ — 814 core; **818 demoted**  
6. ~~GW170608 scrutiny~~ — **demoted** (high corr(r,τ), approx Δχ² swing, mass sign flip)  
7. ~~Core lock + forward band~~ — α ∈ [2.9e-5, 1.2e-4]; GW170823 → NULL  
8. ~~**Predictive freeze**~~ — SUCCESS/FALSIFY/NULL pre-registered; in-catalog closed  
   → `docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md`

See `docs/PREMERGER_PHASE.md`.

### Phase 1 action principle — complete (scaffolding)

Pre-merger freeze remains closed. Core locks frozen.

1. ~~**1.1** Unified action + Gate A-P~~ → `docs/MILESTONE_ACTION_PRINCIPLE.md`  
2. ~~**1.2** Meta-sweep holonomy/gauge jitter (Gate H-S)~~ → `docs/MILESTONE_GAUGED_META_SWEEP.md`  
3. ~~**1.3** Relativistic completion paper~~ → `docs/MILESTONE_RELATIVISTIC_COMPLETION.md`  

### Active: Phase 2 SM particle content

Core locks frozen; pre-merger freeze closed.

1. ~~**2.1** Lattice → boson/fermion representations (Gate SM-1)~~  
   → `docs/MILESTONE_SM_PARTICLE_MAPPING.md`  
2. ~~**2.2** Topological Yukawa + PDG χ² (Gate SM-2 mass)~~  
   → `docs/MILESTONE_SM_YUKAWA.md`  
3. ~~**2.3** Full anomaly + RG flow simulator (Gate SM-3)~~  
   → `docs/MILESTONE_SM_RG.md`  

### Phase 2 SM content — complete (scaffolding + gates)

SM-1 / SM-2 mass / SM-3 all executable with locks frozen.

### Phase 3 emergent gravity — complete (scaffolding)

Core locks frozen; pre-merger freeze closed.

1. ~~**3.1–3.2** Stress-energy + Einstein scaffold + \(G_N\) schema + Newtonian limit (Gate GR-1)~~  
2. ~~**3.3** Analytic precision targets (Gate GR-2 structure)~~  
3. ~~**3.4** Tight SI bridge + lattice→metric Poisson PDE (Gate GR-3)~~  
4. ~~**Close-out + integration snapshot**~~ → `docs/MILESTONE_PHASE3_CLOSEOUT.md`  
   `python scripts/integration_status.py --run-gates`

### Prediction mode — true held-out scorecard (closed for band claim)

| Event | Verdict |
|-------|---------|
| GW170809 | **FALSIFY** |
| GW170729 | **NULL** |
| GW151012 | **FALSIFY** |

**0 SUCCESS / 2 FALSIFY / 1 NULL → universal α-band forward claim demoted.**  
Band and core locks **not** re-fit. See `docs/MILESTONE_HELD_OUT_TRUE_BBH.md`.  

Bayes factor complement (no band re-fit): `scripts/premerger_bayes_factor.py`  
→ `docs/PREMERGER_BAYES_FACTOR.md`  

Gate S-1 complete (canonical n_draws≥12):  
- GW170809 → **ROBUST_ANOMALY**  
- GW151012 → **SYSTEMATICS_RISK**  

Bulk PE-power mapping (executed and **stopped**):  
- v2 mass \(p=1\) → **FALSIFY** (`docs/MILESTONE_PREMERGER_MAPPING_V2.md`)  
- v3 inv-SNR \(q=1\) + distance \(s=1\) → **FALSIFY**; family closed  
  (`docs/MILESTONE_PREMERGER_MAPPING_V3.md`)  
- Close-out: `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md`  

**Active (pre-merger):** score-only under frozen locks; residual anomaly on GW170809
stands **without** a shared \(\alpha_0\) map. **No further bulk PE-power mapping**
unless a *new physical variable* is separately pre-registered (`docs/PREREG_*.md`).

**Archive:** `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md` — chapter closed; repro index frozen.

**Mapping v4 remnant mass \(M_f\):** executed → **FALSIFY** (Unify \(z\approx 30.6\));  
family closed — `docs/MILESTONE_PREMERGER_MAPPING_V4.md`.  
Further mapping only via new physical-variable PREREG.

### Later

- Matched-filter post-merger at \(f_{\mathrm{phys}}(M)\) with \(10^{-6}\) relative amp  
- Falsifier watch on sync branch (relative amp \(\gg 10^{-5}\))  
- Phase 4 quantization pathway; arXiv packaging polish  

Core locks \(W_g\), \(\kappa\), braiding attractor remain available for other translations.

See `docs/falsification_criteria.md`.

## Seed lineage

Seeded from [kinaar8340/toe](https://github.com/kinaar8340/toe) — see `vendor/SEED.md`.
