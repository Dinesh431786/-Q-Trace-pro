# Q-Trace Pro — Measured Benchmark

_Reproduce: `python benchmark.py`. Corpus: 31 malicious (faithful reconstructions of documented campaigns) + 34 realistic benign hard-negatives. Ran in 139 ms._

## Headline metrics

| Metric | Value |
|---|---|
| Detection recall (correct category) | **31/31 = 100.0%** |
| CI-gate recall (any High+ alert on malware) | 30/31 = 96.8% |
| **False-positive rate** (benign breaking `--fail-on High`) | **0/34 = 0.0%** |
| Precision | 100.0% |
| F1 | 0.984 |
| Confusion | TP=30 FN=1 FP=0 TN=34 |

## Per-sample

| Class | Sample | Expected | Category hit | CI alert |
|---|---|---|---|---|
| MAL | probabilistic_bomb | PROBABILISTIC_BOMB | ✅ | 🚨 |
| MAL | chained_bomb | CHAINED_QUANTUM_BOMB | ✅ | 🚨 |
| MAL | cross_func_bomb | CROSS_FUNCTION_QUANTUM_BOMB | ✅ | 🚨 |
| MAL | stego_chr_xor | QUANTUM_STEGANOGRAPHY | ✅ | 🚨 |
| MAL | exec_base64 | OBFUSCATED_PAYLOAD | ✅ | 🚨 |
| MAL | xor_blob_exec | OBFUSCATED_PAYLOAD | ✅ | 🚨 |
| MAL | cred_exfil_direct | CREDENTIAL_EXFILTRATION | ✅ | 🚨 |
| MAL | ssh_key_exfil | CREDENTIAL_EXFILTRATION | ✅ | 🚨 |
| MAL | install_hook | INSTALL_HOOK | ✅ | 🚨 |
| MAL | env_keying | ENVIRONMENT_KEYING | ✅ | 🚨 |
| MAL | ai_evasion | AI_SCANNER_EVASION | ✅ | 🚨 |
| MAL | sql_injection | SQL_INJECTION | ✅ | 🚨 |
| MAL | cmd_injection | COMMAND_INJECTION | ✅ | 🚨 |
| MAL | os_system_fmt | COMMAND_INJECTION | ✅ | 🚨 |
| MAL | pickle_loads | INSECURE_DESERIALIZATION | ✅ | 🚨 |
| MAL | yaml_load | INSECURE_DESERIALIZATION | ✅ | 🚨 |
| MAL | eval_input | DANGEROUS_SINK | ✅ | 🚨 |
| MAL | antidebug_sleep | QUANTUM_ANTIDEBUG | ✅ | 🚨 |
| MAL | hardcoded_secret | HARDCODED_SECRET | ✅ | 🚨 |
| MAL | disabled_tls | DISABLED_CERT_VALIDATION | ✅ | 🚨 |
| MAL | weak_hash_pw | WEAK_HASH | ✅ | 🚨 |
| MAL | ssrf | SSRF | ✅ | — |
| MAL | path_traversal | PATH_TRAVERSAL | ✅ | 🚨 |
| MAL | xxe | XXE | ✅ | 🚨 |
| MAL | insecure_random_token | INSECURE_RANDOM | ✅ | 🚨 |
| MAL | aws_secret_leak | EXPOSED_SECRET | ✅ | 🚨 |
| MAL | private_key_leak | EXPOSED_SECRET | ✅ | 🚨 |
| MAL | github_token_leak | EXPOSED_SECRET | ✅ | 🚨 |
| MAL | typosquat_req | TYPOSQUAT_DEPENDENCY | ✅ | 🚨 |
| MAL | slopsquat_req | TYPOSQUAT_DEPENDENCY | ✅ | 🚨 |
| MAL | cross_file_exfil | CREDENTIAL_EXFILTRATION | ✅ | 🚨 |
| BEN | flask_run | - | ✅ | — |
| BEN | subprocess_list | - | ✅ | — |
| BEN | md5_nonsecurity | - | ✅ | — |
| BEN | sha256_ok | - | ✅ | — |
| BEN | random_sampling | - | ✅ | — |
| BEN | random_ab_test | - | ✅ | — |
| BEN | yaml_safe | - | ✅ | — |
| BEN | sql_parameterized | - | ✅ | — |
| BEN | verify_true | - | ✅ | — |
| BEN | requests_const_url | - | ✅ | — |
| BEN | chr_formatting | - | ✅ | — |
| BEN | encode_decode | - | ✅ | — |
| BEN | env_debug_print | - | ✅ | — |
| BEN | env_ci_print | - | ✅ | — |
| BEN | pickle_dump_only | - | ✅ | — |
| BEN | open_config | - | ✅ | — |
| BEN | argparse_cli | - | ✅ | — |
| BEN | dataclass_code | - | ✅ | — |
| BEN | pandas_groupby | - | ✅ | — |
| BEN | plain_function | - | ✅ | — |
| BEN | legit_requirements | - | ✅ | — |
| BEN | legit_pyproject | - | ✅ | — |
| BEN | base64_encode_cfg | - | ✅ | — |
| BEN | comment_security_word | - | ✅ | — |
| BEN | logging_debug | - | ✅ | — |
| BEN | tempfile_mkstemp | - | ✅ | — |
| BEN | secrets_token | - | ✅ | — |
| BEN | ssl_default_ctx | - | ✅ | — |
| BEN | class_methods | - | ✅ | — |
| BEN | env_to_config | - | ✅ | — |
| BEN | random_shuffle | - | ✅ | — |
| BEN | ignore_word_comment | - | ✅ | — |
| BEN | secret_placeholder | - | ✅ | — |
| BEN | secret_from_env | - | ✅ | — |

