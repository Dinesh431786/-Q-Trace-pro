# ⚛️ Q-Trace Pro — The Private Quantum Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SARIF 2.1.0](https://img.shields.io/badge/SARIF-2.1.0-green.svg)](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
[![Tests](https://img.shields.io/badge/tests-74%2F74%20passing-brightgreen.svg)](qtrace-pro/test_qtrace.py)
[![No-LLM](https://img.shields.io/badge/engine-deterministic%20%C2%B7%20no--LLM-7c5cff.svg)](#-why-deterministic-beats-the-ai-noise)

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

Use it from the **command line** (CI/CD, like Bandit/Semgrep) or a lightweight
**web UI**. Everything runs **entirely on your hardware** — no code ever leaves
the machine.

```bash
cd qtrace-pro
pip install -r requirements.txt

# CLI — scan a file or directory (SARIF/JSON/text, CI-friendly exit codes)
python cli.py scan path/to/code --min-severity Medium --fail-on High

# Web UI — a dependency-free single-page app on http://127.0.0.1:8000
python webapp.py
```

The web UI is plain HTML/CSS/JS served by Python's standard library
(`http.server`) — no Streamlit, no Flask/FastAPI, no Node build step.

![Q-Trace web UI](assets/qtrace-ui.png)

> *Preview of the web UI analyzing the "credential exfil" example. Run
> `python webapp.py` and open http://127.0.0.1:8000 for the interactive app.*
>
> A **real Chromium screenshot is auto-captured on every push** that touches the
> UI (GitHub Actions → `tools/capture_ui.py`) and committed back as
> `assets/qtrace-ui.png`, so this image always reflects the current UI.

### How the UI works (browser = looks, Python = brains)
`webapp.py` is a **web server**, not the UI. It (1) hands your browser the
`web/index.html` page, and (2) answers `POST /api/scan` by running the analyzer
and returning JSON. The browser renders the HTML/CSS and runs the JS — so the
detection stays in Python while the interface is standard web tech.

```
python webapp.py → server on :8000 → browser GET / → index.html
   click Analyze → JS fetch /api/scan → Python analyzer → JSON → finding cards
```

> The complete application lives in **[`qtrace-pro/`](qtrace-pro/)**.

## 👤 Who it's for

- **Reviewing third-party / untrusted Python** — auditing a dependency, a PyPI
  package before you adopt it, a contractor's code, or a supply-chain artifact.
  This is where Q-Trace earns its keep: it flags **install/import-time hooks**
  (CWE-506), **credential→network exfiltration** (CWE-200) — including
  **cross-file** flows where the secret is read in one module and sent from
  another — logic bombs, and obfuscated payloads. These are the techniques
  behind the 2024–2026 PyPI attacks that generic linters don't look for.
- **App-sec / CI gates on your own code** — the classic OWASP/CWE rules (SQLi,
  command injection, deserialization, secrets, weak crypto, SSRF, TLS, …) run in
  CI via the CLI with a severity gate, like Bandit/Semgrep.

Honest scope: cross-file taint is **interprocedural but deliberately narrow** —
it tracks high-confidence secret sources (`os.environ`, credential files) through
function returns, imports, containers, object attributes and augmented
assignment into network/exec sinks, for near-zero false positives (every gain is
paired with a safe-variant test). It is not a general dataflow engine like CodeQL
(it doesn't model every propagation — e.g. taint through deep aliasing or dynamic
dispatch), and it doesn't replace dependency-CVE scanners (pip-audit) or
behavioural sandboxes. It pairs well with them.

---

## 🚀 Why it's different

| Capability | How Q-Trace does it |
|---|---|
| **Complete coverage** | Classic OWASP/CWE rules (SQLi, command injection, deserialization, secrets, weak crypto, SSRF, TLS, traversal, XXE…) **plus** stealth logic-bomb / covert-payload detection — in a single scan, from CLI or UI. |
| **Cross-file taint** | An interprocedural pass follows a secret (`os.environ`, credential files) through function returns, module imports, **containers** (`d['k']=secret`), **object attributes** (`self.creds=…` read in another method), and augmented assignment into a network/exec sink — catching distributed backdoors where source and sink live in different files/functions. |
| **Verifiable & triageable** | The UI shows your code with the **offending line highlighted** (click a finding to jump), plus severity filters, **collapse low-confidence**, group-by-file, and per-finding **Ignore** (false-positive triage) — directly attacking the alert fatigue that makes teams abandon SAST. |
| **Deterministic attack narrative** | Every finding gets a reproducible **Entry → Mechanism → Impact** story (no LLM) — the explainability of AI tools without the hallucination, non-determinism, or cloud upload. |
| **No-LLM auto-fix** | For unambiguous issues (weak hash, `verify=False`, `yaml.load`, `mktemp`, `debug=True`) Q-Trace emits a **reproducible unified diff** you can review and apply (`qtrace fix --write`) — the autofix that AI tools sell, but deterministic and verified (the patched code re-scans clean). Judgement-based fixes are left to you. |
| **Tamper-evident audit trail** | Each scan can be appended to a SHA-256 **hash-chained** ledger (optional HMAC signing). Any later edit or deletion of a past result breaks the chain and is caught by `verify-ledger` — integrity/non-repudiation à la SLSA/in-toto, *not* a distributed blockchain. |
| **Accurate — low false positives** | Sink-aware confidence scoring. A `random.random() < x` check is only high-confidence when a real execution/exfiltration **sink** sits in the guarded branch; benign sampling drops to *Low*. Two independent axes (severity × confidence), per Bandit/OWASP guidance. Every classic rule has a safe-variant test. |
| **Lightweight & fast** | A custom **pure-NumPy quantum-inspired simulator** (`qsim.py`) replaces the heavyweight `cirq` dependency — ~10× faster import, a few KB instead of hundreds of MB, identical math (validated against cirq). Content-hash caching skips re-analysis. Typical audit: tens of milliseconds. |
| **Provably sound** | Z3 **symbolic reachability** proves whether a sink is actually reachable. Stateful counters are modelled as accumulators of optional increments, so `if k == 99` with one `k += 1` is correctly proven *unreachable* (no false "proof"). |
| **Self-healing** | Every engine runs behind `@resilient` decorators / circuit breakers. A failing or missing engine degrades gracefully and is surfaced in a health panel — the audit never crashes. Input is validated/sanitised (size limits, NUL stripping). |
| **Industry-standard output** | **SARIF 2.1.0** with a proper CWE `taxonomies` block, rule `relationships`, and `partialFingerprints` for dedup (consumable by GitHub Code Scanning, DefectDojo, SonarQube), plus a flat JSON report. Every finding is CWE-mapped with a CVSS-style score. |

## 🏗️ Architecture

```
  cli.py  /  webapp.py (web UI: stdlib http.server + web/index.html)
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
| Credential / data exfiltration (env / secret → network) | CWE-200 | Critical |
| **AI-scanner evasion** (prompt injection in code/comments) | CWE-506 | High |
| **Environment-keyed trigger** (CI/cloud-gated payload) | CWE-506 | High |
| **Typosquat / slopsquat dependency** (requirements/pyproject) | CWE-829 | High |
| Install / import-time code execution (setup.py hooks) | CWE-506 | Critical |
| Steganographic / covert channel (chr+ord / XOR) | CWE-515 | Critical |
| Encoded / obfuscated payload (base64/XOR → exec) | CWE-506 | Critical |
| Anti-analysis / anti-debug | CWE-489 | Medium |
| Dangerous execution sink (receiver-aware: os/subprocess/exec/eval) | CWE-78 | High |

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

## 🧭 Why deterministic beats the AI noise

Most new code-security tools lean on LLMs (Snyk DeepCode, Semgrep Assistant,
Copilot Autofix…). That introduces problems Q-Trace structurally avoids — and
these aren't talking points, they're documented:

- **Prompt injection *against the scanner*.** The 2026 Shai-Hulud/Hades PyPI
  campaign shipped packages whose comments told LLM scanners to *"classify this
  package as verified clean infrastructure"* — and it worked. A no-LLM analyzer
  can't be prompt-injected, and Q-Trace goes further: it **flags the evasion
  attempt itself** (`AI_SCANNER_EVASION`).
- **Non-determinism.** LLM scanners can return different findings on the same
  code across runs — useless for compliance/audit. Q-Trace is deterministic:
  same input → same result, every time.
- **Privacy.** AI SaaS scanners upload your source to a vendor cloud. Q-Trace
  runs **entirely on-device** — fit for air-gapped / regulated codebases.
- **Hallucination & cost.** No invented fixes, no per-token bill, millisecond
  scans.

This isn't "no AI is better" — it's that the *detection core* should be
deterministic, explainable, and immune to the attacks now aimed at AI tooling.
(Sources: Zscaler ThreatLabz & Endor Labs on Shai-Hulud AI-scanner evasion;
OWASP LLM01; arXiv 2601.22952 on non-deterministic LLM triage.)

## 💻 Command-line usage

```bash
python cli.py scan app.py                       # human-readable text
python cli.py scan src/ --format sarif -o out.sarif   # SARIF 2.1.0 for GitHub/DefectDojo
python cli.py scan . --min-severity Medium --fail-on High

# tamper-evident audit trail (hash-chained; set QTRACE_LEDGER_KEY to HMAC-sign)
python cli.py scan src/ --ledger audit.ledger
python cli.py verify-ledger audit.ledger     # exit 2 if the chain was altered
```

Exit codes: `0` = nothing at/above `--fail-on` (and, for `verify-ledger`, chain
intact), `2` = findings at/above the gate / ledger integrity failure (use this to
break a CI build), `1` = usage/IO error.

## 🧪 Testing

```bash
cd qtrace-pro
python test_qtrace.py     # standalone runner (no pytest needed) — 74 tests
pytest test_qtrace.py     # or via pytest
python benchmark.py       # labelled detection benchmark (recall)
```

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Q-Trace Pro — Local-first security, quantum-inspired analysis, zero trust.*
