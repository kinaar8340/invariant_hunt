# Milestone: GW151226 stress test (injections + band systematics)

**Date:** 2026-07  
**Command:**
```bash
python scripts/event_stress_test.py --event GW151226 --plot
```

## Why this event

Only BBH in the three-event sample that cleared **Gate C strict** and **LEE** under the catalog-wide band (50–900 Hz). Requires follow-up before weight is assigned.

## Band systematics @ s=1

| Band | Range (Hz) | Δχ² | MF SNR | C strict | LEE |
|------|------------|-----|--------|----------|-----|
| catalog_wide | 50–900 | 10.85 | 3.30 | Y | Y |
| 50 → 1.5 f_ring | 50–1154 | 9.39 | 3.06 | Y | Y |
| 0.5–1.5 f_ring | 385–1154 | 11.62 | 3.41 | Y | Y |
| 0.7–1.3 f_ring | 539–1000 | 12.23 | 3.50 | Y | Y |
| f_ring ± 150 | 620–920 | 25.26 | 5.03 | Y | Y |
| **gw150914_band (off)** | **50–300** | **34.14** | **5.84** | **Y** | **Y** |

## Injection recovery (catalog band)

| into | a_inj=0 Δχ² | a_inj=0 SNR | thr (strict) |
|------|-------------|-------------|--------------|
| residual | 10.85 | 3.30 | ~0.25 |
| **noise** | **4.65** | **2.16** | ~0.25 |

Pipeline remains sensitive (Gate B-net style: injections recover strongly).

## Verdict

**Does not hold under stress** (provisional hold criteria failed).

Reasons:

1. Catalog and narrow f_ring bands all pass strict — superficially robust.  
2. **Off-band 50–300 Hz (far below f_ring≈770 Hz) also passes, with the largest Δχ².** That is the opposite of a ringdown-localized echo: consistent with **broadband residual structure / systematics**, not a frequency-targeted ladder.  
3. Pure-noise floor is already high (Δχ²≈4.7, SNR≈2.2), so the noise model / short-segment variance for this event is less clean than GW150914.  
4. PE SNR only ~11 (vs ~54/39 for GW150914) — PE subtraction less constraining.

## Implication for the framework

- Multi-event **Gate D remains FAIL**.  
- GW151226 is **not** promoted to a detection candidate under these stress tests.  
- Highest-value physics-side next step: **amplitude-structure mapping** (or other observables), not further single-event retuning of GW151226 under the same template.

Core locks \(W_g\), \(\kappa\) still untouched.

## Outputs

- `outputs/benchmarks/GW151226_stress_test.json`
- `outputs/benchmarks/GW151226_stress_test.png`
- `outputs/benchmarks/GW151226_stress_test_injections.png`
