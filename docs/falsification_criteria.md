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

On one event with `--baseline pe`:

- \(\Delta\chi^2 = \chi^2_{\mathrm{base}} - \chi^2_{\mathrm{toe}} \ge 4\) **and**
- best-fit \(a_1 > 0\) **and**
- at least one echo window with matched-filter \|SNR\| ≥ 2

**Status on GW150914 H1 (2026-07):** fail (Δχ²≈0.04, a₁≈0).

### Gate B — Injection recovery (sensitivity)

Using `scripts/injection_recovery.py`:

- Background (a_inj=0) must recover \(a_1 \approx 0\) and Δχ² ≲ 1
- Injected signals with \(a_{\mathrm{inj}} \ge a_{\mathrm{thr}}\) must recover \(a_1 / a_{\mathrm{inj}} \in [0.5, 1.5]\) and Δχ² ≥ 4
- If real-data \(|a_1|\) is well below \(a_{\mathrm{thr}}\), the null is **expected**, not a pipeline bug

### Gate C — Multi-event (stronger; not yet implemented)

- Gates A on ≥ 3 BBH events, or coherent H1+L1 with shared ladder
- Look-elsewhere correction for delay/κ scans if those are free

### Gate D — Mapping revision triggers

Revise the **echo mapping** (not necessarily the invariant locks) if:

1. Gate A fails on GW150914-class events **and** injection shows the pipeline would have seen a physical echo of comparable literature amplitude, **or**
2. Residual diagnostics show local Δχ² only at control (off-ladder) times, **or**
3. Best-fit \(a_1 < 0\) consistently (anti-template)

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
| `compare_benchmark.py --baseline pe` | End-to-end PE residual test |
| `inspect_residual.py` | Per-echo local Δχ², MF SNR, control windows |
| `injection_recovery.py` | Sensitivity / Gate B |

## Suggested next refinements (mapping only)

1. Tie amp decay to braiding / flux rather than fixed 0.35ⁿ  
2. Coherent primary–echo interference in one complex amplitude  
3. Small scan in delay scale around geometric prediction (with look-elsewhere)  
4. Whitened multi-detector likelihood before claiming Gate A/C  
