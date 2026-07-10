# Milestone: PE draws on P-D passers + B-P on GW170814

**Command:**
```bash
python scripts/premerger_followup_passers.py --plot --n-draws 8 --inject-events GW170814
```

## PE posterior draws (n=8, IMRPhenomD)

| Event | Pass | Median α (all) | Median Δχ² | Sign maj. | Verdict |
|-------|------|----------------|------------|-----------|---------|
| GW170608 | **7/8** | +5.9e-5 | **405** | 100% + | Stable sign; **high Δχ²** remains |
| GW170814 | **7/8** | +7.6e-5 | **17.5** | 100% + | **Cleanest** passer |
| GW170818 | **4/8** | +4.4e-4 | **176** | 100% + | **Unstable** under draws — demote |

### Scrutiny notes

- **GW170608:** Pass fraction high and α positive, but median Δχ² ~400 still screams PE/template mismatch risk even after draws. Keep as provisional passer with caution.  
- **GW170814:** Moderate Δχ², both detectors same sign, stable under draws — **best multi-event anchor after GW150914**.  
- **GW170818:** Only half of PE draws pass Gate P → **do not count as a solid multi-event member** despite median-PE pass.

## B-P injection (GW170814)

| into | α=0 Gate P | thr α for Gate P | Recovery |
|------|------------|------------------|----------|
| **noise** | **fail** (Δχ²=0.1) | ~1×10⁻⁴ | Good frac→1 for α≥1e-4 |
| residual | pass (real excess) | ~2×10⁻⁵ | Additive α_real+α_inj |

Residual–τ correlation: H1 +0.02, L1 +0.03 (low).

**Real |α|≈7.5e-5** sits **below** the pure-noise Gate P thr (~1e-4) but above residual background thr. Calibrated: detectable-ish, not deep in the injection-confident zone for noise-only.

## Updated multi-event interpretation

| Tier | Events | Notes |
|------|--------|-------|
| **Core (draws-stable)** | GW150914 (9/10), **GW170814 (7/8)** | Moderate Δχ² preferred |
| **Provisional** | GW170608 (7/8 draws, high Δχ²) | Keep but flag |
| **Demote** | GW170818 (4/8 draws) | Median-PE pass not enough |
| Fail sign | GW170104, GW151226, GW170823 | Systematics |

**Gate P-D still formally PASS** on original median-PE rules (4 positive passers), but after this follow-up the **credible core is closer to 2–3 events** (150914 + 170814 ± 170608).

## Status table

| Check | Result |
|-------|--------|
| PE draws on new passers | 608 & 814 solid; **818 weak** |
| B-P on second event (170814) | Noise FP clean; recovery OK |
| Claim level | Still **provisional multi-event** — tightened by demoting 818 |

## Next (if continuing)

1. B-P on GW170608 (does high Δχ² inject/recover cleanly?)  
2. Approximant robustness on GW170814  
3. Only then revisit mass-scaled β on the **draw-stable** subset  
