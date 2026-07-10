# arXiv packaging — Gauged Hopf Lattice scaffold series

**Date:** 2026-07-10  
**Papers (I–IV):**

| # | Source | Title (short) |
|---|--------|----------------|
| I | `Lagrangian_Derivation.tex` | Unified Action Principle |
| II | `Relativistic_Completion.tex` | Relativistic Completion |
| III | `SM_Derivation.tex` | SM Particle Content |
| IV | `Gravity_Emergence.tex` | Emergent Gravity |

Optional cover: `Series_Overview.tex`.

Related (not in I–IV core package): `GW_Burst_Threshold.tex`.

## Build

```bash
cd papers
make              # four PDFs
make package      # PDFs + tarballs in arxiv_dist/
make clean        # aux files
make distclean    # PDFs + dist
```

Requires TeX Live (`pdflatex`).

## arXiv upload conventions

### Option A — four separate submissions (recommended)

For each paper `P` in {Lagrangian_Derivation, Relativistic_Completion, SM_Derivation, Gravity_Emergence}:

1. Use `arxiv_dist/P_arxiv_source.tar.gz` (contains only `P.tex`).  
   Or upload `P.tex` alone via the arXiv process form.
2. Process with **TeX Live** / `pdflatex` (default).
3. Category suggestions (adjust as needed):
   - I, II: `hep-th` primary; optional `gr-qc` cross-list for II/IV
   - III: `hep-ph` primary; optional `hep-th`
   - IV: `gr-qc` primary; optional `hep-th`
4. After I has an arXiv ID, update companion `\bibitem`s in II–IV to cite
   `arXiv:XXXX.XXXXX` instead of “companion note”.

### Option B — single series bundle (ancillary / institutional)

Use `arxiv_dist/hopf_lattice_series_arxiv_source.tar.gz` as a multi-file
source package. Prefer separate submissions for discoverability.

### Comments for arXiv form (template)

> Scaffold notes for a gauged Hopf-lattice EFT: frozen topological locks
> (W_g=350/π, κ≈0.85, φ_b*), gated kinetic/health criteria. No claim of
> completed SM+GR unification or observational discovery. Companion notes
> in the same series treat relativity, SM content, and gravity.

## Discipline (do not remove)

Each paper states explicitly:

- Core locks are **inputs**, not free fits  
- FAIL demotes mappings, not locks by default  
- No multi-event GW discovery claim from this series  
- Companion software is optional reproducibility  

## Local distribution

`arxiv_dist/hopf_lattice_series_with_pdfs.tar.gz` includes PDFs for offline
sharing. **Do not** upload PDFs as primary arXiv sources when TeX is available.

## Checklist before submit

- [ ] `make package` completes with exit 0  
- [ ] Each PDF opens and shows abstract + bibliography  
- [ ] Titles/authors match intended metadata  
- [ ] Companion cites still say “companion note” *or* have real arXiv IDs  
- [ ] License choice decided (arXiv default or CC)  
