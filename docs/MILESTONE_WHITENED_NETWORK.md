# Milestone: Whitened H1+L1 network likelihood (Gate C)

**Date:** 2026-07  
**Command:**
```bash
python scripts/network_whiten_scan.py --event GW150914 --detectors H1,L1 --plot
```

## What was built

1. **Welch PSD** from ~8 s pre-merger of the full 32 s public file (per detector)  
2. **Frequency-domain whitening** of the full file, then analysis cut  
3. **PE residual** in whitened domain (IMRPhenomD + lag + A₊,Aₓ per detector)  
4. **Network coherent echo fit**: shared \((a_c,a_s)\), per-detector leftover ringdown \(a_{0,d}\)  
5. **Delay-scale scan** \(s\in[0.8,1.2]\) with LEE \(thr'=thr+2\ln N\)

## GW150914 result

| Quantity | H1-only band-lim (v2) | Whitened H1+L1 |
|----------|----------------------|----------------|
| PE SNR proxy | ~11 (band-lim) | H1≈54, L1≈39 |
| Δχ² @ s=1 | 0.45 | **4.16** |
| MF SNR | 0.77 | **2.04** |
| Gate A / C nominal | Fail | **marginal PASS** |
| Best s | 1.00 | 0.96 (Δχ²=4.86) |
| Gate A′ / C + LEE | Fail | **FAIL** (need ≥10.1) |

## Interpretation

- Moving to **whitened multi-detector** likelihood is a real credibility upgrade: PE recovery becomes healthy and the network statistic is well-defined.  
- The echo mapping **crosses the weak Gate C threshold** by a hair (Δχ²=4.16, SNR=2.04).  
- Under **Gate C strict** (Δχ²≥6 for 2-dof) it **fails**.  
- It does **not** survive the **LEE-corrected** delay scan (max Δχ²=4.86 ≪ 10.1).  
- Core locks \(W_g\), \(\kappa\) still not moved; this is a **mapping + analysis** result.  
- **Do not claim detection.** Marginal single-event pass without full look-elsewhere on continuous phase, without PSD uncertainty, and without multi-event replication is at best a **follow-up target**.

## Network injection recovery (Gate B-net)

```bash
python scripts/network_injection_recovery.py --into residual --plot
python scripts/network_injection_recovery.py --into noise --plot
```

Places Δχ²≈4.2 on a calibrated a_inj curve; reports a_inj needed for Δχ²≥6.

## Reproduce

```bash
python scripts/network_whiten_scan.py --event GW150914 --detectors H1,L1 --plot
python scripts/network_injection_recovery.py --into residual --plot
```

Outputs:
- `outputs/benchmarks/GW150914_H1-L1_whitened_network.json`
- `outputs/benchmarks/GW150914_H1-L1_whitened_network.png`
- `outputs/benchmarks/GW150914_H1-L1_network_injection_residual.json`