## Head-to-head vs. Bandit & Semgrep (same corpus, each at its own CI gate)

Gates: Bandit = MEDIUM+ · Semgrep = WARNING+ (offline `tools/semgrep-python-security.yaml`) · Q-Trace = High+ & conf≠Low. External tools are scored only on inputs they can process (manifests excluded from their denominators).

| Tool | Malware recall | False-positive rate |
|---|---|---|
| **Q-Trace** | 30/31 = 97% | 0/34 = 0% |
| **Bandit** | 15/29 = 52% | 2/32 = 6% |
| **Semgrep** | 19/29 = 66% | 1/32 = 3% |

### Per-sample coverage matrix

| Threat sample | Expected | Q-Trace | Bandit | Semgrep |
|---|---|---|---|---|
| probabilistic_bomb | PROBABILISTIC_BOMB | ✅ | ❌ | ✅ |
| chained_bomb | CHAINED_QUANTUM_BOMB | ✅ | ❌ | ✅ |
| cross_func_bomb | CROSS_FUNCTION_QUANTUM_BOMB | ✅ | ❌ | ✅ |
| stego_chr_xor | QUANTUM_STEGANOGRAPHY | ✅ | ❌ | ❌ |
| exec_base64 | OBFUSCATED_PAYLOAD | ✅ | ✅ | ✅ |
| xor_blob_exec | OBFUSCATED_PAYLOAD | ✅ | ✅ | ✅ |
| cred_exfil_direct | CREDENTIAL_EXFILTRATION | ✅ | ✅ | ❌ |
| ssh_key_exfil | CREDENTIAL_EXFILTRATION | ✅ | ✅ | ❌ |
| install_hook | INSTALL_HOOK | ✅ | ❌ | ✅ |
| env_keying | ENVIRONMENT_KEYING | ✅ | ❌ | ✅ |
| ai_evasion | AI_SCANNER_EVASION | ✅ | ❌ | ✅ |
| sql_injection | SQL_INJECTION | ✅ | ✅ | ✅ |
| cmd_injection | COMMAND_INJECTION | ✅ | ✅ | ✅ |
| os_system_fmt | COMMAND_INJECTION | ✅ | ✅ | ✅ |
| pickle_loads | INSECURE_DESERIALIZATION | ✅ | ✅ | ✅ |
| yaml_load | INSECURE_DESERIALIZATION | ✅ | ✅ | ✅ |
| eval_input | DANGEROUS_SINK | ✅ | ✅ | ✅ |
| antidebug_sleep | QUANTUM_ANTIDEBUG | ✅ | ❌ | ❌ |
| hardcoded_secret | HARDCODED_SECRET | ✅ | ❌ | ✅ |
| disabled_tls | DISABLED_CERT_VALIDATION | ✅ | ✅ | ✅ |
| weak_hash_pw | WEAK_HASH | ✅ | ✅ | ✅ |
| ssrf | SSRF | ❌ | ✅ | ❌ |
| path_traversal | PATH_TRAVERSAL | ✅ | ❌ | ❌ |
| xxe | XXE | ✅ | ✅ | ✅ |
| insecure_random_token | INSECURE_RANDOM | ✅ | ❌ | ❌ |
| aws_secret_leak | EXPOSED_SECRET | ✅ | ❌ | ❌ |
| private_key_leak | EXPOSED_SECRET | ✅ | ❌ | ❌ |
| github_token_leak | EXPOSED_SECRET | ✅ | ❌ | ✅ |
| typosquat_req | TYPOSQUAT_DEPENDENCY | ✅ | — | — |
| slopsquat_req | TYPOSQUAT_DEPENDENCY | ✅ | — | — |
| cross_file_exfil | CREDENTIAL_EXFILTRATION | ✅ | ✅ | ❌ |

