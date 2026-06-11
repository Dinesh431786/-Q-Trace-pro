"""
main.py — Q-Trace Pro: The Private Quantum Auditor (Streamlit entry point)
=========================================================================
Local-native, air-gapped source-code security auditor. Combines:

  * a sink-aware taint/pattern detection core (low false positives),
  * a lightweight pure-NumPy quantum-inspired risk engine (no cirq),
  * Z3 symbolic reachability proofs,
  * a self-healing resilience layer (engines degrade, never crash),
  * industry-standard SARIF 2.1.0 + CWE/CVSS reporting.

Run with:  streamlit run main.py
"""
from __future__ import annotations

import time

import streamlit as st

from analyzer import analyze, clear_cache
from findings import SEVERITY_TO_CVSS
from report import json_report_string, sarif_string
from self_healing import ValidationError, health

# Optional engines (UI degrades gracefully if missing).
try:
    from quantum_engine import (circuit_to_text, format_score, map_to_unitary,
                                 run_quantum_analysis, visualize_quantum_state)
    _QUANTUM = True
except Exception:
    _QUANTUM = False

try:
    from gemini_explainer import explain_result
    _EXPLAIN = True
except Exception:
    _EXPLAIN = False

try:
    from rust_wrapper import is_rust_active
except Exception:
    def is_rust_active():
        return False

PATTERN_ARGS = {
    "PROBABILISTIC_BOMB": {"prob": 0.22},
    "ENTANGLED_BOMB": {"probs": [0.19, 0.71]},
    "CHAINED_QUANTUM_BOMB": {"chain_length": 3, "prob": 0.14},
    "QUANTUM_STEGANOGRAPHY": {"encode_val": 1},
    "QUANTUM_ANTIDEBUG": {"prob": 0.08},
    "CROSS_FUNCTION_QUANTUM_BOMB": {"func_probs": [0.31, 0.47, 0.99]},
}

DEFAULT_CODE = """import random, os

def rare_bomb():
    if random.random() < 0.22:
        os.system("shutdown -h now")
        grant_root_access()
"""

SEV_COLOR = {
    "Critical": "#7d0a0a", "High": "#e74c3c",
    "Medium": "#f1c40f", "Low": "#2ecc71", "Info": "#3498db",
}


st.set_page_config(page_title="Q-Trace Pro — Private Quantum Auditor", layout="wide")
st.title("⚛️ Q-Trace Pro — The Private Quantum Auditor")
st.markdown(
    "**Local-Native · Air-Gapped · Symbolic Proofs · Self-Healing · SARIF/CWE**  \n"
    "Detects logic bombs, covert channels and anti-analysis backdoors with a "
    "sink-aware engine that keeps false positives low — running entirely on your "
    "own hardware."
)

# --- Sidebar controls ---------------------------------------------------- #
with st.sidebar:
    st.subheader("Auditor Controls")
    use_symbolic = st.checkbox("Symbolic Verification (Z3)", value=True)
    use_cache = st.checkbox("Content-hash cache (faster)", value=True)
    show_quantum = st.checkbox("Show quantum circuit details", value=True)
    st.markdown("---")
    rust_status = "✅ Active" if is_rust_active() else "⚠️ Python fallback"
    st.caption(f"**Rust Core:** {rust_status}")
    if st.button("🔄 Reset / clear cache"):
        clear_cache()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


uploaded = st.file_uploader("Upload a Python file", type=["py"])
file_code = DEFAULT_CODE
if uploaded is not None:
    try:
        file_code = uploaded.read().decode("utf-8", errors="ignore")
    except Exception:
        st.error("Could not decode uploaded file; using default sample.")

code_input = st.text_area("Paste Python code to audit:", height=240, value=file_code)

run_clicked = st.button("⚡ Perform Local Quantum Audit", type="primary")


# --- Run analysis -------------------------------------------------------- #
if run_clicked:
    try:
        with st.spinner("Auditing locally…"):
            result = analyze(code_input, use_symbolic=use_symbolic, use_cache=use_cache)
        st.session_state["result"] = result
        st.session_state["code"] = code_input
    except ValidationError as e:
        st.error(f"Input rejected: {e}")
    except Exception as e:  # last-resort guard — should not happen
        st.error(f"Unexpected error (audit aborted safely): {e}")


result = st.session_state.get("result")
code = st.session_state.get("code", code_input)

