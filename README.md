# Invariant Hunt

**From locked topological/geometric invariants to falsifiable predictions.**

Seeded from [kinaar8340/toe](https://github.com/kinaar8340/toe) (Flux Flywheels, Gauged Hopf Lattice).
This repo focuses the TOE machinery on a single scientific path:

1. **Hunt** robust invariants (meta-optimization, sweeps, PDE relaxation)
2. **Interpret** \(W_g \approx 350/\pi\) as a **positional/phase** lattice coordinate
3. **Map** invariants → observables with explicit formulas
4. **Predict** quantitative signals (GW echoes/bursts first)
5. **Compare** head-to-head on shared benchmarks
6. **Falsify** with documented fail conditions

Metaphysical or theological motivation may inspire the search; **claims are evaluated only on empirical and mathematical merits**.

## Quick start

```bash
cd ~/Projects/invariant_hunt
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Analytic meta-hunt (no GPU / no full conduit required)
python scripts/meta_optimize_invariants.py --dry-run --trials 50

# Forward GW echo train from locked invariants
python scripts/forward_gw_signal.py --mass 30 --sites 5 --plot

# Synthetic benchmark: baseline ringdown vs positional echoes
python scripts/compare_benchmark.py --inject-echoes

# Map ladder → public GW150914; PE residual vs positional echoes
python scripts/map_event_echoes.py --event GW150914 --benchmark --plot
# equivalent:
python scripts/compare_benchmark.py --event GW150914 --baseline pe --detector H1 --plot

# Unit tests (core math; no torch required)
python -m pytest tests/ -q
```

### Public event mapping (GW150914)

The positional echo ladder is evaluated at the published remnant mass (~62 M☉):

| Mode | Formula | First delay (GW150914) |
|------|---------|-------------------------|
| `geometric` (default) | \(\delta t_n=(GM/c^3)\,2\pi\,n\,(1+\kappa)\) | ~3.5 ms (LIGO-resolvable) |
| `phase_unit` | \(\delta t_n=(GM/c^3)\,2\pi\,(n/W_g)\,(1+\kappa)\) | ~µs (sub-sample @ 4 kHz) |

```bash
# Recommended: GWTC-1 PE medians → IMRPhenomD residual + echo ladder
python scripts/compare_benchmark.py --event GW150914 --baseline pe --detector H1 --plot

# Legacy toy ringdown (no PE subtraction)
python scripts/compare_benchmark.py --event GW150914 --baseline toy --detector H1 --plot
```

Data caches (gitignored; auto-downloaded):

- `data/gwosc/` — public strain (GWOSC)
- `data/pe/` — GWTC-1 posterior samples (LIGO-P1800370)

Outputs: `outputs/benchmarks/`, `outputs/predictions/`.

**Caveat:** PE baseline is a **median point estimate** (IMRPhenomD) with lag+(A+,Ax) fit under band-limited white noise — not a full PSD-whitened multi-detector PE. Use results as a transparent residual test, not a discovery claim.

### Residual diagnostics & injection recovery

After a PE benchmark, quantify *why* Δχ² is small and *how loud* an echo must be to recover:

```bash
python scripts/inspect_residual.py --plot
python scripts/injection_recovery.py --into residual --plot
python scripts/injection_recovery.py --into noise --plot
```

### Coherent mapping + delay-scale scan (v2)

Shared complex amplitude for the whole ladder; optional \(s\) scan around geometric \(\delta t_1\) with LEE threshold. Core \(W_g\), κ fixed.

```bash
python scripts/coherent_echo_scan.py --event GW150914 --plot
python scripts/coherent_echo_scan.py --no-scan   # s=1 only
```

### Whitened H1+L1 network (Gate C)

Welch PSD → FD whitening → per-detector PE residual → network coherent \((a_c,a_s)\):

```bash
python scripts/network_whiten_scan.py --event GW150914 --detectors H1,L1 --plot
python scripts/network_injection_recovery.py --into residual --plot
python scripts/network_injection_recovery.py --into noise --plot

# Multi-event Gate C / D
python scripts/multi_event_network.py --events GW150914,GW170104,GW151226 --plot

# Outlier stress test (injections + band systematics)
python scripts/event_stress_test.py --event GW151226 --plot

# Amplitude-structure mapping scan (core locks fixed)
python scripts/amp_structure_scan.py --plot

# Analytic: when/whether echoes are expected (Hopf + observer sync)
python scripts/evaluate_echo_expectation.py

# Pre-merger topological phase (Gate P) — predictive freeze
python scripts/premerger_phase_scan.py --event GW150914 --plot
python scripts/premerger_phase_scan.py --events GW150914,GW170104,GW151226
python scripts/premerger_injection_recovery.py --event GW150914 --plot
python scripts/premerger_pe_robustness.py --event GW150914 --plot
python scripts/premerger_mass_scale.py
# Expanded multi-event + PE posterior draws
python scripts/premerger_expand_events.py --plot --n-draws 10
# Follow-up PE draws on passers + B-P on second event
python scripts/premerger_followup_passers.py --plot --n-draws 8 --inject-events GW170814
# Locked core band + held-out scoring (SUCCESS / FALSIFY / NULL)
python scripts/premerger_core_predict.py
python scripts/premerger_core_predict.py --predict-event GW170823

# Phase 1.1 — unified action principle (Gate A-P; locks frozen)
python scripts/action_principle_check.py
python scripts/action_principle_check.py --pde-smoke
python scripts/pde_relaxation.py --gauge-flux 0 --nt 500 --nx 16 --no-plot

# Phase 1.2 — holonomy/gauge meta-sweep (Gate H-S; locks frozen)
python scripts/meta_optimize_invariants.py --locks-fixed --dry-run --trials 40
python scripts/meta_optimize_invariants.py --locks-fixed --monte-carlo --samples 64

# Phase 2.1 — SM lattice mode mapping (Gate SM-1; locks frozen)
python scripts/sm_mapping.py --mode bosons_fermions --plot
python scripts/sm_gate_check.py --require SM-1
python scripts/meta_optimize_invariants.py --sm-mode --trials 8

# Phase 2.2 — topological Yukawa / mass hierarchy (Gate SM-2 mass)
python scripts/sm_yukawa_ansatz.py --sweep --trials 64 --plot
python scripts/meta_optimize_invariants.py --sm-mode --yukawa --trials 64
python scripts/sm_gate_check.py --gates SM-2 --yukawa --require SM-2

# Phase 2.3 — one-loop SM gauge RG (Gate SM-3 complete)
python scripts/sm_rg_flow.py --plot
python scripts/sm_gate_check.py --gates SM-3 --require SM-3

# Phase 3 — emergent gravity (Gates GR-1 / GR-2 / GR-3)
python scripts/gravity_emergence_check.py --gates GR-1,GR-2,GR-3 --plot
```

Falsification gates: [`docs/falsification_criteria.md`](docs/falsification_criteria.md).  
Campaign close-out: [`docs/CAMPAIGN_ECHO_MAPPING.md`](docs/CAMPAIGN_ECHO_MAPPING.md).  
Analytic prediction: [`docs/ANALYTIC_ECHO_PREDICTION.md`](docs/ANALYTIC_ECHO_PREDICTION.md).  
Pre-merger freeze: [`docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md`](docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md).  
Action principle (Phase 1.1): [`docs/MILESTONE_ACTION_PRINCIPLE.md`](docs/MILESTONE_ACTION_PRINCIPLE.md).

Full conduit evaluation (from TOE):

```bash
python scripts/meta_optimize_invariants.py --trials 30
python scripts/run_reproduction.py --trials 30
```

## Project layout

```
invariant_hunt/
├── src/
│   ├── invariants.py         # W_g, κ, braiding locks & residuals
│   ├── action_principle.py   # Phase 1.1 unified action (SymPy + Gate A-P)
│   ├── gauged_meta_sweep.py  # Phase 1.2 locks-fixed holonomy/gauge sweeps
│   ├── sm_mapping.py         # Phase 2.1 SM representations + Gate SM-*
│   ├── sm_yukawa.py          # Phase 2.2 topological Yukawa + χ²
│   ├── sm_rg.py              # Phase 2.3 one-loop SM gauge RG
│   ├── gravity_emergence.py  # Phase 3 G_N + weak field + GR gates
│   ├── positional.py         # 350/π as phase / lattice site
│   ├── predictions.py        # InvariantSet → PredictionRecord
│   ├── conduit.py            # RubikConeConduit (seeded from toe)
│   ├── config.py
│   └── relaxation_survival.py
├── scripts/
│   ├── action_principle_check.py / sm_* / gravity_emergence_check.py
│   ├── meta_optimize_invariants.py   # --locks-fixed / --sm-mode / --yukawa
│   ├── premerger_core_predict.py     # held-out SUCCESS/FALSIFY/NULL
│   └── pde_relaxation.py
├── docs/
│   ├── GRAVITY_EMERGENCE.md
│   ├── MILESTONE_SM_*.md
│   ├── MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md
│   └── falsification_criteria.md
├── papers/
│   ├── Lagrangian_Derivation.tex / Relativistic_Completion.tex
│   ├── SM_Derivation.tex / Gravity_Emergence.tex
│   └── GW_Burst_Threshold.tex
├── ROADMAP.md
└── vendor/SEED.md
```

## Canonical lock

| Quantity | Value | Notes |
|----------|-------|--------|
| \(w_{g,\mathrm{base}}\) | 350 | Action-like base |
| \(W_g\) | \(350/\pi \approx 111.408\) | Geometric winding |
| \(\kappa\) | ≈ 0.85 | Holonomy / burst lift |
| \(\phi_b\) | ≈ 0.8145 | Braiding attractor |
| \(\theta_{\mathrm{crit}}\) | \(\pi(1+\kappa)\approx 5.81\) | Burst threshold |

See `docs/positional_350_pi.md` for the phase/lattice reading of bursts.

## Status

**Echo-mapping campaign closed.** Gated multi-event tests constrain the
post-merger geometric echo-ladder translation of the locks; they do **not**
falsify the core invariants. Full write-up:
[docs/CAMPAIGN_ECHO_MAPPING.md](docs/CAMPAIGN_ECHO_MAPPING.md).

**Pre-merger predictive freeze closed** (in-catalog). Held-out BBHs scored via
`premerger_core_predict.py`. See
[docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md](docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md).

**Phase 1 action scaffolding complete** (Gates A-P + H-S).  
**Phases 1–3 scaffolding complete** (action, SM, gravity gates).  
**Pre-merger predictive freeze active.** Locks frozen; no full unification claim.  
[docs/MILESTONE_PHASE3_CLOSEOUT.md](docs/MILESTONE_PHASE3_CLOSEOUT.md) ·
[docs/GRAVITY_EMERGENCE.md](docs/GRAVITY_EMERGENCE.md) ·
[docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md](docs/MILESTONE_PREMERGER_PREDICTIVE_FREEZE.md).

```bash
python scripts/integration_status.py --run-gates
python scripts/premerger_core_predict.py --predict-event GW170823
```

Next phase: other observables or analytic invariant→signal derivation
(see [ROADMAP.md](ROADMAP.md)).

## License

MIT — see [LICENSE](LICENSE).
