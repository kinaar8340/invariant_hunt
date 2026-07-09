# Positional interpretation of \(350/\pi\)

## Motivation

Numerically, the gauged Hopf lattice locks a geometric winding

\[
W_g \approx \frac{350}{\pi} \approx 111.408.
\]

A purely *temporal* reading treats this as a burst cadence or clock tick.
A *positional* reading (this project’s default) treats \(W_g\) as a **phase /
lattice coordinate** — a locked step on the Hopf fiber and in the discrete
gauged lattice — so that “bursts” are **alignments** of dynamical trajectories
with those loci.

Both framings can generate time series; they differ in what is fundamental
(phase geometry vs. pure time).

## Geometric picture

1. **Hopf fiber angle**  
   For lattice index \(n\) and fractional offset \(f\),

   \[
   \theta_n = \frac{2\pi}{W_g}\,(n + f).
   \]

2. **Unit phase** (toroidal \([0,1)\))

   \[
   \varphi_n = \Bigl(\frac{n}{W_g} + f\Bigr) \bmod 1.
   \]

3. **Timing offset from position**  
   Given a base period \(T\) of an observable,

   \[
   \delta t_n = T\,\varphi_n.
   \]

   Echo delays for remnant mass \(M\) use the geometric time \(GM/c^3\) as \(T\)
   scale (see `src/predictions.py`).

4. **Burst thresholds** (from `papers/GW_Burst_Threshold.tex`)

   | Symbol | Formula | Role |
   |--------|---------|------|
   | \(\Theta_{\mathrm{link}}\) | \(2\pi W_g/(2W_g+1)\) | Hopf linking saturation (~π) |
   | \(\theta_{\mathrm{crit}}\) | \(\pi(1+\kappa)\) | PDE/lattice burst sink |

## Diagram (textual)

```
  Hopf S¹ fiber          lattice sites along winding
  ─────────────────      0──1──2──…──n──…──W_g
       ↑ θ_n                    ↑
   locked steps            alignment → burst/echo
       │
       └─ phase φ_n ──► δt = T · φ_n  (observable timing)
```

## Code entry points

| Module | Role |
|--------|------|
| `src/positional.py` | `PositionalPhase`, timing/frequency maps, burst loci |
| `src/invariants.py` | Canonical locks, residuals, \(\Theta_{\mathrm{link}}\) |
| `src/predictions.py` | Falsifiable `PredictionRecord`s |
| `scripts/meta_optimize_invariants.py` | Hunt stable locks with positional penalty |
| `scripts/forward_gw_signal.py` | Forward echo train from locks |

## Falsification checkpoint

If measured GW echo delays (or QPO / timing residuals) show **no** structure
near \(\delta t_n\) predicted from \(n/W_g\) at the stated mass/period scale
within documented uncertainty, revise the positional map or the scale factors
— not the aesthetic of the number alone.