if result is not None:
    findings = result.findings

    # --- Executive summary ---
    st.subheader("🛡️ Audit Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Findings", len(findings))
    c2.metric("Max CVSS", f"{max((f.cvss for f in findings), default=0.0):.1f}")
    c3.metric("AST Entropy", f"{result.ast_entropy:.2f}")
    audit_ms = result.duration_s * 1000
    c4.metric("Audit Time", f"{audit_ms:.0f} ms" + (" (cached)" if result.cache_hit else ""))

    if result.symbolic:
        msg, unsafe = result.symbolic
        st.markdown(f"**Symbolic Proof:** :{'red' if unsafe else 'green'}[{msg}]")

    # --- Self-healing health panel ---
    with st.expander("🩺 Engine Health (Self-Healing Status)", expanded=False):
        for h in result.health:
            st.write(f"{h['emoji']} **{h['name']}** — {h['state']}"
                     + (f" · {h['detail']}" if h['detail'] else "")
                     + (f" · {h['failures']} failure(s)" if h['failures'] else ""))
        overall = health.overall().value
        st.caption(f"Overall system state: **{overall}**")
        if st.button("🔧 Attempt self-heal"):
            healed = health.self_heal()
            st.write("Self-heal results:", healed or "nothing to heal")

    # --- Findings table ---
    if findings:
        st.subheader("🚨 Findings (severity × confidence, CWE-mapped)")
        for f in findings:
            color = SEV_COLOR.get(f.severity, "#888")
            st.markdown(
                f"<div style='border-left:6px solid {color};padding:6px 12px;margin:6px 0;"
                f"background:rgba(127,127,127,0.08)'>"
                f"<b>{f.meta.title}</b> &nbsp;·&nbsp; "
                f"<span style='color:{color}'><b>{f.severity}</b></span> "
                f"(CVSS {f.cvss}) &nbsp;·&nbsp; confidence <b>{f.confidence}</b> "
                f"&nbsp;·&nbsp; <a href='{f.meta.cwe_uri()}' target='_blank'>{f.meta.cwe}</a> "
                f"&nbsp;·&nbsp; line {f.line}<br>"
                f"<small>{f.meta.description}</small><br>"
                f"<small>💡 <i>{f.meta.remediation}</i></small>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ No malicious-logic patterns detected with actionable confidence.")

    # --- Reports (SARIF / JSON) — the float32 crash is fixed at the source ---
    st.subheader("📤 Export Reports (Industry Standard)")
    rc1, rc2 = st.columns(2)
    extra = {
        "symbolic_proof": result.symbolic[0] if result.symbolic else "N/A",
        "ast_entropy": round(result.ast_entropy, 4),
        "physics_metrics": result.physics_metrics,
        "engine_health": result.health,
    }
    rc1.download_button(
        "⬇️ SARIF 2.1.0 (GitHub/DefectDojo)",
        data=sarif_string(findings),
        file_name="qtrace_audit.sarif",
        mime="application/json",
    )
    rc2.download_button(
        "⬇️ JSON Audit Report",
        data=json_report_string(findings, extra=extra),
        file_name="qtrace_audit.json",
        mime="application/json",
    )

    # --- Physics dashboard ---
    if result.physics_metrics:
        with st.expander("⚛️ Physics-Informed Security Dashboard"):
            import numpy as np
            p = result.physics_metrics
            pc = st.columns(3)
            pc[0].metric("Logic Temperature (Landauer)",
                         f"{np.mean([m['landauer_ratio'] for m in p]):.3f}",
                         help="High = possible hidden data exfiltration")
            pc[1].metric("Quantum Discord",
                         f"{np.mean([m['quantum_discord'] for m in p]):.3f}",
                         help="Non-classical correlation = obfuscation")
            pc[2].metric("Least-Action Deviation",
                         f"{np.mean([m['action_hamiltonian'] for m in p]):.3f}",
                         help="Deviation from optimal path = backdoor")

    # --- Sinks ---
    if result.sinks:
        with st.expander("🎯 Dangerous Sinks (with line numbers)"):
            for s in result.sinks:
                tag = "🔴 guarded trigger" if s.in_guarded_branch else "🟠 direct"
                st.write(f"{tag} — `{s.name}` at line {s.line}")

    # --- Quantum circuit details + AI explanation ---
    if show_quantum and _QUANTUM and result.patterns:
        with st.expander("⚛️ Formal Verification & Quantum Entropy"):
            for pattern in result.patterns:
                circuit = map_to_unitary(pattern, **PATTERN_ARGS.get(pattern, {}))
                if not circuit:
                    continue
                score, _, _, _ = run_quantum_analysis(circuit, pattern)
                pct, label = format_score(score)
                st.markdown(f"### `{pattern}`")
                st.metric("Von Neumann Entropy Risk", pct, label)
                st.code(circuit_to_text(circuit))
                img = visualize_quantum_state(circuit, f"Quantum State ({pattern})")
                if img is not None:
                    st.image(img, width=360)
                if _EXPLAIN:
                    try:
                        st.info(explain_result(score, pattern, code))
                    except Exception:
                        pass

st.markdown("---")
st.caption("Q-Trace Pro · Lightweight NumPy quantum core · Z3 · scikit-learn · "
           "Self-healing · SARIF 2.1.0 / CWE · (c) 2026 — The Private Quantum Auditor")
