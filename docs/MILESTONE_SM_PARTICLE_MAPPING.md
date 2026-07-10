# Milestone: Phase 2.1 SM Particle Mapping (Gate SM-1)

**Status:** Gate SM-1 PASS (structure scaffold)  
**Date:** 2026-07-09  
**Phase:** 2.1 — lattice modes → SM representations

## Goal

Map gauged Hopf lattice excitations (flux flywheels, holonomy waves, Hopfion
solitons, braiding layers) onto SM gauge bosons, chiral fermions (3 generations),
and the Higgs multiplet with **correct quantum numbers**.

## Frozen core (unchanged)

| Lock | Value |
|------|--------|
| \(W_g\) | \(350/\pi\) |
| \(\kappa\) | \(\approx 0.85\) |
| \(\phi_b^\star\) | \(\approx 0.8145\) |
| Pre-merger freeze | untouched |

## Deliverables

| Item | Path | Status |
|------|------|--------|
| SM mapping library | `src/sm_mapping.py` | done |
| Mapping CLI | `scripts/sm_mapping.py` | done |
| Gate runner | `scripts/sm_gate_check.py` | done |
| Meta `--sm-mode` | `scripts/meta_optimize_invariants.py` | done |
| Tests | `tests/test_sm_mapping.py` | done |
| Paper scaffold | `papers/SM_Derivation.tex` | done |
| This milestone | `docs/MILESTONE_SM_PARTICLE_MAPPING.md` | done |

## Lattice → SM map (Phase 2.1)

| Lattice mode class | SM target |
|--------------------|-----------|
| YM adjoint SU(3) flux flywheel | \(g\) (gluons, 8) |
| YM adjoint SU(2) holonomy wave | \(W\) (before EWSB) |
| U(1) global pointer mode | \(B\) (hypercharge) |
| Holonomy modulus / pointer VEV | \(H\) (Higgs doublet) |
| Hopfion soliton (\(S^3\) double cover) | \(Q_L,u_R,d_R,L_L,e_R\) |
| Braiding layer index \(n_g=1,2,3\) | three generations |

Hypercharge convention: \(Q = T_3 + Y/2\) with standard PDG weak hypercharges
(\(Y_{Q_L}=1/3\), \(Y_{u_R}=4/3\), \(Y_{d_R}=-2/3\), \(Y_{L_L}=-1\), \(Y_{e_R}=-2\), \(Y_H=1\)).

## Gate SM-1

```bash
python scripts/sm_mapping.py --mode bosons_fermions --plot
python scripts/sm_gate_check.py --gates SM-1 --require SM-1
python scripts/meta_optimize_invariants.py --sm-mode --trials 8
```

| Criterion | Pass condition |
|-----------|----------------|
| Representation catalog | All gauge + Higgs + 3×5 fermion multiplets with correct \(({\rm su3},{\rm su2},Y)\) |
| Electric charges | \(Q=T_3+Y/2\) matches SM for gen-1 components |
| Lattice mode coverage | Unique non-empty mode tags; maps cover all targets; locks in maps |
| Locks frozen | \(W_g,\kappa,\phi_b\) unchanged |

Artifact: `outputs/sm_mapping/sm_mapping_latest.json`, `sm_gate_check_latest.json`.

## Gate SM-2 / SM-3

| Gate | Status |
|------|--------|
| **SM-2 structure** | Three identical representation copies — PASS |
| **SM-2 mass (2.2)** | Topological Yukawa χ² — see `MILESTONE_SM_YUKAWA.md` |
| **SM-3** | Anomaly coeffs ≈ 0; RG deferred to 2.3 |

```bash
python scripts/sm_gate_check.py --gates SM-1,SM-2,SM-3
python scripts/sm_yukawa_ansatz.py --sweep --trials 64
```

## What this is *not*

- Not a claim that Hopfions *are* electrons with measured \(m_e\).  
- Not gravity emergence or full EFT (Phase 3+).  
- Not a reopening of the pre-merger predictive freeze.

## Demotion rule

Demote any mapping that:

1. Fails Gate SM-1 quantum numbers, or  
2. Breaks anomaly cancellation (SM-3), or  
3. Fails SM-2 mass thresholds (demote Yukawa ansatz only), or  
4. Reopens core locks / conflicts with Gate A-P or H-S, or  
5. Fails multi-event GW consistency when it claims GW-facing couplings.

## Next

Phase **2.3**: RG flow simulator (complete Gate SM-3).  

## Lineage

- Phase 1 action: `docs/MILESTONE_ACTION_PRINCIPLE.md`  
- Relativistic completion: `papers/Relativistic_Completion.tex`  
- Code: `src/action_principle.py` product-group YM scaffold  
