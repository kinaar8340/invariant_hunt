# Analytic invariant → echo signal

**Purpose:** From the gauged Hopf lattice + flux flywheel + observer synchronization,  
derive *when/whether* GW echo-like signatures should be detectable — and reconcile  
that with the closed empirical mapping campaign.

**Sources (TOE papers):**  
`GW_Burst_Threshold`, `GW_Echo_Derivation`, `GW_Echo` (residual bounds),  
`Observer_Synchronization`.

**Code:** `src/echo_theory.py`, `scripts/evaluate_echo_expectation.py`

---

## 1. Locked invariants (unchanged)

| Symbol | Value | Role |
|--------|-------|------|
| \(W_g\) | \(350/\pi \approx 111.408\) | Topological winding / flux quantization |
| \(\kappa\) | \(\approx 0.85\) | Global pointer holonomy |
| \(\phi_b\) | \(\approx 0.8145\) | Braiding-phase attractor |
| \(\Delta\omega\) | \(\approx 0.002\) | Two-gyro detuning (lattice) |
| \(\bar\Theta\) | \(\approx 0.82\) | Mean low-twist state |

## 2. Burst thresholds

\[
\Theta_{\mathrm{link}} = \frac{2\pi W_g}{2W_g+1} \approx \pi
\qquad
\theta_{\mathrm{crit}} = \pi(1+\kappa) \approx 5.812
\]

Burst when local twist \(\Theta > \theta_{\mathrm{crit}}\). Flux shed per burst:
\(\Delta\Phi \propto \Delta\omega / W_g\).

## 3. Lattice burst timescale and frequency

Drive toward threshold:

\[
\Delta t_{\mathrm{burst}} \approx \frac{\theta_{\mathrm{crit}} - \bar\Theta}{\Delta\omega}
\approx \frac{5.0}{0.002} = 2500
\quad\text{(lattice time units).}
\]

Topological emission frequency (lattice):

\[
\boxed{\;
f_{\mathrm{lat}} = \frac{\Delta\omega}{W_g}
\;}
\]

## 4. Physical frequency (mass dependence)

Using GR geometric time \(t_M = GM/c^3\):

\[
\boxed{\;
f_{\mathrm{phys}}(M)
  = f_{\mathrm{lat}} \cdot \frac{c^3}{GM}
  = \frac{\Delta\omega}{W_g\, t_M}
\;}
\]

(The paper text writes \(c^2/GM\); that is dimensionally inconsistent for frequency.  
Code uses \(c^3/GM\). An overall \(O(1)\) model prefactor can still sit in torsion–curvature matching.)

**Consequence:** \(f_{\mathrm{phys}} \propto 1/M\). Lighter remnants → higher echo frequency  
(relevant for band choice; does *not* by itself fix amplitude).

## 5. Observer synchronization → amplitude bound

Pointer: \(\alpha = -\kappa\bar\Theta\). Local deviation damps as \(\delta\Theta(t)=\delta\Theta(0)\,e^{-\kappa t}\).

Time-averaged burst strength for \(\kappa\Delta t_{\mathrm{burst}}\gg 1\):

\[
\frac{\langle\delta\Theta_{\mathrm{burst}}\rangle}{\delta\Theta_{\mathrm{burst}}(0)}
  \approx \frac{1}{\kappa\,\Delta t_{\mathrm{burst}}}.
\]

Undamped paper estimate: \(h_{\mathrm{burst}}/h_{\mathrm{ring}} \sim A_0 \approx 10^{-3}\).

With sync (and embedded detectors, including LIGO):

\[
\boxed{\;
\frac{h_{\mathrm{echo}}}{h_{\mathrm{main}}}
  \lesssim \frac{A_0}{\kappa\,\Delta t_{\mathrm{burst}}}
  \sim 2\times 10^{-6}
  \quad(\kappa=0.85,\;\Delta t_{\mathrm{burst}}\sim 500\text{–}2500)
\;}
\]

