# ⚛️ Q-Trace Pro — The Private Quantum Auditor

**Local-native, air-gapped Python source-code security auditor** that hunts the
threats ordinary SAST tools miss: probabilistic logic bombs, chained/stateful
triggers, cross-function backdoors, covert/steganographic channels, and
anti-analysis evasion — the exact techniques seen in 2024–2026 PyPI supply-chain
attacks (aiocpa, W4SP, Hades/Shai-Hulud, LiteLLM/TeamPCP, telnyx).

Everything runs **entirely on your hardware**. No code ever leaves the machine.

```bash
pip install -r requirements.txt
streamlit run main.py
```

---

## Why it's different

| Capability | How Q-Trace does it |
|---|---|
| **Accurate, low false positives** | Sink-aware confidence scoring. A `random.random() < x` check is only high-confidence when a real execution/exfiltration **sink** sits in the guarded branch — benign sampling drops to *Low*. Two independent axes (severity × confidence), per Bandit/OWASP guidance. |
| **Lightweight & fast** | Custom **pure-NumPy quantum-inspired simulator** (`qsim.py`) replaces the heavyweight `cirq` dependency — ~10× faster import, a few KB instead of hundreds of MB, identical math (validated against cirq). Content-hash caching skips re-analysis. Typical audit: tens of milliseconds. |
| **Provably sound** | Z3 **symbolic reachability** proves whether a sink is actually reachable. Stateful counters are modelled as accumulators of optional increments, so `if k == 99` with one `k += 1` is correctly proven *unreachable* (no false "proof"). |
| **Self-healing** | Every engine runs behind `@resilient` / circuit breakers. A failing or missing engine degrades and is recorded in a health panel — the audit never crashes. Input is validated/sanitised (size limits, NUL stripping). |
| **Industry standard output** | **SARIF 2.1.0** with a proper CWE `taxonomies` block + rule `relationships` + `partialFingerprints` for dedup (consumable by GitHub Code Scanning, DefectDojo, SonarQube), plus a flat JSON report. Every finding is CWE-mapped with a CVSS-style score. |

---

## Architecture

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

### Module map
- **`qsim.py`** — lightweight pure-NumPy quantum simulator (RY/H/X/CNOT + sampling).
- **`quantum_engine.py`** — pattern->circuit mapping, Von Neumann entropy, physics metrics, risk scoring.
- **`pattern_matcher.py`** — taint-based AST pattern detection.
- **`analyzer.py`** — sink-aware orchestrator; the custom detection algorithm.
- **`symbolic_engine.py`** — Z3 symbolic reachability with sound counter modelling.
- **`self_healing.py`** — `@resilient`, `CircuitBreaker`, `retry`, `HealthMonitor`, input validation.
- **`findings.py`** — threat catalog: CWE IDs, severities, confidence, remediation.
- **`report.py`** — SARIF 2.1.0 + JSON serialization (NumPy-safe encoder).
- **`gemini_explainer.py`** — optional AI explanations (modern `google-genai`, local fallback).
- **`main.py`** — Streamlit front end.

## Detection coverage (CWE-mapped)

| Pattern | CWE | Severity |
|---|---|---|
| Probabilistic logic bomb | CWE-511 | High |
| Entangled (multi-condition) bomb | CWE-511 | High |
| Chained / stateful bomb | CWE-511 | High |
| Cross-function embedded malicious code | CWE-506 | Critical |
| Steganographic / covert channel | CWE-515 | Critical |
| Anti-analysis / anti-debug | CWE-489 | Medium |
| Dangerous execution sink (os.system/exec/eval/subprocess) | CWE-78 | High |

## Testing

```bash
python test_qtrace.py     # standalone runner (no pytest needed)
pytest test_qtrace.py     # or via pytest
python benchmark.py       # labelled detection benchmark (recall)
```

---

*Q-Trace Pro — Local-first security, quantum-inspired analysis, zero trust.*
