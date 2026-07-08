#!/usr/bin/env bash
# Reproducible build of the Q-Trace Pro research paper (LaTeX).
# Requires: texlive (pdflatex, IEEEtran, booktabs, algorithmicx, listings),
#           python3 + matplotlib (pgf backend), rsvg-convert, the Q-Trace repo.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/4] measuring corpus -> paper_data.json"
python collect_data.py

echo "[2/4] rendering figures (pgf/Times vector PDF)"
python make_figs.py
rsvg-convert -f pdf -o figs/fig1_arch.pdf     figs/fig1_arch.svg
rsvg-convert -f pdf -o figs/figA_confflow.pdf figs/figA_confflow.svg

echo "[3/4] emitting appendix tables"
python emit_tables.py

echo "[4/4] typesetting (two pdflatex passes)"
pdflatex -interaction=nonstopmode -halt-on-error paper.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error paper.tex >/dev/null
mv -f paper.pdf QTracePro_ResearchPaper.pdf
echo "done -> QTracePro_ResearchPaper.pdf"
