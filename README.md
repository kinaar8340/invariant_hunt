# Invariant Hunt

**From locked topological/geometric invariants to falsifiable predictions.**

Seeded from [kinaar8340/toe](https://github.com/kinaar8340/toe) (Flux Flywheels, Gauged Hopf Lattice).
This repo focuses the TOE machinery on a single scientific path:

1. **Hunt** robust invariants (meta-optimization, sweeps, PDE relaxation)
2. **Interpret** \(W_g \approx 350/\pi\) as a **positional/phase** lattice coordinate
3. **Map** invariants → observables with explicit formulas
4. **Predict** quantitative signals (GW echoes/bursts first)
5. **Compare** head-to-head on shared benchmarks
6. **Falsify** with documented fail conditions

Metaphysical or theological motivation may inspire the search; **claims are evaluated only on empirical and mathematical merits**.

## Quick start

```bash
cd ~/Projects/invariant_hunt
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Analytic meta-hunt (no GPU / no full conduit required)
python scripts/meta_optimize_invariants.py --dry-run --trials 50

# Forward GW echo train from locked invariants
python scripts/forward_gw_signal.py --mass 30 --sites 5 --plot

# Synthetic benchmark: baseline ringdown vs positional echoes
python scripts/compare_benchmark.py --inject-echoes

# Map ladder → public GW150914 and compare on GWOSC H1 strain
python scripts/map_event_echoes.py --event GW150914 --benchmark --plot

# Unit tests (core math; no torch required)
python -m pytest tests/ -q
```

### Public event mapping (GW150914)

The positional echo ladder is evaluated at the published remnant mass (~62 M☉):

| Mode | Formula | First delay (GW150914) |
|------|---------|-------------------------|
| `geometric` (default) | \(\delta t_n=(GM/c^3)\,2\pi\,n\,(1+\kappa)\) | ~3.5 ms (LIGO-resolvable) |
| `phase_unit` | \(\delta t_n=(GM/c^3)\,2\pi\,(n/W_g)\,(1+\kappa)\) | ~µs (sub-sample @ 4 kHz) |

```bash
python scripts/compare_benchmark.py --event GW150914 --detector H1 --plot
```

Strain is cached under `data/gwosc/` (downloaded from GWOSC on first run).
Outputs land in `outputs/benchmarks/` and `outputs/predictions/`.
**Caveat:** templates are amplitude-fitted damped sinusoids, not NR PE waveforms.

Full conduit evaluation (from TOE):

```bash
python scripts/meta_optimize_invariants.py --trials 30
python scripts/run_reproduction.py --trials 30
```

## Project layout

```
invariant_hunt/
├── src/
│   ├── invariants.py      # W_g, κ, braiding locks & residuals
│   ├── positional.py      # 350/π as phase / lattice site
│   ├── predictions.py     # InvariantSet → PredictionRecord
│   ├── conduit.py         # RubikConeConduit (seeded from toe)
│   ├── config.py
│   └── relaxation_survival.py
├── scripts/
│   ├── meta_optimize_invariants.py   # positional meta-optimizer
│   ├── forward_gw_signal.py          # concrete GW prediction pipeline
│   ├── compare_benchmark.py          # χ² head-to-head scaffold
│   ├── epoch_bake_sweep.py           # from toe
│   ├── pde_relaxation.py
│   └── run_reproduction.py
├── docs/
│   ├── positional_350_pi.md
│   └── invariants_to_observables.md
├── papers/                # Burst-threshold derivation (tex)
├── ROADMAP.md
└── vendor/SEED.md
```

## Canonical lock

| Quantity | Value | Notes |
|----------|-------|--------|
| \(w_{g,\mathrm{base}}\) | 350 | Action-like base |
| \(W_g\) | \(350/\pi \approx 111.408\) | Geometric winding |
| \(\kappa\) | ≈ 0.85 | Holonomy / burst lift |
| \(\phi_b\) | ≈ 0.8145 | Braiding attractor |
| \(\theta_{\mathrm{crit}}\) | \(\pi(1+\kappa)\approx 5.81\) | Burst threshold |

See `docs/positional_350_pi.md` for the phase/lattice reading of bursts.

## Status

Early scaffold: formalized invariants, positional framing, prediction schema,
forward GW toy signal, synthetic benchmark. Next: real datasets and paper-grade
mappings. Track progress in [ROADMAP.md](ROADMAP.md).

## License

MIT — see [LICENSE](LICENSE).
