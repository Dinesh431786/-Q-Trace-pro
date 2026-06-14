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
