# Pre-merger topological phase signatures

**Status:** active phase (post-merger echo-ladder campaign closed)  
**Why:** Observer sync suppresses loud post-merger amplitudes; inspiral offers  
cumulative **phase** over many orbits, farther from \(\theta_{\mathrm{crit}}\).

## Locks (fixed)

| Symbol | Value |
|--------|-------|
| \(W_g\) | \(350/\pi \approx 111.4085\) |
| \(\kappa\) | \(\approx 0.85\) |
| \(\phi_b\) | \(\approx 0.8145\) (toroidal) |
| \(\Delta\omega\) | \(\approx 0.002\) |

## Primary template (class A)

\[
\boxed{\;
\Delta\phi(t) = \alpha \cdot W_g \cdot \Phi_{\mathrm{orb}}(t) \cdot \cos(\phi_b)
\;}
\]

- \(\Phi_{\mathrm{orb}}\): orbital phase proxy from GR IMR template (\(\Psi_{GW}/2\))  
- \(\alpha\): single free coupling (fit / bound)  
- Kernel \(K = W_g\cos\phi_b\) fixed by locks  

Small-\(\alpha\) strain response (\(H\) = Hilbert):

\[
h(\alpha) \approx h_{\mathrm{GR}} - \alpha\, K\, \Phi_{\mathrm{orb}}\, H[h_{\mathrm{GR}}]
\]

Basis template: \(\tau = \partial h/\partial\alpha|_{\alpha=0} = -K\,\Phi_{\mathrm{orb}}\,H[h_{\mathrm{GR}}]\).

## Other classes (future)

| Class | Idea |
|-------|------|
| B | Modulation at \(f_{\mathrm{phys}}(M(t))\propto 1/M\) |
| C | Polarization mixing / angle rotation \(\propto\kappa,\phi_b\) |
| D | Pre-threshold damping in earliest inspiral |

## Pipeline

1. Whiten long pre-merger window (Welch PSD)  
2. Subtract PE IMRPhenomD (lag + A₊,Aₓ)  
3. Fit \(\alpha\) on inspiral residual \(t < t_{\mathrm{end}}\)  
4. Gate P: \(\Delta\chi^2\ge 6\), \(|\alpha|>2\sigma\), **and H1/L1 same sign**  
5. Multi-event Gate P-D: ≥2 events pass with **same-sign** network \(\alpha\)  
6. Injection recovery before any detection claim

```bash
python scripts/premerger_phase_scan.py --event GW150914 --plot
python scripts/premerger_phase_scan.py --events GW150914,GW170104,GW151226

# Gate B-P: α injection recovery + residual–τ correlation + time cuts
python scripts/premerger_injection_recovery.py --event GW150914 --plot
```

## Relation to analytics

Post-merger: \(h_{\mathrm{echo}}/h_{\mathrm{main}}\lesssim10^{-6}\) (sync) → residual ladders null  
Pre-merger: phase integrates; amplitude of \(\alpha\) still expected small —  
Gate P is a **bound or detection** on \(\alpha\), not a revival of O(1) echoes.

## Code

| Path | Role |
|------|------|
| `src/premerger_theory.py` | Formulas, Hilbert basis, predictions |
| `src/premerger_phase.py` | Whitened fit (single + network) |
| `scripts/premerger_phase_scan.py` | Gate P runner |
