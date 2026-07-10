# Milestone: arXiv packaging polish (Papers I–IV)

**Status:** complete (local packaging ready)  
**Date:** 2026-07-10  

## Deliverables

| Paper | Source | Role |
|-------|--------|------|
| I | `papers/Lagrangian_Derivation.tex` | Unified action + Gate A-P v2 criteria |
| II | `papers/Relativistic_Completion.tex` | Relativistic lift + quantization outline |
| III | `papers/SM_Derivation.tex` | SM representations, Yukawa, anomalies, RG |
| IV | `papers/Gravity_Emergence.tex` | \(G_N\) schema, weak field, SI bridge |

Also: `papers/Series_Overview.tex`, `papers/README_ARXIV.md`, `papers/Makefile`.

## Packaging

```bash
cd papers
make package
# → arxiv_dist/*_arxiv_source.tar.gz
# → arxiv_dist/hopf_lattice_series_arxiv_source.tar.gz
# → arxiv_dist/hopf_lattice_series_with_pdfs.tar.gz
```

## Polish applied

- Companion-series cross-cites (Papers I–IV), not bare repo paths  
- Softened software-only claims; software listed as optional reproducibility  
- Gate A-P v2 criteria in Paper I (Hessian, multi-amplitude \(W_g\), PDE energy)  
- Dropped `booktabs` dependency (minimal TeX Live builds)  
- `hyperref` with `hidelinks`  
- Build verified with `pdflatex` (two passes)

## Not claimed

- Actual arXiv submission IDs (upload is manual)  
- Peer-review acceptance  
- Completed SM+GR unification  

## Next

1. Optional: upload each paper separately via arXiv (see `papers/README_ARXIV.md`).  
2. After Paper I has an ID, replace “companion note” bibitems with `arXiv:…`.  
