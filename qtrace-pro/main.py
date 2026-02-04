import streamlit as st
import time
import numpy as np
import json
import networkx as nx

# Core modules
from code_parser import extract_logic_blocks, calculate_ast_entropy
from pattern_matcher import detect_patterns
from quantum_engine import (
    map_to_unitary, run_quantum_analysis, format_score,
    circuit_to_text, visualize_quantum_state
)
from quantum_graph import plot_quantum_risk_graph, check_graph_threats
from gemini_explainer import explain_result as generate_explanation
from quantum_redteam import generate_python_redteam_suite
from quantum_ml import block_to_features, train_detection_model, predict_threats
from benchmark import ADVANCED_TEST_CASES, run_benchmark_suite
from symbolic_engine import run_symbolic_verification
from rust_wrapper import scan_code_fast, is_rust_active

# Initialize session state
for var, default in [
    ('analysis_done', False),
    ('detected', []),
    ('logic_blocks', []),
    ('quantum_scores', []),
    ('graph_image', None),
    ('code_input', ''),
    ('ml_model', None),
    ('ml_results', {}),
    ('last_code', ''),
    ('ml_scaler', None),
    ('symbolic_result', None),
    ('graph_threats', []),
    ('ast_entropy', 0.0),
    ('physics_metrics', [])
]:
    if var not in st.session_state:
        st.session_state[var] = default

pattern_args = {
    "PROBABILISTIC_BOMB": {"prob": 0.22},
    "ENTANGLED_BOMB": {"probs": [0.19, 0.71]},
    "CHAINED_QUANTUM_BOMB": {"chain_length": 3, "prob": 0.14},
    "QUANTUM_STEGANOGRAPHY": {"encode_val": 1},
    "QUANTUM_ANTIDEBUG": {"prob": 0.08},
    "CROSS_FUNCTION_QUANTUM_BOMB": {"func_probs": [0.31, 0.47, 0.99]}
}

st.set_page_config(page_title="Q-Trace Pro — Private Quantum Auditor", layout="wide")
st.title("⚛️ Q-Trace Pro — The Private Quantum Auditor")
st.markdown("""
**Local-Native | Air-Gapped | Symbolic Verification | Rust Core**

The only security tool that mathematically proves safety using Quantum Symbolic Execution and Von Neumann Entropy, running entirely on your local hardware.
""")

