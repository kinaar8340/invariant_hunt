# Milestone: Multi-event whitened H1+L1 network (Gate C / D)

**Date:** 2026-07  
**Command:**
```bash
python scripts/multi_event_network.py --events GW150914,GW170104,GW151226 --plot
```

## Setup (common)

- Whitened H1+L1, coherent complex echo map, geometric delays from \(M_f\), \(\kappa\)
- Core locks fixed: \(W_g \approx 111.41\), \(\kappa = 0.85\)
- Event-dependent analysis band (lighter remnants → higher \(f_{\mathrm{high}}\))
- Gate C weak: Δχ²≥4, SNR≥2  
- Gate C strict: Δχ²≥6, SNR≥2  
- Gate D: Gate C strict on ≥3 events

## Results @ s=1

| Event | \(M_f\) | Band (Hz) | Δχ² | MF SNR | C weak | C strict | LEE scan |
|-------|---------|-----------|-----|--------|--------|----------|----------|
| GW150914 | 63.1 | 50–300 | 4.16 | 2.04 | Y | **n** | fail |
| GW170104 | 48.9 | 50–400 | 2.81 | 1.68 | n | **n** | fail* |
| GW151226 | 20.5 | 50–900 | 10.85 | 3.30 | Y | **Y** | pass† |

\* best raw Δχ²=4.24 @ s=1.2, LEE fail  
† best Δχ²=14.0 @ s=0.92, LEE thr≈10.1 → pass

**Gate C strict: 1/3**  
**Gate D: FAIL**

## Interpretation

1. **No multi-event consistency** under Gate C strict — only the lightest event (GW151226) clears the bar.  
2. GW150914 remains **marginal / weak-only**; GW170104 is a clean null under both bars.  
3. GW151226 is an **outlier of interest**, not a claim: higher band, lower PE SNR (~11), different mass scale. Needs dedicated injection recovery + band systematics before weight is given.  
4. Core invariants **unchanged**. Mapping still not established across the BBH sample.

## Follow-ups

1. Network injection recovery on GW151226 (same as GW150914 Gate B-net)  
2. Band robustness for GW151226 (narrower bands around \(f_{\mathrm{ring}}\))  
3. Amplitude-structure mapping if multi-event remains mixed/null  

Outputs: `outputs/benchmarks/multi_event_network_summary.json` and per-event `*_whitened_network.json`.
