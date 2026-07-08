"""Collect ALL real measurements for the research paper figures -> paper_data.json.
No number in the paper is hand-written; every figure reads from this file."""
import json, os, sys, time
sys.path.insert(0, "/home/user/-Q-Trace-pro/qtrace-pro")
os.chdir("/home/user/-Q-Trace-pro/qtrace-pro")

from benchmark import MALICIOUS, BENIGN, findings_for, is_ci_alert
from tool_comparison import compare
from analyzer import analyze, clear_cache

SEV_RANK = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}
CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}

def max_finding(fs):
    """Return (severity, confidence) of the highest (severity, confidence) finding."""
    if not fs:
        return ("None", "None")
    best = max(fs, key=lambda f: (SEV_RANK.get(f.severity, 0), CONF_RANK.get(f.confidence, 0)))
    return (best.severity, best.confidence)

data = {}

# ---- 1. Q-Trace headline (recall / FP / precision / F1 / confusion) ----------
tp = fn = fp = tn = cat_hits = 0
mal_latency = []
conf_grid = {}   # (severity, confidence) -> {"mal": n, "ben": n}
sev_only_fp = 0  # ablation: FP if gated on severity alone (no confidence axis)
sev_only_recall = 0
per_sample = []

clear_cache()
for name, kind, payload, expected, *rest in MALICIOUS:
    t0 = time.perf_counter()
    fs = findings_for(kind, payload)
    dt = (time.perf_counter() - t0) * 1000.0
    if kind == "code":
        mal_latency.append(dt)
    cats = {f.pattern for f in fs}
    caught = expected in cats
    cat_hits += caught
    alert = is_ci_alert(fs)
    tp += alert; fn += (not alert)
    sev = any(f.severity in ("Critical", "High") for f in fs)
    sev_only_recall += sev
    sv, cf = max_finding(fs)
    conf_grid.setdefault((sv, cf), {"mal": 0, "ben": 0})[sv, cf] if False else None
    key = f"{sv}|{cf}"
    conf_grid.setdefault(key, {"mal": 0, "ben": 0})["mal"] += 1
    per_sample.append({"name": name, "cls": "malicious", "expected": expected,
                       "caught": bool(caught), "alert": bool(alert),
                       "severity": sv, "confidence": cf})

clear_cache()
for name, kind, payload in BENIGN:
    fs = findings_for(kind, payload)
    alert = is_ci_alert(fs)
    fp += alert; tn += (not alert)
    sev = any(f.severity in ("Critical", "High") for f in fs)
    sev_only_fp += sev
    sv, cf = max_finding(fs)
    key = f"{sv}|{cf}"
    conf_grid.setdefault(key, {"mal": 0, "ben": 0})["ben"] += 1
    per_sample.append({"name": name, "cls": "benign", "expected": "-",
                       "caught": bool(not alert), "alert": bool(alert),
                       "severity": sv, "confidence": cf})

nmal, nben = len(MALICIOUS), len(BENIGN)
precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

data["headline"] = {
    "n_malicious": nmal, "n_benign": nben,
    "category_recall": cat_hits / nmal, "category_hits": cat_hits,
    "ci_recall": recall, "fp_rate": fp / nben,
    "precision": precision, "f1": f1,
    "tp": tp, "fn": fn, "fp": fp, "tn": tn,
    "mean_latency_ms": sum(mal_latency) / len(mal_latency),
    "median_latency_ms": sorted(mal_latency)[len(mal_latency)//2],
    "max_latency_ms": max(mal_latency), "min_latency_ms": min(mal_latency),
}
data["ablation"] = {
    "severity_only": {"fp": sev_only_fp, "fp_rate": sev_only_fp / nben,
                      "recall_hits": sev_only_recall, "recall": sev_only_recall / nmal},
    "two_axis": {"fp": fp, "fp_rate": fp / nben, "recall_hits": tp, "recall": recall},
}
data["confidence_grid"] = conf_grid
data["per_sample"] = per_sample
data["latency_samples"] = sorted(mal_latency)

# ---- 2. Head-to-head vs Bandit & Semgrep -------------------------------------
def _qtrace_alert(kind, payload):
    return is_ci_alert(findings_for(kind, payload))

clear_cache()
cmp = compare(MALICIOUS, BENIGN, _qtrace_alert)
tools = cmp["tools"]
data["tools"] = tools
data["headtohead"] = {}
for t in tools:
    r, f = cmp["recall"][t], cmp["fp"][t]
    data["headtohead"][t] = {
        "recall": r["tp"] / r["n"] if r["n"] else 0, "recall_tp": r["tp"], "recall_n": r["n"],
        "fp_rate": f["fp"] / f["n"] if f["n"] else 0, "fp": f["fp"], "fp_n": f["n"],
    }
data["matrix"] = cmp["matrix"]

# ---- 3. Category-level coverage per tool -------------------------------------
cat_cov = {}
for row in cmp["matrix"]:
    cat = row["expected"]
    d = cat_cov.setdefault(cat, {t: None for t in tools})
    for t in tools:
        d[t] = row["flags"].get(t)
data["category_matrix"] = cat_cov

# ---- 4. CWE / threat-class coverage counts -----------------------------------
from findings import CATALOG
cwe_counts = {}
for meta in CATALOG.values():
    cwe_counts.setdefault(meta.cwe, {"name": meta.cwe_name, "count": 0})
    cwe_counts[meta.cwe]["count"] += 1
data["cwe_catalog"] = {
    "n_rules": len(CATALOG),
    "n_cwe": len(cwe_counts),
    "by_severity": {},
}
for meta in CATALOG.values():
    data["cwe_catalog"]["by_severity"].setdefault(meta.severity, 0)
    data["cwe_catalog"]["by_severity"][meta.severity] += 1

with open("/tmp/claude-0/-home-user--Q-Trace-pro/b8403377-1689-5a3f-82ed-d67d5cc8f269/scratchpad/paper_data.json", "w") as fh:
    json.dump(data, fh, indent=2)

print("=== COLLECTED ===")
print(json.dumps(data["headline"], indent=2))
print("head-to-head:", json.dumps(data["headtohead"], indent=2))
print("ablation:", json.dumps(data["ablation"], indent=2))
print("confidence grid:", json.dumps(data["confidence_grid"], indent=2))
print("tools:", tools, "| matrix rows:", len(data["matrix"]))
