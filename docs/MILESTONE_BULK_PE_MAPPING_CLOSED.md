# Milestone: Bulk PE-power pre-merger mapping — **stopped**

**Status:** closed / frozen — **archived**  
**Date:** 2026-07-10  
**Decision:** Stop the bulk PE-power mapping stretch.  
**Archive index:** `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md`  
**Exception:** A *new physical variable* only under a **separate pre-registration** (not a mild power rescue of mass / SNR / distance).

## Closed family (executed)

| Campaign | Form | Verdict |
|----------|------|---------|
| Mapping v1 band | Event-independent α ∈ freeze band | **Demoted** (true held-outs 0 SUCCESS / 2 FALSIFY / 1 NULL) |
| Mapping v2 | \(\beta=\alpha_0(M_{\mathrm{tot}}/60)^p\), \(p=1\) | **FALSIFY** (mass-unification; \(z\approx 30\)) |
| Mapping v3a | \(\beta=\alpha_0(\rho_{\mathrm{ref}}/\rho)^q\), \(q=1\) | **FALSIFY** (unification; \(z\approx 21\)) |
| Mapping v3b | \(\beta=\alpha_0(d_L/d_{\mathrm{ref}})^s\), \(s=1\) | **FALSIFY** (unification; \(z\approx 18.5\)) |

Milestones:  
`docs/MILESTONE_HELD_OUT_TRUE_BBH.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V2.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V3.md`.

## What remains standing

| Item | Status |
|------|--------|
| Core locks \(W_g\), \(\kappa\), \(\phi_b\) | **Frozen** — not reopened by mapping FALSIFY |
| Residual template channel \(\tau_0\) | Unchanged; used for score-only diagnostics |
| GW170809 Gate P / BF / S-1 | **ROBUST_ANOMALY** — large stable residual preference **without** shared \(\alpha_0\) map |
| GW151012 | **SYSTEMATICS_RISK** — not a design anchor |
| Phases 1–3 scaffolding gates | Separate; not reopened |

## What is stopped

- Further bulk PE-power unifications: \(M_{\mathrm{tot}}^p\), \((\rho_{\mathrm{ref}}/\rho)^q\), \((d_L/d_{\mathrm{ref}})^s\) with mild pre-registered powers  
- Post-hoc exponents chosen to hit \(\alpha_{809}/\alpha_{914}\approx 12\) (including unregistered \(d_L^3\))  
- Free \(p,q,s\) after seeing held-out \(\hat\alpha\)  
- Dual-sign / GW151012-driven redesign  
- Re-fitting demoted v1 SUCCESS band  

## Operational mode now

1. **Score-only** under frozen locks and existing scripts (historical band claim remains demoted; no SUCCESS restoration).  
2. **No new mapping template** until a document under `docs/PREREG_*.md` names a **new physical variable** with fixed form, honesty table, SUCCESS/FALSIFY, and explicit non-use of GW151012 for design.  
3. Residual anomaly on GW170809 may be **cited as open / unexplained** under the locked template — not promoted to multi-event discovery.

```bash
# Allowed: re-score under frozen template (no new map)
python scripts/premerger_core_predict.py --predict-event GW170809
python scripts/premerger_bayes_factor.py --event GW170809

# Not allowed without new PREREG: mapping v4 bulk PE power rescue
```

## Gate for any future mapping

| Requirement | Rule |
|-------------|------|
| Document | New `docs/PREREG_*.md` before code |
| Variable | **Not** mass / inv-SNR / distance mild powers already closed |
| Locks | Remain frozen unless independent theory justification (separate process) |
| Design set | No GW151012; prefer blind holdouts after form freeze |
| Honesty | Pre-run predicted β ratios vs empirical ~12 must be stated |

### Successor remnant-mass family (executed → closed)

| Campaign | Variable | Verdict |
|----------|----------|---------|
| Mapping v4 | Remnant \(M_f\), \(p=1\) | **FALSIFY** Unify (\(z\approx 30.6\)); family **closed** |

See `docs/MILESTONE_PREMERGER_MAPPING_V4.md`. Not a reopening of closed \(M_{\mathrm{tot}}\) / SNR / distance.

## Explicit non-claims

- Not a claim that the GW170809 residual is non-physical  
- Not a claim that no map exists — only that **this bulk PE-power family failed**  
- Not a license to float Hopf locks to absorb the anomaly  