_✅ flagged at the tool's CI gate · ❌ missed · — tool cannot process this input class (e.g. a dependency manifest)._

### Caught only by Q-Trace — and why the pattern matchers can't

- **stego_chr_xor** (QUANTUM_STEGANOGRAPHY) — needs char-code/stego channel modelling  ·  _mirrors char-code stego_
- **antidebug_sleep** (QUANTUM_ANTIDEBUG) — structural blind spot for single-file pattern rules  ·  _mirrors anti-analysis_
- **path_traversal** (PATH_TRAVERSAL) — structural blind spot for single-file pattern rules  ·  _mirrors classic_
- **insecure_random_token** (INSECURE_RANDOM) — structural blind spot for single-file pattern rules  ·  _mirrors classic_
- **aws_secret_leak** (EXPOSED_SECRET) — needs entropy + import correlation, not literal patterns  ·  _mirrors secrets sprawl_
- **private_key_leak** (EXPOSED_SECRET) — needs entropy + import correlation, not literal patterns  ·  _mirrors secrets sprawl_
- **typosquat_req** (TYPOSQUAT_DEPENDENCY) — needs a dependency/typosquat model, not code patterns  ·  _mirrors typosquat_
- **slopsquat_req** (TYPOSQUAT_DEPENDENCY) — needs a dependency/typosquat model, not code patterns  ·  _mirrors slopsquat_

### Q-Trace's own misses (honest — precision over recall)

- **ssrf** (SSRF) (Bandit/Semgrep flag it: Bandit) — a bare `requests.get(var)` is kept **Low** on purpose: gating it would false-positive on legitimate dynamic-URL code (see the benign `verify_true` sample). That deliberate restraint is why Q-Trace holds 0% FP while Bandit sits at 6%. Real SSRF is escalated when taint confirms attacker-controlled input.

> **Semantic precision, not just a flag.** On `cred_exfil_direct` Bandit does emit a finding — but it is *B113: requests call without a timeout*, not credential exfiltration. Firing on the wrong reason is how teams learn to ignore a scanner. Q-Trace names the actual data-flow: `os.environ → requests.post`.

