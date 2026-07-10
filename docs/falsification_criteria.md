# Falsification criteria

These criteria keep the invariant search alive while blocking confirmation bias.
They apply to **mappings** of the locked invariants into observables — not to
the existence of \(W_g \approx 350/\pi\) itself.

---

## I. Post-merger echo ladder (campaign closed)

Criteria below apply to geometric delays + amp structures in post-merger residuals.

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

### Gate D — Multi-event

- Gate C **strict** on ≥ 3 BBH events under the same mapping  
- Runner: `python scripts/multi_event_network.py`

**Status (GW150914, GW170104, GW151226):** Gate C strict **1/3** → **Gate D FAIL**.  
GW151226 stress test (**band systematics + injections**): **does not hold** — off-band 50–300 Hz also passes with larger Δχ² (broadband systematics, not ringdown-localized).  
See `docs/MILESTONE_MULTI_EVENT.md`, `docs/MILESTONE_GW151226_STRESS.md`.

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

### Analytic consistency (sync branch)

From `docs/ANALYTIC_ECHO_PREDICTION.md`: observer synchronization implies  
\(h_{\mathrm{echo}}/h_{\mathrm{main}} \lesssim 10^{-6}\). For SNR_main ~ 10–50,  
SNR_echo ≪ 2. Therefore **Gate C/D failure for O(1) residual echo templates is  
predicted**, not anomalous. A true falsifier of the sync branch would be  
confirmed echoes at relative amplitude \(\gg 10^{-5}\) for embedded detectors.

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
| v3 amp structure | braiding / flux / hopf weights | Gate D still 1/3 strict all structures |

Core locks \(W_g\), κ unchanged across mapping versions.  
Milestones: `MILESTONE_GW150914_v2.md`, `MILESTONE_AMP_STRUCTURE.md`.

## II. Pre-merger topological phase (Gate P) — active

**Observable:** cumulative phase drift on inspiral residuals after PE IMR subtraction.

**Template (locks fixed):**
\[\Delta\phi(t) = \alpha\, W_g\, \Phi_{\mathrm{orb}}(t)\, \cos(\phi_b)\]
Only \(\alpha\) free. Basis: \(\tau = -W_g\cos\phi_b\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\).

**Setup:** whitened H1+L1, ~4 s pre-merger; inspiral \(t < -0.05\) s; band 20–100 Hz.

### Gate P
Pass if \(\Delta\chi^2 \ge 6\), \(|\hat\alpha| > 2\sigma_{\hat\alpha}\), **and**
H1/L1 same sign when both are significant.

### Gate P-D
Gate P on ≥ 2 BBHs with **same sign** of network \(\hat\alpha\).

### Core lock (after systematics)

**Credible core:** GW150914 + GW170814 only.  
**Demoted:** GW170608 (high corr(r,τ), mass sign flip), GW170818 (draws 4/8).

**Forward band** (3×width): \(\hat\alpha \in [2.88\times10^{-5},\,1.15\times10^{-4}]\) (positive).

```bash
python scripts/premerger_core_predict.py
python scripts/premerger_core_predict.py --predict-event <NEW_BBH>
```

**SUCCESS:** next Gate-P-pass event with \(\hat\alpha\) in band.  
**FALSIFY:** Gate-P-pass with \(\hat\alpha\) outside band or significantly negative.  
**NULL:** Gate P fail (not a counterexample).

**Freeze:** in-catalog campaign closed at this rule —  
`docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md`. Reopen only for a true new held-out BBH or roadmap “later” items.

### Gate B-P — pre-merger injection recovery

- Background α_inj=0: false Gate P rate should be low  
- Injected α above thr recovered with frac ∈ [0.5, 1.5] and Gate P pass  
- Real |α| compared to thr and residual–τ correlation (systematics);  
  **corr(r,τ) ≳ 0.1 flags PE-systematics risk** (as on demoted GW170608)

Docs: `docs/PREMERGER_PHASE.md`

## Suggested next refinements (echo ladder — closed)

1. ~~Amp structure / whitened network / multi-event~~ done (mapping constrained)  
2. Pre-merger Gate P (active)  
3. Matched-filter quiet post-merger at \(f_{\mathrm{phys}}(M)\) (later)
