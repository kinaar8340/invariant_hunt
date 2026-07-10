# Milestone: PE approximant robustness (pre-merger Gate P)

**Event:** GW150914  
**Commands:**
```bash
python scripts/premerger_pe_robustness.py --event GW150914 --plot
python scripts/premerger_mass_scale.py --events GW150914,GW170104,GW151226
```

## Approximant scan (network Gate P)

| Approximant | α_hat | Δχ² | Gate P |
|-------------|-------|-----|--------|
| IMRPhenomD | 6.93e-5 | 30.4 | **PASS** |
| SEOBNRv4_opt | 8.25e-5 | 51.3 | **PASS** |
| IMRPhenomXAS | 8.67e-5 | 48.0 | **PASS** |
| IMRPhenomXP | 8.50e-5 | 49.4 | **PASS** |

- **4/4** pass  
- **Sign stable** (all positive)  
- Relative spread std/|mean| ≈ **0.08** (tight)

L1 remains weak individually; network still H1-driven. Sign consistency rule does not fail because L1 is not >2σ on opposite sign.

## PE parameter jitter (IMRPhenomD)

| Jitter | α_hat | Δχ² | Gate P |
|--------|-------|-----|--------|
| nominal | 6.93e-5 | 30.4 | PASS |
| m +3% | 1.16e-4 | 93.2 | PASS |
| **m −3%** | 1.91e-5 | **2.2** | **fail** |
| d ±15% | 6.93e-5 | 30.4 | PASS |
| m+3% & d+15% | 1.16e-4 | 93.2 | PASS |

**5/6** pass. Distance jitter is irrelevant after free A₊,Aₓ. **Mass −3%** drops Δχ² below Gate P — residual phase is **chirp-mass sensitive** (expected if PE mismatch couples to Φ_orb).

## Mass-scaled multi-event

Only events that already pass Gate P enter β = α (M_f/M_ref)^p consistency.  
With current multi-event scan, **only GW150914** passes network Gate P (H1/L1 sign flips kill the others) → mass scaling **cannot** produce Gate P-D.

## Verdict

| Check | Result |
|-------|--------|
| PE approximant robustness (GW150914) | **YES (provisional)** |
| Mass-scaled P-D | **FAIL** (insufficient multi-event passes) |
| Multi-event P-D | **FAIL** (unchanged) |

**Interpretation:** The GW150914 excess is **not** an IMRPhenomD artifact — it survives SEOBNR and PhenomX families with stable positive α. It remains a **single-event**, H1-dominated result that is **sensitive to PE mass**, so it is still not a multi-event topological claim. Next: more events with strict sign consistency, or test whether mass-matched PE draws remove the excess.
