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

## 2. Derive invariants → observables

- [x] Prediction record schema + GW delay/spectrum stubs (`src/predictions.py`)
- [ ] Expand Lagrangian / GW echo paper formulas into code with full coefficients
- [ ] Particle / spectral maps (where lattice stable configs meet data)

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

1. ~~Form + Gate P + scanner~~ (`src/premerger_*.py`, `scripts/premerger_phase_scan.py`)  
2. Run GW150914 → multi-event; injection recovery for \(\alpha\)  
3. If Gate P-D fails: polarization / class B modulation forms  

See `docs/PREMERGER_PHASE.md`.

### Later

- Matched-filter post-merger at \(f_{\mathrm{phys}}(M)\) with \(10^{-6}\) relative amp  
- Falsifier watch on sync branch (relative amp \(\gg 10^{-5}\))  

Core locks \(W_g\), \(\kappa\), braiding attractor remain available for other translations.

See `docs/falsification_criteria.md`.

## Seed lineage

Seeded from [kinaar8340/toe](https://github.com/kinaar8340/toe) — see `vendor/SEED.md`.
