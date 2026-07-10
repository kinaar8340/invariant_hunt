# Milestone: Pre-merger α injection recovery (Gate B-P)

**Event:** GW150914  
**Command:**
```bash
python scripts/premerger_injection_recovery.py --event GW150914 --plot
```

## Real residual (baseline)

| Quantity | Value |
|----------|-------|
| Network \(\hat\alpha\) | \(6.93\times 10^{-5} \pm 1.26\times 10^{-5}\) (~5.5σ) |
| Δχ² | 30.4 |
| Gate P | PASS (H1-driven; L1 weak) |

## Systematics diagnostics

| Check | Result |
|-------|--------|
| corr(r, τ) H1 | +0.051 (low) |
| corr(r, τ) L1 | +0.004 (negligible) |
| Power frac along τ | H1 0.26%, L1 ~0 |
| Time cuts t_end ∈ {−0.2…−0.02} | All Gate P pass; α stable ~7–10×10⁻⁵ |

Low residual–τ correlation argues against a pure dump of PE residual power into the basis; time-cut stability is good.

## Injection recovery

### Into pure whitened noise

| α_inj | α_hat | frac | Δχ² | Gate P |
|-------|-------|------|-----|--------|
| 0 | 8.1e-6 | — | 0.41 | **no** (clean FP) |
| 2e-5 | 3.6e-5 | 1.80 | 8.2 | YES |
| 7e-5 | 6.2e-5 | 0.88 | 24 | YES |
| 2e-4 | 2.0e-4 | 0.98 | 241 | YES |
| 5e-4 | 4.8e-4 | 0.97 | 1479 | YES |

**False Gate P at α=0 (noise): fail** — pipeline not freely firing on noise.

### Into PE residual (additive)

Recovered α ≈ α_residual + α_inj (linear).  
Thr for Gate P on residual background is already met at α_inj=0 because real residual passes.

## Calibration of the real result

- Real |α| ~ 7×10⁻⁵ sits **above** the noise recovery thr (~2×10⁻⁵).  
- Noise false-positive controlled for this seed.  
- **Still not a claim:** multi-event Gate P-D fails (sign flips); only one event fully passes network Gate P; L1 is weak on GW150914.

## Status

| Gate | Result |
|------|--------|
| B-P (injection sensitivity) | **Pass** on noise |
| P (GW150914 network) | Pass (single-event) |
| P-D (multi-event) | **Fail** |

Next: multi-event only after PE approximant / band systematics; do not refine form until then.
