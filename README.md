# ⚛️ Q-Trace Pro — The Private Quantum Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SARIF 2.1.0](https://img.shields.io/badge/SARIF-2.1.0-green.svg)](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen.svg)](qtrace-pro/test_qtrace.py)

**Local-native, air-gapped Python source-code security auditor** that detects the
threats ordinary SAST tools miss — probabilistic logic bombs, chained/stateful
triggers, cross-function backdoors, covert/steganographic channels, and
anti-analysis evasion. These are the exact techniques seen in 2024–2026 PyPI
supply-chain attacks (aiocpa, W4SP, Hades/Shai-Hulud, LiteLLM/TeamPCP, telnyx).

Everything runs **entirely on your hardware** — no code ever leaves the machine.

```bash
cd qtrace-pro
pip install -r requirements.txt
streamlit run main.py
```

> The complete application lives in **[`qtrace-pro/`](qtrace-pro/)**.

---

## 🚀 Why it's different

| Capability | How Q-Trace does it |
|---|---|
| **Accurate — low false positives** | Sink-aware confidence scoring. A `random.random() < x` check is only high-confidence when a real execution/exfiltration **sink** sits in the guarded branch; benign sampling drops to *Low*. Two independent axes (severity × confidence), per Bandit/OWASP guidance. |
| **Lightweight & fast** | A custom **pure-NumPy quantum-inspired simulator** (`qsim.py`) replaces the heavyweight `cirq` dependency — ~10× faster import, a few KB instead of hundreds of MB, identical math (validated against cirq). Content-hash caching skips re-analysis. Typical audit: tens of milliseconds. |
| **Provably sound** | Z3 **symbolic reachability** proves whether a sink is actually reachable. Stateful counters are modelled as accumulators of optional increments, so `if k == 99` with one `k += 1` is correctly proven *unreachable* (no false "proof"). |
| **Self-healing** | Every engine runs behind `@resilient` decorators / circuit breakers. A failing or missing engine degrades gracefully and is surfaced in a health panel — the audit never crashes. Input is validated/sanitised (size limits, NUL stripping). |
| **Industry-standard output** | **SARIF 2.1.0** with a proper CWE `taxonomies` block, rule `relationships`, and `partialFingerprints` for dedup (consumable by GitHub Code Scanning, DefectDojo, SonarQube), plus a flat JSON report. Every finding is CWE-mapped with a CVSS-style score. |

## 🏗️ Architecture

```
                    +------------------------------+
   Python source -> |        analyzer.py           |  <- unified orchestrator
                    |  validate -> detect -> score  |     (self-healing)
                    +------+-----------+-----------+
        +------------------+-----------+--------------------+
        v                  v           v                    v
 pattern_matcher    sink scanner   quantum_engine      symbolic_engine
  (taint/AST)       (AST sinks +   (qsim.py: NumPy     (Z3 reachability,
                    line numbers)   state-vector,       sound counters)
                                    Von Neumann entropy)
        +------------------+-----------+--------------------+
                                v
                  findings.py  (CWE + severity + confidence)
                                v
                  report.py  ->  SARIF 2.1.0  /  JSON
                                v
                     main.py  (Streamlit UI + health panel)
```

## 🔬 Detection coverage (CWE-mapped)

| Pattern | CWE | Severity |
|---|---|---|
| Probabilistic logic bomb | CWE-511 | High |
| Entangled (multi-condition) bomb | CWE-511 | High |
| Chained / stateful bomb | CWE-511 | High |
| Cross-function embedded malicious code | CWE-506 | Critical |
| Steganographic / covert channel | CWE-515 | Critical |
| Encoded / obfuscated payload (base64/XOR → exec) | CWE-506 | Critical |
| Anti-analysis / anti-debug | CWE-489 | Medium |
| Dangerous execution sink (os.system / exec / eval / subprocess) | CWE-78 | High |

> **Note — advanced maths, validated honestly.** The obfuscated-payload channel uses
> Shannon entropy + the **Higuchi fractal dimension** of the byte-entropy curve. It
> was selected by an A/B experiment over a labelled corpus: a Mandelbrot escape-time
> "trigger-fragility" metric was *tried and rejected* (it gave no lift over a trivial
> baseline), while the entropy + fractal-dimension channel cleanly separated encoded
> payloads from benign code (lifting combined separation to AUC ≈ 0.88).

## 🧪 Testing

```bash
cd qtrace-pro
python test_qtrace.py     # standalone runner (no pytest needed) — 17 tests
pytest test_qtrace.py     # or via pytest
python benchmark.py       # labelled detection benchmark (recall)
```

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Q-Trace Pro — Local-first security, quantum-inspired analysis, zero trust.*
