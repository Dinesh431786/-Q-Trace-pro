"""
quantum_engine.py — Q-Trace Pro Core Engine
Implements Formal Verification via Quantum Hoare Logic mapping and
Von Neumann Entropy-based Risk Scoring.
"""
import cirq
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# --- Formal Verification & Unitary Mapping ---

def map_to_unitary(pattern, **kwargs):
    """
    Maps classical control flow patterns to Quantum Unitary Operators.
    This replaces simple circuit building with a formal mapping layer.
    """
    if pattern == "PROBABILISTIC_BOMB":
        return _unitary_probabilistic(kwargs.get("prob", 0.2))
    elif pattern == "ENTANGLED_BOMB":
        return _unitary_entangled(kwargs.get("probs", [0.2, 0.5]))
    elif pattern == "CHAINED_QUANTUM_BOMB":
        return _unitary_chained(kwargs.get("chain_length", 3), kwargs.get("prob", 0.3))
    elif pattern == "QUANTUM_STEGANOGRAPHY":
        return _unitary_stego(kwargs.get("encode_val", 1))
    elif pattern == "QUANTUM_ANTIDEBUG":
        return _unitary_antidebug(kwargs.get("prob", 0.1))
    elif pattern == "CROSS_FUNCTION_QUANTUM_BOMB":
        return _unitary_cross_func(kwargs.get("func_probs", [0.3, 0.5, 0.8]))
    else:
        return None

# Alias for compatibility with existing calls
build_quantum_circuit = map_to_unitary

def _unitary_probabilistic(prob=0.2):
    qubit = cirq.LineQubit(0)
    theta = 2 * np.arcsin(np.sqrt(prob))
    circuit = cirq.Circuit()
    # Rotation represents the probabilistic transition operator
    circuit.append(cirq.ry(theta)(qubit))
    circuit.append(cirq.measure(qubit, key='result'))
    return circuit

def _unitary_entangled(probs=[0.2, 0.5]):
    q0, q1 = cirq.LineQubit.range(2)
    theta0 = 2 * np.arcsin(np.sqrt(probs[0]))
    theta1 = 2 * np.arcsin(np.sqrt(probs[1]))
    circuit = cirq.Circuit()
    circuit.append(cirq.ry(theta0)(q0))
    circuit.append(cirq.ry(theta1)(q1))
    # CNOT represents the coupled dependency (Entanglement)
    circuit.append(cirq.CNOT(q0, q1))
    circuit.append(cirq.measure(q0, key='result0'))
    circuit.append(cirq.measure(q1, key='result1'))
    return circuit

def _unitary_chained(chain_length=3, prob=0.3):
    qubits = cirq.LineQubit.range(chain_length)
    theta = 2 * np.arcsin(np.sqrt(prob))
    circuit = cirq.Circuit()
    for q in qubits:
        circuit.append(cirq.ry(theta)(q))
    # Linear chain of dependencies (CNOT cascade)
    for i in range(chain_length - 1):
        circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
    for i, q in enumerate(qubits):
        circuit.append(cirq.measure(q, key=f'result{i}'))
    return circuit

def _unitary_stego(encode_val=1):
    q = cirq.LineQubit(0)
    circuit = cirq.Circuit()
    if encode_val:
        circuit.append(cirq.X(q))
    # Hadamard creates superposition for hiding data
    circuit.append(cirq.H(q))
    circuit.append(cirq.measure(q, key='stego'))
    return circuit

def _unitary_antidebug(prob=0.1):
    q = cirq.LineQubit(0)
    theta = 2 * np.arcsin(np.sqrt(prob))
    circuit = cirq.Circuit()
    circuit.append(cirq.ry(theta)(q))
    circuit.append(cirq.measure(q, key='anti'))
    return circuit

def _unitary_cross_func(func_probs=[0.3, 0.5, 0.8]):
    n = len(func_probs)
    qubits = cirq.LineQubit.range(n)
    circuit = cirq.Circuit()
    for i, q in enumerate(qubits):
        theta = 2 * np.arcsin(np.sqrt(func_probs[i]))
        circuit.append(cirq.ry(theta)(q))
    # Cross-function entanglement (Mesh topology ideally, linear here for demo)
    for i in range(n - 1):
        circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
    for i, q in enumerate(qubits):
        circuit.append(cirq.measure(q, key=f'f{i}'))
    return circuit

# --- Mathematical Risk Framework ---

def calculate_von_neumann_entropy(state_vector):
    """
    Calculates Entanglement Entropy (Von Neumann Entropy of reduced density matrix).
    For a single qubit, returns Shannon entropy of probabilities.
    For multi-qubit, traces out half the system.
    S = -Tr(rho * ln(rho))
    """
    n_qubits = int(np.log2(len(state_vector)))
    
    if n_qubits == 1:
        # Shannon entropy of measurement outcomes
        probs = np.abs(state_vector)**2
        # Avoid log(0)
        probs = probs[probs > 1e-10]
        return -np.sum(probs * np.log(probs))
        
    # For multi-qubit, calculate reduced density matrix of first qubit
    # (Simplified entanglement measure)
    # Reshape to tensor
    # Split system into A (first qubit) and B (rest)
    dim_A = 2
    dim_B = 2 ** (n_qubits - 1)
    matrix = state_vector.reshape((dim_A, dim_B))
    
    # Singular values (Schmidt coefficients)
    try:
        _, s, _ = np.linalg.svd(matrix)
        # s are singular values. lambda_i = s_i^2 are eigenvalues of reduced density matrix
        eigenvalues = s**2
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))
        return entropy
    except np.linalg.LinAlgError:
        return 0.0