Frequency is **unchanged** by sync; amplitude is **suppressed**.

## 6. Detectability condition

Proxy: \(\mathrm{SNR}_{\mathrm{echo}} \approx \mathrm{SNR}_{\mathrm{main}} \times (h_{\mathrm{echo}}/h_{\mathrm{main}})\).

| Branch | \(h_{\mathrm{echo}}/h_{\mathrm{main}}\) | SNR_main for SNR_echo≥2 |
|--------|----------------------------------------|---------------------------|
| Undamped | \(10^{-3}\) | \(\gtrsim 2\times 10^3\) |
| **Sync (model default)** | \(\sim 2\times 10^{-6}\) | \(\gtrsim 10^{6}\) |

**No LIGO BBH event** (SNR_main ~ 10–50) meets the sync branch.  
Even undamped needs SNR_main thousands.

### Catalog sketch (sync branch)

| Event | \(M_f\) | \(f_{\mathrm{phys}}\) (pref=1) | SNR_main | SNR_echo (sync) | Detectable? |
|-------|---------|--------------------------------|----------|-----------------|-------------|
| GW150914 | 63.1 | ~few–tens Hz order | ~25 | \(\sim 6\times 10^{-5}\) | **No** |
| GW170104 | 48.9 | higher | ~13 | \(\sim 3\times 10^{-5}\) | **No** |
| GW151226 | 20.5 | higher still | ~13 | \(\sim 3\times 10^{-5}\) | **No** |

(Exact \(f_{\mathrm{phys}}\) depends on geometric prefactor; **detectability does not** — amplitude bound is mass-independent in this damping law.)

## 7. Relation to the empirical campaign

| Campaign assumption | Analytic status |
|---------------------|-----------------|
| Relative echo train \(O(0.1–1)\) of residual templates | **Forbidden** under sync (amp \(\lesssim 10^{-6}\)) |
| Geometric delay ladder \(\delta t_n=(GM/c^3)2\pi n(1+\kappa)\) | Mapping hypothesis; paper primary is **frequency** \(f_{\mathrm{burst}}\) |
| Gate C / D fail on multi-event residuals | **Predicted** under sync-suppressed branch |
| GW151226 off-band excess | **Not** a predicted localized ladder; systematics |

**Punchline:** The gated campaign constrained a **loud** mapping. The analytic model  
says embedded detectors should see only **extremely quiet** echoes. Null multi-event  
results are **consistent with the theory’s sync branch**, not a falsification of \(W_g\) or \(\kappa\).

## 8. When *would* echoes be expected?

Under current papers, only if at least one holds:

1. **Observer sync fails** for the GW channel (non-embedded / different coupling), or  
2. **\(\kappa\Delta t_{\mathrm{burst}}\) not ≫ 1** (rare short bursts → weaker average suppression), or  
3. **Search targets** matched filters at \(f_{\mathrm{phys}}(M)\) with amplitude sensitivity \(\lesssim 10^{-6}\) relative to ringdown (beyond residual ladder fits), or  
4. **Different observable** not subject to the same pointer locking (non-GW, or differential channels).

None of these revive \(O(1)\) post-merger residual ladders as a viable default.

## 9. Predictions to pre-register next

1. **Amplitude ceiling:** For any BBH with SNR_main < 100, sync-branch SNR_echo < 2×10⁻⁴.  
2. **Frequency track:** Any future echo search should use \(f \propto 1/M_f\), not a fixed 250 Hz band alone.  
3. **Null expectation:** Gate C strict on residual ladders with \(a_{\mathrm{inj}}\sim O(1)\) templates should fail (already observed).  
4. **Falsifier of sync branch:** Confirmed post-merger echoes at relative amp \(\gg 10^{-5}\) with embedded detectors would force revision of observer synchronization or \(A_0\), not necessarily of \(W_g\).

## 10. Reproduce

```bash
python scripts/evaluate_echo_expectation.py
```

Output: `outputs/predictions/echo_expectation_analytic.json`
