"""Emit the appendix LaTeX tables (catalogue + per-sample) from paper_data.json.
Rows are joined by '\\' between rows with NO trailing backslash (the template
supplies the final one) to avoid a Misplaced-\\noalign at the \\input/EOF boundary."""
import json, sys
sys.path.insert(0, "/home/user/-Q-Trace-pro/qtrace-pro")
from findings import CATALOG

D = json.load(open("paper_data.json"))
def esc(s): return s.replace("_", r"\_").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
CK, X, DASH = r"$\checkmark$", r"$\times$", r"--"
SEP = "\\\\\n"

cat = [f"{esc(m.title)} & {m.cwe} & {esc(m.severity)} & {esc(m.base_confidence)}"
       for k, m in sorted(CATALOG.items(), key=lambda kv: (kv[1].severity, kv[0]))]
open("catalog_table.tex", "w").write(SEP.join(cat))

sym = {True: CK, False: X, None: DASH}
mal = [f"{esc(r['name'])} & {esc(r['expected'])} & {sym[r['flags'].get('Q-Trace')]} & "
       f"{sym[r['flags'].get('Semgrep')]} & {sym[r['flags'].get('Bandit')]}" for r in D["matrix"]]
open("mal_table.tex", "w").write(SEP.join(mal))

ben = []
for r in D["per_sample"]:
    if r["cls"] != "benign":
        continue
    dec = f"{X} alert" if r["alert"] else f"{CK} clean"
    top = f"{esc(r['severity'])}/{esc(r['confidence'])}" if r['severity'] != 'None' else DASH
    ben.append(f"{esc(r['name'])} & {dec} & {top}")
open("ben_table.tex", "w").write(SEP.join(ben))
print(f"catalog {len(cat)}  malicious {len(mal)}  benign {len(ben)} rows")
