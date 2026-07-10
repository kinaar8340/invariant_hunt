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
- [ ] NR / published GR PE baselines (replace toy damped-sinusoid family)
- [ ] Whitened likelihood with official PSD; multi-detector coherence
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

## Immediate next actions

1. Run `python scripts/meta_optimize_invariants.py --dry-run --trials 50`
2. Run `python scripts/forward_gw_signal.py --plot`
3. Run `python scripts/compare_benchmark.py --inject-echoes`
4. Pick one real public GW event and replace the synthetic `obs` in the benchmark
5. Port analytic sections from TOE papers into `src/predictions.py`

## Seed lineage

Seeded from [kinaar8340/toe](https://github.com/kinaar8340/toe) — see `vendor/SEED.md`.
