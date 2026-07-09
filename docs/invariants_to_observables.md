# Invariants → observables

## Pipeline

```
meta_optimize_invariants  →  InvariantSet (W_g, κ, braiding)
         ↓
   PositionalPhase (n, φ)
         ↓
   PredictionRecord (value, uncertainty, falsify_if)
         ↓
   forward_gw_signal / compare_benchmark
         ↓
   public data / instruments
```

## Mapping table (current)

| Invariant | Symbol | Observable | Module |
|-----------|--------|------------|--------|
| Geometric winding | \(W_g = w_{g,\mathrm{base}}/\pi\) | Echo delay ladder, spectral scale | `predictions.gw_echo_delay` |
| Holonomy | \(\kappa\) | Delay factor \((1+\kappa)\), \(\theta_{\mathrm{crit}}\) | `invariants.burst_threshold` |
| Braiding phase | \(\phi_b\) | Phase offset in echo train | `forward_gw_signal` |
| Lattice index | \(n\) | Discrete delay / alignment site | `positional.PositionalPhase` |

## Formulas (v0.1)

**Echo delay** (toy, documented for replacement by full paper derivation):

\[
\delta t_n = \frac{GM}{c^3}\cdot 2\pi\cdot\frac{n}{W_g}\cdot(1+\kappa)
\]

**Peak frequency proxy**:

\[
f_{\mathrm{peak}} \approx f_{\mathrm{scale}}\cdot\frac{W_g}{2\pi}
\times\text{(mild positional modulation)}
\]

## Expanding the map

1. Lift formulas from `toe` papers: Lagrangian, GW Echo Derivation, Observer Sync.
2. Wire each formula to a `PredictionRecord` with units and uncertainty.
3. Attach a dataset ID and comparison script for every prediction domain.

## Statistical standard

Claims of “better than mainstream” require:

- Same public dataset and preprocessing
- Documented baseline (GR waveform, null, etc.)
- \(\chi^2\) / likelihood ratio / posterior predictive checks
- Reproducible scripts (this repo’s `compare_benchmark.py` is the template)
