# Campaign complete: positional echo ladder mapping

**Status:** closed for the post-merger geometric echo-train observable  
**Repo:** [kinaar8340/invariant_hunt](https://github.com/kinaar8340/invariant_hunt)  
**Period:** project inception → amplitude-structure v3 (2026-07)

## What was tested

Systematic, gated confrontation of one **mapping** — locked topological invariants → post-merger geometric echo ladder — with public LIGO data:

| Layer | Implementation |
|-------|----------------|
| Baseline | Toy RD → GWTC-1 PE → whitened H1+L1 PE residual |
| Template | Independent → coherent complex \((a_c,a_s)\) |
| Timing | Geometric \(\delta t_n\); \(s\)-scan + LEE |
| Sensitivity | Single-det + network injection recovery |
| Consistency | Multi-event Gate D (3 BBHs) |
| Outlier | GW151226 band systematics |
| Weights | 5 amplitude structures (v3) |

Core locks held fixed throughout: \(W_g \approx 350/\pi\), \(\kappa \approx 0.85\), braiding attractor.

## Cumulative gate status

| Gate | Result |
|------|--------|
| B / B-net (sensitivity) | **Pass** — pipelines detect injected echoes |
| C strict (per event) | Mostly fail / marginal; GW151226 fails stress |
| D (multi-event strict) | **Fail** (≤1/3 under all amp structures) |
| Core invariants | **Not falsified** by this campaign |

### Event sketch (geometric amp, whitened network, s=1)

| Event | Δχ² | SNR | C strict | Notes |
|-------|-----|-----|----------|-------|
| GW150914 | 4.16 | 2.04 | fail | Marginal weak only |
| GW170104 | 2.81 | 1.68 | fail | Clean null |
| GW151226 | 10.85 | 3.30 | pass* | *Fails band stress (off-band larger) |

Amplitude variants (braiding, braiding_lock, flux_kappa, hopf_winding) change Δχ² by ≪1; **Gate D fails for all**.

## Scientific conclusion

> The tested **translation** of the locked invariants into a post-merger coherent positional echo train does **not** produce robust, multi-event support in whitened H1+L1 residuals.

This is a **constraint on the mapping**, not a disproof of the Hopf-lattice / flux-flywheel locks. Off-band behavior on GW151226 and stability across amp weights indicate the issue is the **assumption that this form of echo ladder should appear in post-merger residuals**, not fine weight details.

## Campaign product (reusable)

A gated, reproducible apparatus:

- PE residual + whitening + network coherent fit  
- Injection calibration  
- LEE-aware delay scans  
- Multi-event + stress-test scripts  
- Explicit falsification criteria (`docs/falsification_criteria.md`)

Further fine-tuning of this post-merger echo template is **low leverage**.

## Analytic follow-up (done)

See `docs/ANALYTIC_ECHO_PREDICTION.md` and `src/echo_theory.py`.

Under observer synchronization the model predicts  
\(h_{\mathrm{echo}}/h_{\mathrm{main}} \lesssim 10^{-6}\).  
**Gate D failure for loud residual ladders is the expected outcome** of the  
sync-suppressed branch — consistent with the campaign, not a tension with \(W_g\) or \(\kappa\).

## Next phase (higher value)

1. **Different observable domain** — pre-merger, polarization, non-GW, or matched-filter search at \(f_{\mathrm{phys}}(M)\) with \(10^{-6}\)-level relative amp  
2. **Falsifier of sync branch** — confirmed echoes at relative amp \(\gg 10^{-5}\) for embedded detectors  

Reuse gated discipline: pre-register gates, injection recovery, multi-event, no free retuning of core locks on single events.

## Milestone index

| Doc | Content |
|-----|---------|
| `MILESTONE_GW150914_v2.md` | H1 PE residual, coherent + LEE |
| `MILESTONE_WHITENED_NETWORK.md` | H1+L1 whitening Gate C |
| `MILESTONE_MULTI_EVENT.md` | Three-event Gate D |
| `MILESTONE_GW151226_STRESS.md` | Outlier band stress |
| `MILESTONE_AMP_STRUCTURE.md` | Weight variants v3 |
| **This file** | Campaign close-out |
