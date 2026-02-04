# benchmark.py — ADVANCED QUANTUM ONLY

import csv
from code_parser import extract_logic_blocks
from pattern_matcher import detect_patterns
from quantum_engine import map_to_unitary, run_quantum_analysis, format_score

ADVANCED_TEST_CASES = [
    {
        "name": "Probabilistic Bomb (Python)",
        "language": "python",
        "code": "if random.random() < 0.14:\n    os.system('rm -rf /')",
        "pattern": "PROBABILISTIC_BOMB"
    },
    {
        "name": "Entangled Bomb (Python, chained calls)",
        "language": "python",
        "code": """
def a(x): return random.random() < 0.22
def b(y): return a(y) and (random.randint(1,5)==3)
if b(user): os.system('shutdown -h now')
""",
        "pattern": "ENTANGLED_BOMB"
    },
    {
        "name": "Chained Bomb (C style) - regex fallback only",
        "language": "python",  # Force python for advanced mode (no tree-sitter)
        "code": """
k = 0
if (random.randint(0,7) == 3): k += 1
if (random.randint(0,11) == 5): k += 1
if k == 2: os.system('shutdown -h now')
""",
        "pattern": "CHAINED_QUANTUM_BOMB"
    },
    {
        "name": "Cross-function Quantum Bomb (Python)",
        "language": "python",
        "code": """
def q1(x): return random.random() < 0.27
def q2(y): return q1(y) and (random.random() < 0.13)
if q2(user): os.system('shutdown -h now')
""",
        "pattern": "CROSS_FUNCTION_QUANTUM_BOMB"
    },
    {
        "name": "Quantum Stego (Python)",
        "language": "python",
        "code": """
def qstego(msg): return ''.join([chr(ord(c)^0x2A) for c in msg])
if qstego(secret) == trigger: unlock_root()
""",
        "pattern": "QUANTUM_STEGANOGRAPHY"
    },
    {
        "name": "Quantum Anti-Debug (Python)",
        "language": "python",
        "code": """
if random.random() < 0.09:
    import time
    time.sleep(99999)
    print("anti-debug triggered")
""",
        "pattern": "QUANTUM_ANTIDEBUG"
    }
]

def run_benchmark_suite(output_csv="benchmark_results.csv"):
    rows = []
    print("QUANTUM Pattern Detection Benchmark:\n")

    for test in ADVANCED_TEST_CASES:
        # Taint-based pattern matcher now requires raw code input
        patterns = detect_patterns(test["code"])
        detected = [p for p in patterns if p != "UNKNOWN"]
        expected_pattern = test["pattern"]

        # Format quantum score if matched
        quantum_score = "N/A"
        risk_label = ""
        if expected_pattern in detected:
            try:
                circuit = map_to_unitary(expected_pattern)
                score, _, _, _ = run_quantum_analysis(circuit, expected_pattern)
                pct, risk_label = format_score(score)
                quantum_score = f"{pct} ({risk_label})"
            except Exception as e:
                quantum_score = "Error"

        row = {
            "Case": test["name"],
            "Detected": ", ".join(detected) if detected else "UNKNOWN",
            "Expected": expected_pattern,
            "QuantumScore": quantum_score
        }

        print(f"Test: {row['Case']}")
        print(f"  - Detected: {row['Detected']}")
        print(f"  - Expected: {row['Expected']}")
        print(f"  - Quantum Risk: {row['QuantumScore']}\n")
        rows.append(row)

    # Save results to CSV
    try:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Benchmark completed. Results saved to '{output_csv}'")
    except Exception as e:
        print(f"[ERROR] Failed to write benchmark results: {e}")

    return rows


# --- Run Benchmark Locally ---
if __name__ == "__main__":
    benchmark_data = run_benchmark_suite()
