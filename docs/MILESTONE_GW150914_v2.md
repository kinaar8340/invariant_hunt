# Milestone: GW150914 PE residual — echo mapping v1 → v2

**Date:** 2026-07  
**Repo:** [kinaar8340/invariant_hunt](https://github.com/kinaar8340/invariant_hunt)  
**Event:** GW150914 / H1 public GWOSC strain  
**Baseline:** GWTC-1 Overall_posterior medians → IMRPhenomD (PyCBC), lag + (A₊, Aₓ)  
**Observation:** post-merger PE residual (band-limited white-noise model)

## Separation of concerns

| Layer | Status after this milestone |
|-------|----------------------------|
| Core locks \(W_g \approx 350/\pi\), \(\kappa \approx 0.85\), braiding attractor | **Unchanged** — not constrained to move by this null |
| Echo **mapping** (how locks → waveform) | **v1 fail → v2 fail** on this event/setup |
| Test infrastructure | PE residual, diagnostics, injections, coherence, LEE |

A failed mapping on one event is **not** a falsification of the Hopf-lattice locks.

## Mapping versions

### v1 — independent real amplitude
- Geometric delays \(\delta t_n = (GM/c^3)\,2\pi\,n\,(1+\kappa)\)
- Relative weights \(0.35^n\), fixed braiding phase per step
- Single real scale \(a_1\) on the summed train

### v2 — coherent complex amplitude (+ optional delay scan)
- Same delays and relative weights
- Shared complex amplitude \((a_c, a_s)\) → \(|A|\), \(\varphi\)
- Optional \(s \in [0.8,1.2]\) on \(\delta t_n \to s\cdot\delta t_n\) with LEE \(thr' = thr + 2\ln N\)

## Quantitative results (H1)

| Quantity | v1 | v2 |
|----------|----|----|
| Δχ² @ \(s=1\) | ~0.04 | **0.45** |
| Echo strength | \(a_1 \approx 0\) | \|A\| ~ 10⁻²², MF SNR **≈ 0.77** |
| Best delay scale | — | **s = 1.00** |
| Gate A (nominal) | Fail | **Fail** |
| Gate A′ (best + LEE, thr≈10.1) | — | **Fail** |
| Gate B (injection recovery) | Pass | **Pass** (thr \(a_{\mathrm{inj}}\gtrsim 0.56\)) |

Sources:
- `outputs/benchmarks/GW150914_H1_pe_geometric.json`
- `outputs/benchmarks/GW150914_H1_residual_diagnostics.json`
- `outputs/benchmarks/GW150914_H1_injection_residual.json`
- `outputs/benchmarks/GW150914_H1_coherent_scan.json`

## Interpretation

1. Coherence improved Δχ² slightly but not into a detection regime.  
2. No evidence for a retimed ladder (scan maximum at geometric \(s=1\)).  
3. Pipeline is sensitive (Gate B); the null is not a dead fitter.  
4. **Conclusion:** this invariant→post-merger-echo translation does not describe GW150914 H1 PE residual structure under the current noise model.

## Reproduce

```bash
python scripts/compare_benchmark.py --event GW150914 --baseline pe --plot
python scripts/inspect_residual.py --plot
python scripts/injection_recovery.py --into residual --plot
python scripts/coherent_echo_scan.py --event GW150914 --plot
```

## Next forks (do not mix with moving core locks)

1. **Amp structure** — braiding/flux-dependent visibility instead of fixed \(0.35^n\)  
2. **Stronger analysis** — PSD whitening + H1+L1 coherent likelihood  
3. **Other observables** — alternate bands / pre-merger / non-GW domains  

Gates: `docs/falsification_criteria.md`.
