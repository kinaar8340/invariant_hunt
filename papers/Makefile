# Build and package gated Hopf-lattice notes for arXiv-style distribution.
#
# Usage:
#   make              # build all four PDFs
#   make package      # PDFs + source tarballs under arxiv_dist/
#   make clean

LATEX ?= pdflatex
LATEXFLAGS = -interaction=nonstopmode -halt-on-error

PAPERS = \
	Lagrangian_Derivation \
	Relativistic_Completion \
	SM_Derivation \
	Gravity_Emergence

PDFS = $(addsuffix .pdf,$(PAPERS))
DIST = arxiv_dist

.PHONY: all package clean distclean overview

all: $(PDFS)

%.pdf: %.tex
	$(LATEX) $(LATEXFLAGS) $<
	$(LATEX) $(LATEXFLAGS) $<

overview: Series_Overview.pdf

package: all overview
	mkdir -p $(DIST)
	for p in $(PAPERS); do \
		mkdir -p $(DIST)/$$p; \
		cp $$p.tex $(DIST)/$$p/; \
		cp $$p.pdf $(DIST)/$$p/; \
		tar -czf $(DIST)/$${p}_arxiv_source.tar.gz -C . $$p.tex; \
	done
	tar -czf $(DIST)/hopf_lattice_series_arxiv_source.tar.gz \
		Lagrangian_Derivation.tex \
		Relativistic_Completion.tex \
		SM_Derivation.tex \
		Gravity_Emergence.tex \
		Series_Overview.tex \
		README_ARXIV.md \
		Makefile
	tar -czf $(DIST)/hopf_lattice_series_with_pdfs.tar.gz \
		$(PDFS) \
		Series_Overview.pdf \
		Lagrangian_Derivation.tex \
		Relativistic_Completion.tex \
		SM_Derivation.tex \
		Gravity_Emergence.tex \
		Series_Overview.tex \
		README_ARXIV.md \
		Makefile
	cp Series_Overview.pdf $(DIST)/
	cp README_ARXIV.md $(DIST)/
	@echo ""
	@echo "Wrote packages under $(DIST)/"
	@ls -la $(DIST)/

clean:
	rm -f *.aux *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz

distclean: clean
	rm -f $(PDFS) Series_Overview.pdf
	rm -rf $(DIST)