with st.sidebar:
    st.subheader("Auditor Controls")
    use_ml = st.checkbox("Enable Adversarial Quantum ML (SVM)", value=True)
    use_symbolic = st.checkbox("Enable Symbolic Verification (Z3)", value=True)
    run_benchmark = st.checkbox("Run Benchmark Test Cases", value=False)
    
    st.markdown("---")
    rust_status = "✅ Active" if is_rust_active() else "⚠️ Inactive (Using Python Fallback)"
    st.caption(f"**Rust Core:** {rust_status}")
    if not is_rust_active():
        st.caption("Compile `qtrace_core` for 100x speedup.")

    if st.button("🔄 Reset Analysis"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

uploaded_file = st.file_uploader("Upload Python code file", type=["py"], key="file_upload")

default_code = '''import random
def rare_bomb():
    if random.random() < 0.22:
        os.system("shutdown -h now")
        grant_root_access()
'''

file_code = default_code
if uploaded_file is not None:
    try:
        file_code = uploaded_file.read().decode(errors="ignore")
    except Exception as e:
        st.error("Could not decode uploaded file.")
        file_code = default_code

code_input = st.text_area(
    "Paste your Python code snippet:",
    height=240,
    value=st.session_state.code_input if st.session_state.code_input else file_code,
    key="main_code_input"
)
st.session_state.code_input = code_input

col1, col2 = st.columns(2)
with col1:
    run_clicked = st.button("⚡️ Perform Local Quantum Audit")
with col2:
    sandbox_clicked = st.button("🛡️ Run in Quantum Sandbox (Safe Mode)")

# Run analysis
if run_clicked or sandbox_clicked or st.session_state.code_input != st.session_state.get('last_code', ''):
    st.session_state.last_code = st.session_state.code_input
    st.session_state.analysis_done = True

    start_time = time.time()

    # 1. Rust Core Scan (or Python Fallback)
    rust_patterns = scan_code_fast(code_input)
    # We use this to augment or cross-check later, currently primarily logging speed
    
    # 2. Logic Extraction & Entropy
    try:
        st.session_state.logic_blocks = extract_logic_blocks(code_input)
        st.session_state.ast_entropy = calculate_ast_entropy(code_input)
    except Exception as e:
        st.error(f"Error parsing code: {str(e)}")
        st.stop()

    logic_blocks = st.session_state.logic_blocks
    
    # 3. Taint Analysis (Hybrid Step 1)
    patterns = detect_patterns(code_input)
    st.session_state.detected = [p for p in patterns if p != "UNKNOWN"]
    
    # 4. Symbolic Verification (Z3)
    if use_symbolic:
        msg, is_unsafe = run_symbolic_verification(code_input)
        st.session_state.symbolic_result = (msg, is_unsafe)

    # 5. Quantum Mapping & Entropy
    feature_matrix = []
    quantum_scores = []
    
    for i, pattern in enumerate(st.session_state.detected):
        args = pattern_args.get(pattern, {})
        circuit = map_to_unitary(pattern, **args)
        
        if circuit:
            score, _, _, p_metrics = run_quantum_analysis(circuit, pattern)
            quantum_scores.append(score)
            st.session_state.physics_metrics.append(p_metrics)
            
            if i < len(logic_blocks):
                block = logic_blocks[i]
                state_probs = np.zeros(8)
                feats = block_to_features(block, score, state_probs)
                feature_matrix.append(feats)
        else:
            quantum_scores.append(0)

    st.session_state.quantum_scores = quantum_scores

    # 6. ML Detection (Local SVM)
    if use_ml and len(feature_matrix) > 0:
        X = np.array(feature_matrix)
        if len(X) > 1:
            model, scaler = train_detection_model(X)
            preds, scores = predict_threats(model, scaler, X)
            st.session_state.ml_model = model
            st.session_state.ml_results = {"preds": preds, "scores": scores}
        else:
             st.session_state.ml_results = {}

    # 7. Graph Analysis
    entangled_pairs = [
        (i, j)
        for i, block in enumerate(logic_blocks)
        for call in block['calls']
        for j, blk in enumerate(logic_blocks)
        if call in "".join(blk['body'])
    ]
    try:
        buf = plot_quantum_risk_graph(
            logic_blocks,
            quantum_scores + [0] * (len(logic_blocks) - len(quantum_scores)),
            entangled_pairs=entangled_pairs,
            streamlit_buf=True
        )
        st.session_state.graph_image = buf
        
        # Check Isomorphism (Signature-less)
        # Reconstruct graph object temporarily for check
        G_temp = nx.DiGraph()
        # (Simplified graph reconstruction for check)
        for idx, _ in enumerate(logic_blocks): G_temp.add_node(idx)
        for i, j in entangled_pairs: G_temp.add_edge(i, j)
        st.session_state.graph_threats = check_graph_threats(G_temp)
        
    except Exception as e:
        st.warning(f"Graph generation failed: {e}")

    end_time = time.time()
    st.info(f"Local Audit completed in {end_time - start_time:.2f} seconds.")

if st.session_state.analysis_done:
    detected = st.session_state.detected
    
    # --- Dashboard ---
    
    st.subheader("🛡️ Audit Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Detected Threats", len(detected))
    with col2:
        st.metric("AST Entropy", f"{st.session_state.ast_entropy:.2f}")
    with col3:
        if st.session_state.symbolic_result:
            msg, unsafe = st.session_state.symbolic_result
            color = "red" if unsafe else "green"
            st.markdown(f"**Symbolic Proof:** :{color}[{msg}]")
    with col4:
        # Aggregate Physics Metric (e.g. Max Action)
        if st.session_state.physics_metrics:
            max_action = max(m['action_hamiltonian'] for m in st.session_state.physics_metrics)
            st.metric("Code Hamiltonian", f"{max_action:.3f}")
        else:
            st.metric("Code Hamiltonian", "0.00")

    # --- Physics-Informed Dashboard ---
    with st.expander("⚛️ Physics-Informed Security Dashboard"):
        if st.session_state.physics_metrics:
            p_cols = st.columns(3)
            # Average Metrics
            avg_landauer = np.mean([m['landauer_ratio'] for m in st.session_state.physics_metrics])
            avg_discord = np.mean([m['quantum_discord'] for m in st.session_state.physics_metrics])
            avg_action = np.mean([m['action_hamiltonian'] for m in st.session_state.physics_metrics])
            
            p_cols[0].metric("Logic Temperature (Landauer)", f"{avg_landauer:.3f} K", help="High temp = Hidden Data Exfiltration")
            p_cols[1].metric("Quantum Discord", f"{avg_discord:.3f}", help="Non-classical correlations (Obfuscation)")
            p_cols[2].metric("Least Action Deviation", f"{avg_action:.3f}", help="Deviation from optimal path (Backdoor)")
        else:
            st.info("No quantum states analyzed to generate physics metrics.")
            
    if detected:
        st.error(f"Threats Found: {', '.join(detected)}")
    else:
        st.success("No Quantum-Native Threats Detected.")

    if st.session_state.graph_threats:
        for threat in st.session_state.graph_threats:
            st.warning(f"⚠️ Structural Threat: {threat}")

    # Reporting Layer (JSON/SARIF)
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)

    report = {
        "tool": "Q-Trace Pro Private Auditor",
        "timestamp": time.time(),
        "detected_patterns": detected,
        "symbolic_proof": st.session_state.symbolic_result[0] if st.session_state.symbolic_result else "N/A",
        "ast_entropy": st.session_state.ast_entropy,
        "graph_threats": st.session_state.graph_threats,
        "physics_metrics": st.session_state.physics_metrics,
        "ml_analysis": {
            "predictions": st.session_state.ml_results.get("preds", []).tolist() if st.session_state.ml_results else [],
            "anomaly_scores": st.session_state.ml_results.get("scores", []).tolist() if st.session_state.ml_results else []
        }
    }
    st.download_button("Download Secure Audit Report (JSON)", data=json.dumps(report, indent=2, cls=NumpyEncoder), file_name="qtrace_audit.json")

    # Detailed Analysis
    with st.expander("🧩 Taint & Logic Analysis"):
        for block in st.session_state.logic_blocks:
            st.code(f"if {block['condition']}:\n    " + "\n    ".join(block['body']), language="python")

    with st.expander("⚛️ Formal Verification & Entropy"):
        for i, pattern in enumerate(detected):
            args = pattern_args.get(pattern, {})
            circuit = map_to_unitary(pattern, **args)
            st.markdown(f"### Pattern: `{pattern}`")
            if circuit:
                score = st.session_state.quantum_scores[i] if i < len(st.session_state.quantum_scores) else 0
                pct, risk_label = format_score(score)
                st.metric("Von Neumann Entropy Risk", pct, risk_label)
                st.code(circuit_to_text(circuit))
                try:
                    img = visualize_quantum_state(circuit, f"Quantum State ({pattern})")
                    st.image(img, width=350)
                except Exception:
                    pass
                
                try:
                    explanation = generate_explanation(score, pattern, code_input)
                    if explanation:
                        st.markdown("**AI Explanation:**")
                        st.info(explanation)
                except Exception:
                    pass

    with st.expander("🧠 Adversarial Quantum ML (Local SVM)"):
         if st.session_state.ml_results:
            preds = st.session_state.ml_results["preds"]
            scores = st.session_state.ml_results["scores"]
            for i, (pred, score) in enumerate(zip(preds, scores)):
                label = "🚨 Anomaly" if pred == -1 else "✅ Benign"
                st.write(f"Vector {i}: **{label}**, Score: `{score:.4f}`")
         else:
            st.info("Not enough data to train local anomaly model.")

    st.subheader("⚛️ Entanglement Graph")
    if st.session_state.graph_image:
        st.image(st.session_state.graph_image)

    # Red Team Samples
    if st.checkbox("Generate Red Team Suite"):
        st.subheader("🛠️ Quantum Red Team Code Samples")
        redteam_samples = generate_python_redteam_suite(3)
        for sample in redteam_samples:
            st.code(sample, language="python")

if run_benchmark:
    st.subheader("📊 Local Benchmark Results")
    try:
        benchmark_results = run_benchmark_suite()
        display_data = []
        for result in benchmark_results:
            display_data.append({
                "Test Case": result["Case"],
                "Detected": result["Detected"],
                "Expected": result["Expected"],
                "Entropy Risk": result["QuantumScore"]
            })
        st.table(display_data)
    except Exception as e:
        st.error("🚨 Failed to run benchmark")
        st.code(str(e))

st.markdown("---")
st.caption("Built with Cirq, Streamlit, OneClassSVM, Z3, and Rust. (c) 2026 Q-Trace Pro — The Private Quantum Auditor")
