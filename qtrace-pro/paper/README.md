# Q-Trace Pro — Research Paper

**Q-Trace Pro: Sink-Aware Two-Axis Confidence for Low-False-Positive Detection
of Stealth Supply-Chain Threats in Python**
Dinesh K, H Swetha — Voxelta Private Limited.

`QTracePro_ResearchPaper.pdf` — the compiled preprint (22 pages, 13 figures).

Every figure and number in the paper is produced from the tool's own measured
output; nothing is hand-authored. To reproduce end-to-end:

```bash
pip install -r ../requirements.txt bandit semgrep matplotlib pymupdf
python collect_data.py     # runs the corpus + head-to-head -> paper_data.json
python make_figs.py        # renders every figure -> figs/*.svg
python build_pdf.py        # inlines figures into paper.html -> the PDF
```

| File | Role |
|---|---|
| `paper.html` | the manuscript source (figure placeholders) |
| `collect_data.py` | measures Q-Trace/Bandit/Semgrep on the shared corpus |
| `make_figs.py` | generates all data figures (validated palette) |
| `build_pdf.py` | inlines figures, renders the PDF via headless Chromium |
| `paper_data.json` | the measured data snapshot the figures read from |
| `figs/` | all figures (SVG) |

The underlying corpus lives in `../benchmark.py`; the head-to-head harness is
`../tool_comparison.py`. See `../BENCHMARK.md` for the raw reproduced numbers.
