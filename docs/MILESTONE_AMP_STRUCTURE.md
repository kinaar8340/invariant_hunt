# Milestone: Amplitude-structure mapping (v3)

**Date:** 2026-07  
**Command:**
```bash
python scripts/amp_structure_scan.py --plot
```

## What changed

Relative step weights \(w_n\) (delays and core locks unchanged):

| Structure | Formula | Physics intent |
|-----------|---------|----------------|
| `geometric` | \(w_n = a_0^n\) | Fixed decay (v2 baseline) |
| `braiding` | \(w_n = a_0^n(1+\beta\cos\psi_n)\) | Fiber braiding modulation |
| `braiding_lock` | \(w_n = a_0^n e^{-\gamma\,\mathrm{ang}(\psi_n,\phi_b^*)}\) | Prefer braiding attractor |
| `flux_kappa` | \(w_n = (a_0\cdot\kappa/\kappa_0)^n\) | Holonomy / flux-shed rate |
| `hopf_winding` | \(w_n = a_0^n(1+\alpha\cos(2\pi n/W_g))\) | Full-winding quasi-period |

Weights L2-normalized; overall scale free in coherent \((a_c,a_s)\).

## Multi-event Δχ² / SNR @ s=1 (whitened H1+L1)

| structure | GW150914 | GW170104 | GW151226 | strict # |
|-----------|----------|----------|----------|----------|
| geometric | 4.16 / 2.04 | 2.81 / 1.68 | 10.85 / 3.29 | **1/3** |
| braiding | 4.14 / 2.04 | 2.82 / 1.68 | 10.87 / 3.30 | **1/3** |
| braiding_lock | 3.64 / 1.91 | 2.90 / 1.70 | 11.37 / 3.37 | **1/3** |
| flux_kappa | 4.16 / 2.04 | 2.81 / 1.68 | 10.85 / 3.29 | **1/3** |
| hopf_winding | 4.15 / 2.04 | 2.81 / 1.68 | 10.87 / 3.30 | **1/3** |

Best by strict count then mean Δχ²: `braiding_lock` (still **1/3**).  
**Gate D: FAIL** for every structure.

## Interpretation

1. Amplitude-structure variants **barely move** the network statistics (Δχ² changes ≪ 1 on most events).  
2. Multi-event picture is **stable under mapping v3**: only GW151226 clears Gate C strict; it already failed stress tests for band localization.  
3. The bottleneck is **not** the fixed \(0.35^n\) decay alone — timing/template domain mismatch or residual systematics dominate.  
4. Core locks remain fixed; this was a controlled mapping experiment.

## Implication

Further fine-tuning of step weights under the same post-merger coherent ladder is **low leverage**. Higher-value directions:

- Different **observable domain** (not only this echo train)  
- Stronger PE / PSD / multi-IFO modeling  
- Or analytic invariant→observable derivation that predicts *whether* echoes should appear at all for heavy vs light BBHs  

## Outputs

- `outputs/benchmarks/amp_structure_scan.json`
- `outputs/benchmarks/amp_structure_scan.png`
- Module: `src/amp_structure.py`
