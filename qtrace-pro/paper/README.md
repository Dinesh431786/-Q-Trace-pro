# Q-Trace Pro — Research Paper (LaTeX)

**Q-Trace Pro: Sink-Aware Two-Axis Confidence for Low-False-Positive Detection
of Stealth Supply-Chain Threats in Python**
Dinesh K, H Swetha — Voxelta Private Limited.

`QTracePro_ResearchPaper.pdf` — the compiled paper (IEEE manuscript format,
20 pages, 13 figures, 5 tables, 3 algorithms, 30 references).

Every figure and number is produced from the tool's own measured output; nothing
is hand-authored. The figures are **vector PDFs typeset in the paper's own Times
face** (matplotlib pgf/pdflatex backend), not raster screenshots.

## Reproduce

```bash
# deps: texlive (pdflatex, IEEEtran, booktabs, algorithmicx, listings),
#       python3 + matplotlib, librsvg2-bin (rsvg-convert), bandit, semgrep
./build_paper.sh          # measures corpus, renders figures, typesets the PDF
```

Or step by step:

```bash
python collect_data.py    # run corpus + head-to-head -> paper_data.json
python make_figs.py        # render data figures (pgf/Times) -> figs/*.pdf
rsvg-convert -f pdf -o figs/fig1_arch.pdf     figs/fig1_arch.svg
rsvg-convert -f pdf -o figs/figA_confflow.pdf figs/figA_confflow.svg
python emit_tables.py      # appendix tables from measured data
pdflatex paper.tex && pdflatex paper.tex
```

| File | Role |
|---|---|
| `paper.tex` | the manuscript (IEEEtran) |
| `collect_data.py` | measures Q-Trace/Bandit/Semgrep on the shared corpus |
| `make_figs.py` | renders the 11 data figures (validated palette, Times) |
| `emit_tables.py` | generates the appendix tables from measured data |
| `build_paper.sh` | one-shot reproducible build |
| `paper_data.json` | measured data snapshot the figures/tables read from |
| `figs/` | figure sources (vector PDF + the two hand-drawn SVG diagrams) |

The underlying corpus lives in `../benchmark.py`; the head-to-head harness is
`../tool_comparison.py`. See `../BENCHMARK.md` for the raw reproduced numbers.
