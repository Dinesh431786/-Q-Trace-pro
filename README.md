# ⚛️ Q-Trace Pro — The Private Quantum Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SARIF 2.1.0](https://img.shields.io/badge/SARIF-2.1.0-green.svg)](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
[![Tests](https://img.shields.io/badge/tests-31%2F31%20passing-brightgreen.svg)](qtrace-pro/test_qtrace.py)

**Local-native, air-gapped Python source-code security scanner.** It covers two
families of risk in one pass:

* **Classic vulnerabilities** — the everyday OWASP/CWE issues real SAST tools
  flag (SQL injection, command injection, insecure deserialization, hard-coded
  secrets, weak crypto, SSRF, disabled TLS verification, path traversal, XXE…).
* **Advanced / stealth threats** ordinary tools miss — probabilistic logic
  bombs, chained/stateful triggers, cross-function backdoors, covert/encoded
  payloads, and anti-analysis evasion — the exact techniques seen in 2024–2026
  PyPI supply-chain attacks (aiocpa, W4SP, Hades/Shai-Hulud, LiteLLM/TeamPCP,
  telnyx).

Use it from the **command line** (CI/CD, like Bandit/Semgrep) or the Streamlit UI.
Everything runs **entirely on your hardware** — no code ever leaves the machine.

```bash
cd qtrace-pro
pip install -r requirements.txt

# CLI — scan a file or directory (SARIF/JSON/text, CI-friendly exit codes)
python cli.py scan path/to/code --min-severity Medium --fail-on High

# or the interactive UI
streamlit run main.py
```

> The complete application lives in **[`qtrace-pro/`](qtrace-pro/)**.

---

## 🚀 Why it's different

| Capability | How Q-Trace does it |
|---|---|
| **Complete coverage** | Classic OWASP/CWE rules (SQLi, command injection, deserialization, secrets, weak crypto, SSRF, TLS, traversal, XXE…) **plus** stealth logic-bomb / covert-payload detection — in a single scan, from CLI or UI. |
| **Accurate — low false positives** | Sink-aware confidence scoring. A `random.random() < x` check is only high-confidence when a real execution/exfiltration **sink** sits in the guarded branch; benign sampling drops to *Low*. Two independent axes (severity × confidence), per Bandit/OWASP guidance. Every classic rule has a safe-variant test. |
| **Lightweight & fast** | A custom **pure-NumPy quantum-inspired simulator** (`qsim.py`) replaces the heavyweight `cirq` dependency — ~10× faster import, a few KB instead of hundreds of MB, identical math (validated against cirq). Content-hash caching skips re-analysis. Typical audit: tens of milliseconds. |
| **Provably sound** | Z3 **symbolic reachability** proves whether a sink is actually reachable. Stateful counters are modelled as accumulators of optional increments, so `if k == 99` with one `k += 1` is correctly proven *unreachable* (no false "proof"). |
| **Self-healing** | Every engine runs behind `@resilient` decorators / circuit breakers. A failing or missing engine degrades gracefully and is surfaced in a health panel — the audit never crashes. Input is validated/sanitised (size limits, NUL stripping). |
| **Industry-standard output** | **SARIF 2.1.0** with a proper CWE `taxonomies` block, rule `relationships`, and `partialFingerprints` for dedup (consumable by GitHub Code Scanning, DefectDojo, SonarQube), plus a flat JSON report. Every finding is CWE-mapped with a CVSS-style score. |

## 🏗️ Architecture

```
  cli.py  /  main.py (Streamlit)
                 v
        +------------------------------+
        |        analyzer.py           |  <- unified orchestrator
        |  validate -> detect -> score  |     (self-healing, content-hash cache)
        +--+------+------+------+------+--+
           v      v      v      v      v
   classic_  pattern_  sink   quantum_  symbolic_   obfuscation
   rules     matcher   scan   engine    engine      (entropy +
  (OWASP/   (taint/   (AST   (qsim.py  (Z3 sound    Higuchi
   CWE SAST) AST)     sinks)  NumPy)    counters)   fractal dim)
           +------+------+------+------+------+
                          v
            findings.py  (CWE + severity + confidence)
                          v
            report.py  ->  SARIF 2.1.0  /  JSON  /  text
```

## 🔬 Detection coverage (CWE-mapped)

**Classic vulnerabilities (OWASP / CWE — the SAST baseline):**

| Rule | CWE | Severity |
|---|---|---|
| SQL injection | CWE-89 | High |
| OS command injection (`shell=True` / tainted) | CWE-78 | High |
| Insecure deserialization (pickle / yaml.load / marshal) | CWE-502 | High |
| Hard-coded credentials | CWE-798 | High |
| Disabled TLS validation (`verify=False`) | CWE-295 | High |
| Server-side request forgery (SSRF) | CWE-918 | High |
| Path traversal | CWE-22 | High |
| Weak hash (MD5/SHA1) / weak cipher (DES/RC4/ECB) | CWE-327 | Medium |
| Insufficiently random values for secrets | CWE-330 | Medium |
| XML external entity (XXE) | CWE-611 | Medium |
| Insecure temp file (`tempfile.mktemp`) | CWE-377 | Medium |
| Debug mode enabled in production | CWE-489 | Medium |
| Cleartext transmission (`http://`) | CWE-319 | Medium |

**Advanced / stealth threats (what ordinary tools miss):**

| Pattern | CWE | Severity |
|---|---|---|
| Probabilistic logic bomb | CWE-511 | High |
| Entangled (multi-condition) bomb | CWE-511 | High |
| Chained / stateful bomb | CWE-511 | High |
| Cross-function embedded malicious code | CWE-506 | Critical |
| Steganographic / covert channel (chr+ord / XOR) | CWE-515 | Critical |
| Encoded / obfuscated payload (base64/XOR → exec) | CWE-506 | Critical |
| Anti-analysis / anti-debug | CWE-489 | Medium |
| Dangerous execution sink (os.system / exec / eval / subprocess) | CWE-78 | High |

Every finding carries two independent axes — **severity** (impact) and
**confidence** (evidence strength) — per Bandit/OWASP guidance, so triage is
realistic and false positives stay low (each classic rule is paired with a
safe-variant test).

> **Note — advanced maths, validated honestly.** The obfuscated-payload channel uses
> Shannon entropy + the **Higuchi fractal dimension** of the byte-entropy curve. It
> was selected by an A/B experiment over a labelled corpus: a Mandelbrot escape-time
> "trigger-fragility" metric was *tried and rejected* (it gave no lift over a trivial
> baseline), while the entropy + fractal-dimension channel cleanly separated encoded
> payloads from benign code (lifting combined separation to AUC ≈ 0.97). See
> [`qtrace-pro/experiments/`](qtrace-pro/experiments/).

## 💻 Command-line usage

```bash
python cli.py scan app.py                       # human-readable text
python cli.py scan src/ --format sarif -o out.sarif   # SARIF 2.1.0 for GitHub/DefectDojo
python cli.py scan . --min-severity Medium --fail-on High
```

Exit codes: `0` = nothing at/above `--fail-on`, `2` = findings at/above the gate
(use this to break a CI build), `1` = usage/IO error.

## 🧪 Testing

```bash
cd qtrace-pro
python test_qtrace.py     # standalone runner (no pytest needed) — 31 tests
pytest test_qtrace.py     # or via pytest
python benchmark.py       # labelled detection benchmark (recall)
```

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Q-Trace Pro — Local-first security, quantum-inspired analysis, zero trust.*
