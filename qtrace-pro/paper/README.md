# Q-Trace Pro — Research Paper (Springer LNCS)

**Sink-Aware Two-Axis Confidence for Low-False-Positive Detection of Stealth
Supply-Chain Threats in Python.**
Dinesh K, H Swetha — Voxelta Private Limited.

`QTracePro_ResearchPaper.pdf` is the compiled paper: Springer LNCS format
(`llncs`), 20 pages, 10 figures, 5 tables, 3 algorithms, 52 references.

Every number and figure is produced from the tool's own measured benchmark; nothing
is hand-authored. Data figures are vector PDFs typeset in the paper's Times face via
the matplotlib pgf/pdflatex backend, following scientific-figure convention (full
bounding box, inward minor ticks, grayscale-safe hatching, multi-panel composites).
System diagrams are restrained grayscale schematics.

The manuscript follows the writing standards of the `academic-research-skills`
suite: neutral academic register, punctuation control (no em-dash overuse), formal
problem definition, and hedged claims.

## Reproduce

```bash
# deps: texlive (pdflatex, llncs, booktabs, algorithmicx, listings),
#       python3 + matplotlib, librsvg2-bin (rsvg-convert), bandit, semgrep
./build_paper.sh          # measures corpus, renders figures, typesets the PDF
```

Step by step:

```bash
python collect_data.py     # run corpus + head-to-head -> paper_data.json
python make_figs.py        # render data figures (pgf/Times) -> figs/*.pdf
rsvg-convert -f pdf -o figs/fig1_arch.pdf     figs/fig1_arch.svg
rsvg-convert -f pdf -o figs/figA_confflow.pdf figs/figA_confflow.svg
python emit_tables.py      # appendix tables from measured data
pdflatex paper.tex && pdflatex paper.tex
```

| File | Role |
|---|---|
| `paper.tex` | the manuscript (Springer `llncs`) |
| `collect_data.py` | measures Q-Trace/Bandit/Semgrep on the shared corpus |
| `make_figs.py` | renders the data figures (validated palette, Times) |
| `emit_tables.py` | generates appendix tables from measured data |
| `build_paper.sh` | one-shot reproducible build |
| `paper_data.json` | measured data snapshot the figures/tables read from |
| `figs/` | figure sources (vector PDF + two grayscale SVG diagrams) |

The corpus lives in `../benchmark.py`; the head-to-head harness is
`../tool_comparison.py`; raw reproduced numbers are in `../BENCHMARK.md`.
