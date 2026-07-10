# Milestone: GW170608 scrutiny (B-P + PE approximants)

**Commands:**
```bash
python scripts/premerger_injection_recovery.py --event GW170608 --plot
python scripts/premerger_pe_robustness.py --event GW170608 --plot
```

## B-P injection

| into | α=0 Gate P | Recovery |
|------|------------|----------|
| noise | **fail** (Δχ²=0.49) | Clean FP control; thr ~2e-5 |
| residual | pass (real excess) | Additive |

**Real:** α≈1.04e-4, Δχ²≈1316, Gate P PASS.

### Critical systematics

| Check | GW170608 | GW170814 (clean) |
|-------|----------|------------------|
| corr(r, τ) H1 | **+0.229** | +0.020 |
| corr(r, τ) L1 | **+0.125** | +0.030 |
| power_frac along τ H1 | **5.2%** | 0.04% |

Residual is **aligned with τ** on GW170608 — PE mismatch can dump power into the phase basis. Time cuts do not remove it (Δχ² stays ~1300).

## PE approximant robustness

| Approximant | α_hat | Δχ² | Gate P |
|-------------|-------|-----|--------|
| IMRPhenomD | 1.04e-4 | **1316** | PASS |
| SEOBNRv4_opt | 7.04e-5 | **584** | PASS |
| IMRPhenomXAS | 4.05e-5 | **195** | PASS |
| IMRPhenomXP | 1.06e-4 | **1383** | PASS |

- 4/4 pass, all + sign  
- **std/|mean| of α ≈ 0.34** (vs ~0.08 on GW150914)  
- Δχ² swings by factor **~7** across approximants  

### Mass jitter (IMRPhenomD)

| Case | α | Δχ² | Gate P |
|------|---|-----|--------|
| nominal | +1.04e-4 | 1316 | PASS |
| **m+3%** | **−8.9e-6** | 8.6 | PASS (barely) |
| m−3% | +4.7e-5 | 302 | PASS |

**Mass +3% flips the sign of α** — not a stable physical coupling.

## Verdict: **DEMOTE GW170608**

| Criterion | Result |
|-----------|--------|
| PE draws | 7/8 pass (looked OK) |
| B-P noise FP | Clean |
| corr(r, τ) | **Fail** — high alignment with residual |
| Approximant Δχ² stability | **Fail** — huge swing |
| Mass jitter sign | **Fail** — sign flip |

**Do not promote to core.** High-Δχ² “PASS” is PE-systematics–dominated.

## Locked core (pre-merger Gate P)

| Event | Role |
|-------|------|
| **GW150914** | Core (draws, approximants, B-P) |
| **GW170814** | Core (draws, B-P, moderate Δχ², low corr) |
| ~~GW170608~~ | Demoted after scrutiny |
| ~~GW170818~~ | Demoted (4/8 draws) |

Credible multi-event set: **n = 2**, same positive α ~ (7–8)×10⁻⁵.
