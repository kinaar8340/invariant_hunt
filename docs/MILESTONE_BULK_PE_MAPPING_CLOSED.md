# Milestone: Pre-merger mapping stretch — **fully closed (v1–v5)**

**Status:** closed / frozen — **archived**  
**Date:** 2026-07-10  
**Decision:** Stop the pre-merger bulk-PE, remnant-mass, and Hopf-\(\Lambda\) mapping stretch.  
**Archive index:** `docs/ARCHIVE_PREMERGER_BULK_PE_MAPPING.md`  
**Exception:** A *genuinely new physical variable* only under a **separate pre-registration**  
(not a mild power rescue of \(M_{\mathrm{tot}}\), SNR, \(d_L\), \(M_f\), or the closed Hopf \(\Lambda\) form).

## Closed family (executed)

| Campaign | Variable | Verdict | Key outcome |
|----------|----------|---------|-------------|
| **v1** | Event-independent α (universal band) | **Demoted** | 0 SUCCESS on true held-outs |
| **v2** | Total mass \(M_{\mathrm{tot}}^p\), \(p=1\) | **FALSIFY** | \(z\approx 30\) |
| **v3a** | Inverse network SNR \(q=1\) | **FALSIFY** | \(z\approx 21\) |
| **v3b** | Luminosity distance \(s=1\) | **FALSIFY** | \(z\approx 18.5\) |
| **v4** | Remnant mass \(M_f^p\), \(p=1\) | **FALSIFY** | Wrong-way scale ~0.89; \(z\approx 30.6\) |
| **v5** | Hopf-lattice \(\Lambda=(\Theta_{\mathrm{link}}/\pi)(M_{f,\mathrm{ref}}/M_f)\) | **FALSIFY** | Scale ~1.12; \(z\approx 28.5\) |

Milestones:  
`docs/MILESTONE_HELD_OUT_TRUE_BBH.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V2.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V3.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V4.md`,  
`docs/MILESTONE_PREMERGER_MAPPING_V5.md`.

**Family verdict:** All pre-registered unifications of \(\alpha_0\) between core and
GW170809 **failed** (bulk PE powers, remnant mass, and this Hopf-geometric form).
Stretch **fully closed** (v1–v5).

## What remains standing

| Item | Status |
|------|--------|
| Core locks \(W_g\), \(\kappa\), \(\phi_b\) | **Frozen** — not reopened by mapping FALSIFY |
| Residual template channel \(\tau_0\) | Unchanged; used for score-only diagnostics |
| GW170809 Gate P / BF / S-1 | **ROBUST_ANOMALY** — large stable residual preference **without** shared \(\alpha_0\) map from v1–v5 |
| GW151012 | **SYSTEMATICS_RISK** — not a design anchor |
| Phases 1–3 scaffolding gates | Separate; not reopened |

## What is stopped

- Mild bulk PE-power unifications: \(M_{\mathrm{tot}}^p\), \((\rho_{\mathrm{ref}}/\rho)^q\), \((d_L/d_{\mathrm{ref}})^s\)  
- Remnant-mass \(M_f^p\) (v4)  
- Hopf-lattice \(\Lambda\) primary form (v5)  
- Post-hoc exponents chosen to hit \(\alpha_{809}/\alpha_{914}\approx 12\) (including unregistered \(d_L^3\))  
- Free exponents / free \(\Lambda\) after seeing held-out \(\hat\alpha\)  
- Dual-sign / GW151012-driven redesign  
- Re-fitting demoted v1 SUCCESS band  

## Operational mode now

1. **Score-only** under frozen locks and existing scripts (historical band claim remains demoted; no SUCCESS restoration).  
2. **No new mapping template** until a document under `docs/PREREG_*.md` names a **genuinely new physical variable** with fixed form, honesty table, SUCCESS/FALSIFY, and explicit non-use of GW151012 for design.  
3. Residual anomaly on GW170809 may be **cited as open / unexplained** under the locked template — not promoted to multi-event discovery.

```bash
# Allowed: re-score under frozen template (no new map)
python scripts/premerger_core_predict.py --predict-event GW170809
python scripts/premerger_bayes_factor.py --event GW170809

# Archival re-runs of closed campaigns OK (do not re-open families)
python scripts/premerger_mapping_v2_score.py
python scripts/premerger_mapping_v3_score.py
python scripts/premerger_mapping_v4_score.py
python scripts/premerger_mapping_v5_score.py

# Not allowed without new PREREG: mapping v6+ rescue of closed forms
```

## Gate for any future mapping

| Requirement | Rule |
|-------------|------|
| Document | New `docs/PREREG_*.md` before code |
| Variable | **Not** closed forms: \(M_{\mathrm{tot}}\) / inv-SNR / \(d_L\) / \(M_f^{\pm}\) / this Hopf \(\Lambda\) |
| Locks | Remain frozen unless independent theory justification (separate process) |
| Design set | No GW151012; prefer blind holdouts after form freeze |
| Honesty | Pre-run predicted β ratios vs empirical ~12 must be stated |

## Explicit non-claims

- Not a claim that the GW170809 residual is non-physical  
- Not a claim that no map exists — only that **these tested families failed**  
- Not a demotion of Hopf locks or \(\Theta_{\mathrm{link}}\) as lattice structure  
- Not a license to float Hopf locks to absorb the anomaly  
