# Prediction mode (pre-merger freeze)

**Status:** active  
**Date:** 2026-07-09

Theory freezes (Phases 1–3) stay closed. Operational work is **score-only**
against the pre-registered α band.

## Frozen rule

```bash
python scripts/premerger_core_predict.py
python scripts/premerger_core_predict.py --predict-event <BBH>
```

| | |
|--|--|
| Core | GW150914, GW170814 |
| Band | \(\hat\alpha \in [2.88\times10^{-5},\,1.15\times10^{-4}]\) (positive) |
| Template | \(\Delta\phi=\alpha\,W_g\,\Phi_{\mathrm{orb}}\cos\phi_b\) |
| Locks | \(W_g=350/\pi\), \(\kappa\approx0.85\), \(\phi_b\approx0.8145\) |

| Verdict | Condition |
|---------|-----------|
| **SUCCESS** | Gate P PASS, \(\hat\alpha>0\), in band |
| **FALSIFY** | Gate P PASS outside band or strongly negative |
| **NULL** | Gate P fail — **not** a counterexample |

## Event classes

| Class | Events | Role |
|-------|--------|------|
| Core | GW150914, GW170814 | Band anchors (do not re-fit) |
| Demoted | GW170608, GW170818 | Do not re-promote without new PE systematics |
| In-catalog NULL | GW170104, GW151226, GW170823 | Reaffirmation only |
| **True held-out** | **GW151012, GW170729, GW170809** | Prediction-mode scores |

True held-outs were **not** used in freeze demotion/NULL training. They are
GWTC-1 BBHs with public PE + H1/L1 strain registered for scoring.

```bash
# Preferred first true held-out
python scripts/premerger_core_predict.py --predict-event GW170809

# Other true held-outs
python scripts/premerger_core_predict.py --predict-event GW170729
python scripts/premerger_core_predict.py --predict-event GW151012
```

## What not to do

- Do not re-open core locks or α band after a NULL  
- Do not re-fit on held-outs after seeing the score  
- Do not treat NULL as FALSIFY  

## Scores to date

| Event | Class | Gate P | \(\hat\alpha\) | Verdict |
|-------|-------|--------|----------------|---------|
| GW170823 | In-catalog reaffirmation | fail | \(-4.3\times10^{-4}\) | NULL |
| **GW170809** | **True held-out** | **PASS** | \(+8.58\times10^{-4}\) | **FALSIFY** |
| **GW170729** | **True held-out** | **fail** | \(+7.58\times10^{-5}\) | **NULL** |
| **GW151012** | **True held-out** | **PASS** | \(-7.96\times10^{-5}\) | **FALSIFY** |

**True held-out tally: 0 SUCCESS · 2 FALSIFY · 1 NULL.**  
Universal α-band claim **demoted**. Band **not** re-fit.  
Full scorecard: `docs/MILESTONE_HELD_OUT_TRUE_BBH.md`.

### Gate S-1 on FALSIFY events (canonical n_draws≥12)

| Event | Gate S-1 | Notes |
|-------|----------|--------|
| GW170809 | **ROBUST_ANOMALY** | +α ≫ band; multi-approx + 12/12 draws stable |
| GW151012 | **SYSTEMATICS_RISK** | −α; 3/4 approx PASS; PE draws 5/12 (n=12); n=8 had flattered ROBUST_ANOMALY |

Only one robust anomaly (GW170809). GW151012 PE-draw instability → systematics narrative.  
See `docs/MILESTONE_FALSIFY_SYSTEMATICS.md`.

### Bulk PE-power mapping — stopped

Mass (v2), inverse SNR (v3a), and distance (v3b) all **FALSIFY** shared-\(\alpha_0\)
unification. Family closed; stretch stopped.

| | |
|--|--|
| Close-out | `docs/MILESTONE_BULK_PE_MAPPING_CLOSED.md` |
| Archive | `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md` |
| Mode | Score-only; locks frozen; band remains demoted |
| Exception | New physical variable only via fresh `docs/PREREG_*.md` |

Do **not** re-open mild bulk PE powers or unregistered exponents (e.g. \(d_L^3\))
to force ratio ~12.

## Artifacts

- `outputs/predictions/premerger_core_prediction.json`  
- Freeze: `docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md`  
- Mapping closed: `outputs/mapping_v2/`, `outputs/mapping_v3/`  

