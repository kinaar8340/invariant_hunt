# Falsification criteria — positional echo ladder

These criteria keep the invariant search alive while blocking confirmation bias.
They apply to the **current** mapping (geometric delays + amp₀ⁿ priors + braiding
phase), not to the existence of \(W_g \approx 350/\pi\) as a lattice lock.

## Setup under test

| Item | Definition |
|------|------------|
| Data | Public GWOSC strain (default GW150914 H1) |
| Baseline | GWTC-1 PE medians → IMRPhenomD, lag+(A₊,Aₓ) fit |
| Observation | Post-merger PE residual |
| Signal model | Leftover ringdown + positional echo train |
| Noise model | White, band-limited (pre-merger σ) — interim |

## Quantitative gates

### Gate A — Single-event support (weak)

On one event with PE residual + **coherent** echo train (`coherent_echo_scan.py`):

- \(\Delta\chi^2 = \chi^2_{\mathrm{RD}} - \chi^2_{\mathrm{RD+echoes}} \ge 4\) **and**
- overall complex amplitude \(|A| = \sqrt{a_c^2+a_s^2} > 0\) (prefer cos-phase aligned with train) **and**
- coherent 2-dof matched-filter SNR ≥ 2

At **nominal** delay scale \(s=1\) (pure geometric). No look-elsewhere credit.

**Status on GW150914 H1:**

| Map | Δχ² @ s=1 | Strength | Gate A |
|-----|-----------|----------|--------|
| v1 independent | ~0.04 | a₁≈0 | **Fail** |
| v2 coherent | **0.45** | MF SNR≈0.77 | **Fail** |

See `docs/MILESTONE_GW150914_v2.md`.

### Gate A′ — Delay-scale scan (with LEE)

Optional controlled scan \(s \in [0.8, 1.2]\) on \(\delta t_n \to s\cdot\delta t_n\):

- Report max \(\Delta\chi^2\) over \(N\) grid points
- **LEE-corrected threshold** (approx.): \(\ thr' = thr + 2\ln N\ \)
- Pass only if max \(\Delta\chi^2 \ge thr'\) and \(|A|>0\)

This tests small timing corrections without claiming \(s\neq 1\) as a new free law.

### Gate B — Injection recovery (sensitivity)

Using `scripts/injection_recovery.py`:

- Background (a_inj=0) must recover \(a_1 \approx 0\) and Δχ² ≲ 1
- Injected signals with \(a_{\mathrm{inj}} \ge a_{\mathrm{thr}}\) must recover \(a_1 / a_{\mathrm{inj}} \in [0.5, 1.5]\) and Δχ² ≥ 4
- If real-data \(|a_1|\) is well below \(a_{\mathrm{thr}}\), the null is **expected**, not a pipeline bug

### Gate C — Whitened multi-detector (stronger single-event)

On whitened H1+L1 network PE residual (`network_whiten_scan.py`):

**Gate C (weak / historical):** Δχ² ≥ 4 and network MF SNR ≥ 2 at \(s=1\).  
**Gate C strict (preferred, 2-dof):** Δχ² ≥ **6** and network MF SNR ≥ 2 at \(s=1\).  
(For 2 extra parameters, χ²₂ 95% ≈ 5.99 — so thr=6 is the natural bar.)

- Optional delay scan with LEE on network Δχ² (same as Gate A′)
- Noise model: Welch PSD → FD whitening → unit-variance white in-band

**Status on GW150914 H1+L1 (full-file Welch whitening, coherent map):**

| Check | Value | Result |
|-------|-------|--------|
| Δχ² @ s=1 | 4.16 | ≥4 ✓, **&lt;6 ✗** |
| network MF SNR | 2.04 | ≥2 ✓ |
| Gate C weak | — | marginal PASS |
| **Gate C strict** | — | **FAIL** |
| best s + LEE (thr≈10.1) | Δχ²_max=4.86 @ s=0.96 | **FAIL** |

PE recovery after whitening: H1 SNR≈54, L1 SNR≈39 (healthy).  
See `outputs/benchmarks/GW150914_H1-L1_whitened_network.json`.

**Caveat:** Even Gate C weak does not trial-factor continuous phase. Marginal weak pass is not a discovery claim. Prefer Gate C strict for physics statements.

### Gate B-net — Network injection recovery

Using `scripts/network_injection_recovery.py` on whitened residuals:

- Background a_inj=0: Δχ² should be ≲ few (noise floor)
- Pipeline must recover Δχ² ≥ 6 and SNR ≥ 2 for some a_inj above threshold
- Places the real-data excess (Δχ²≈4.2) on a calibrated sensitivity curve

### Gate D — Multi-event (not yet implemented)

- Gate C on ≥ 3 BBH events
- Look-elsewhere for free delay/κ scans across events

### Gate E — Mapping revision triggers

Revise the **echo mapping** (not necessarily the invariant locks) if:

1. Gate A **and** Gate C fail on GW150914-class events **and** injection shows the pipeline would have seen a physical echo of comparable literature amplitude, **or**
2. Residual diagnostics show local Δχ² only at control (off-ladder) times, **or**
3. Best-fit echo amplitude consistent with zero / anti-template across H1 and network

Preserve \(W_g\), κ, braiding locks unless independent meta-optimization / analytic work moves them.

## What a null means

> The positional echo ladder with the chosen amplitudes/phases does not improve
> the PE residual under this noise model.

It does **not** mean:

- Hopf-lattice invariants are false
- \(350/\pi\) locking is invalid
- No other observable mapping can work

It **does** mean:

- This invariant→GW-echo translation needs refinement or a different domain

## Tools

| Script | Role |
|--------|------|
| `compare_benchmark.py --baseline pe` | End-to-end PE residual (legacy independent train) |
| `coherent_echo_scan.py` | Coherent complex amp + delay scan + LEE (H1) |
| `network_whiten_scan.py` | Whitened H1+L1 network likelihood (Gate C) |
| `network_injection_recovery.py` | Network sensitivity / Gate B-net |
| `inspect_residual.py` | Per-echo local Δχ², MF SNR, control windows |
| `injection_recovery.py` | Single-det sensitivity / Gate B |

## Mapping versions

| Version | Template | Status |
|---------|----------|--------|
| v1 independent | per-step fixed phase, single real a₁ | Gate A fail on GW150914 |
| v2 coherent | shared complex (a_c, a_s) over train | Gate A fail (Δχ²=0.45, SNR=0.77) |
| v2+scan | coherent + s∈[0.8,1.2] with LEE | best s=1.00; Gate A′ fail |

Core locks \(W_g\), κ unchanged across mapping versions. Milestone write-up:
`docs/MILESTONE_GW150914_v2.md`.

## Suggested next refinements (if Gate A still fails)

1. Tie amp decay to braiding / flux rather than fixed 0.35ⁿ  
2. Whitened multi-detector likelihood before claiming Gate A/C  
3. Alternate observable domain (not only post-merger echoes)