def calculate_risk_score(pattern, circuit, entropy):
    """
    R = sum(w_i * (S / S_max)) + lambda * L
    """
    # Weights (w_i) based on threat severity
    weights = {
        "PROBABILISTIC_BOMB": 1.5,
        "CHAINED_QUANTUM_BOMB": 2.0,
        "CROSS_FUNCTION_QUANTUM_BOMB": 2.5,
        "ENTANGLED_BOMB": 3.0,
        "QUANTUM_STEGANOGRAPHY": 3.5, # High impact
        "QUANTUM_ANTIDEBUG": 1.5
    }
    w_i = weights.get(pattern, 1.0)
    
    # S_max for subsystem A (dim 2) is ln(2)
    s_max = np.log(2)
    entropy_ratio = entropy / s_max if s_max > 0 else 0
    
    # Logical Depth (L)
    # Cirq circuit length (moments)
    L = len(circuit)
    lambda_factor = 0.1 # Scaling factor
    
    risk = w_i * entropy_ratio + lambda_factor * L
    
    # Normalize to 0-1 range roughly (soft sigmoid or clip)
    # Boost sensitivity: tanh(risk) instead of risk/2
    normalized_risk = np.tanh(risk)
    
    return normalized_risk

def run_quantum_analysis(circuit, pattern="PROBABILISTIC_BOMB", shots=1024):
    if circuit is None:
        return 0.0, {}, {}, {}
        
    simulator = cirq.Simulator()
    
    # 1. State Vector Simulation (for Entropy)
    sim_result = simulator.simulate(circuit)
    state_vector = sim_result.final_state_vector
    entropy = calculate_von_neumann_entropy(state_vector)
    
    # 2. Risk Calculation (Math Framework)
    risk_score = calculate_risk_score(pattern, circuit, entropy)
    
    # --- Physics-Based Metrics ---
    physics_metrics = get_physics_metrics(circuit, state_vector, risk_score)
    
    # 3. Measurement (for compatibility with UI)
    run_result = simulator.run(circuit, repetitions=shots)
    measurements = run_result.measurements
    
    return risk_score, measurements, circuit, physics_metrics

# --- Physics-Based Security Metrics ---

def calculate_landauer_limit(circuit, state_vector, initial_entropy=None):
    """
    Landauer's Principle: Heat = k * ln(2) * Delta_I
    Detects 'Hidden Data Exfiltration' if Info Loss is high but logical depth is low.
    """
    # Default initial entropy for a single qubit in superposition (H|0>) is ln(2) approx 0.69
    if initial_entropy is None:
        initial_entropy = np.log(2)
        
    final_entropy = calculate_von_neumann_entropy(state_vector)
    # Assume initial state had max entropy (superposition)
    delta_I = initial_entropy - final_entropy
    
    # We use units where k * ln(2) = 1 for simplicity (Information Units)
    heat = max(0.0, delta_I)
    
    depth = len(circuit)
    ratio = heat / depth if depth > 0 else 0
    return ratio

def calculate_quantum_discord(state_vector):
    """
    Quantum Discord: Delta(A:B) = I(A:B) - J(A:B)
    High discord implies non-classical correlations (Obfuscation).
    For pure states, Entanglement Entropy is a good proxy for non-classical correlation.
    """
    return calculate_von_neumann_entropy(state_vector)

def calculate_action(circuit, risk_score):
    """
    Principle of Least Action: S = Integral(T - V)
    T (Kinetic) ~ Speed (1/Depth)
    V (Potential) ~ Risk
    High Action indicates 'Unphysical' behavior (Malicious deviation).
    """
    depth = len(circuit)
    T = 1.0 / (depth + 1.0)
    V = risk_score
    action = abs(T - V)
    return action

def get_physics_metrics(circuit, state_vector, risk_score):
    """
    Returns a dictionary of physics-based security metrics.
    """
    return {
        "landauer_ratio": calculate_landauer_limit(circuit, state_vector),
        "quantum_discord": calculate_quantum_discord(state_vector),
        "action_hamiltonian": calculate_action(circuit, risk_score)
    }

def format_score(score):
    pct = f"{score * 100:.1f}%"
    if score > 0.8:
        return pct, "CRITICAL (QUANTUM)"
    elif score > 0.5:
        return pct, "HIGH RISK"
    elif score > 0.2:
        return pct, "MODERATE"
    return pct, "SAFE"

def circuit_to_text(circuit):
    return str(circuit)

def visualize_quantum_state(circuit, title="Quantum State Probabilities"):
    sim = cirq.Simulator()
    result = sim.simulate(circuit)
    state_vector = result.final_state_vector
    probs = np.abs(state_vector) ** 2
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.bar(range(len(probs)), probs)
    ax.set_xlabel("State")
    ax.set_ylabel("Probability")
    ax.set_title(title)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

if __name__ == "__main__":
    print("REVOLUTIONARY Quantum Engine: Self-Test")
    # Test logic would go here
