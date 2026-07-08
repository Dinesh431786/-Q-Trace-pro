"""Generate all research-paper figures as SVG from paper_data.json.
Design per the dataviz method: correct form per data job, validated categorical
palette in fixed order, no dual axis, recessive grid, direct labels, status
colors reserved. Light print surface."""
import json, os
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

SC = "/tmp/claude-0/-home-user--Q-Trace-pro/b8403377-1689-5a3f-82ed-d67d5cc8f269/scratchpad"
FIG = f"{SC}/figs"
D = json.load(open(f"{SC}/paper_data.json"))

# ---- Validated palette (references/palette.md, light surface) ----------------
SURF = "#fcfcfb"; INK = "#0b0b0b"; SEC = "#52514e"; MUT = "#898781"
GRID = "#e1e0d9"; BASE = "#c3c2b7"
QT = "#2a78d6"      # blue  (slot 1)  -> Q-Trace
SG = "#4a3aa7"      # violet(slot 5)  -> Semgrep
BD = "#eb6834"      # orange(slot 8)  -> Bandit
AQUA = "#1baf7a"; YEL = "#eda100"; RED = "#e34948"; MAG = "#e87ba4"
GOOD = "#0ca30c"; CRIT = "#d03b3b"; WARN = "#fab219"
TOOLCOL = {"Q-Trace": QT, "Semgrep": SG, "Bandit": BD}

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Arial"],
    "text.color": INK, "axes.labelcolor": SEC, "axes.edgecolor": BASE,
    "xtick.color": MUT, "ytick.color": MUT, "font.size": 10.5,
    "axes.linewidth": 0.8, "svg.fonttype": "none",
})

def style(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(BASE); ax.spines["bottom"].set_color(BASE)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)

def save(fig, name):
    fig.savefig(f"{FIG}/{name}.svg", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("wrote", name)

# =============================================================================
# FIG 2 — Recall vs FP quadrant (the money chart)
# =============================================================================
h = D["headtohead"]
fig, ax = plt.subplots(figsize=(6.4, 4.3))
style(ax, grid_axis="both")
for t in ["Q-Trace", "Semgrep", "Bandit"]:
    x = h[t]["fp_rate"] * 100; y = h[t]["recall"] * 100
    ax.scatter(x, y, s=320, color=TOOLCOL[t], zorder=5, edgecolor=SURF, linewidth=2)
    dy = 4.2 if t != "Bandit" else -6.5
    ax.annotate(f"{t}\n{y:.0f}% recall · {x:.1f}% FP", (x, y),
                textcoords="offset points", xytext=(12, dy), fontsize=9.5,
                color=INK, fontweight="bold", va="center")
ax.set_xlim(-0.6, 8.8); ax.set_ylim(40, 106)
ax.set_xlabel("False-positive rate on benign hard-negatives  (%)  →  worse")
ax.set_ylabel("Malware recall  (%)  →  better")
ax.axhspan(90, 106, xmin=0, xmax=0.14, color=GOOD, alpha=0.06, zorder=0)
ax.annotate("ideal corner", (0.05, 88.5), fontsize=8.5, color=GOOD, ha="left", va="top",
            style="italic")
save(fig, "fig2_quadrant")

# =============================================================================
# FIG 3 — Malware recall by tool (horizontal bars, sorted)
# =============================================================================
order = sorted(["Q-Trace", "Semgrep", "Bandit"], key=lambda t: h[t]["recall"])
fig, ax = plt.subplots(figsize=(6.4, 2.7))
style(ax, grid_axis="x")
for i, t in enumerate(order):
    v = h[t]["recall"] * 100
    ax.barh(i, v, color=TOOLCOL[t], height=0.62, zorder=3,
            edgecolor=SURF, linewidth=1.5)
    ax.text(v - 2, i, f"{v:.0f}%  ({h[t]['recall_tp']}/{h[t]['recall_n']})",
            va="center", ha="right", color="white", fontweight="bold", fontsize=10)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, color=INK, fontweight="bold")
ax.set_xlim(0, 100); ax.set_xlabel("Malware recall at each tool's own CI gate  (%)")
save(fig, "fig3_recall")

# =============================================================================
# FIG 4 — False-positive rate by tool
# =============================================================================
order = sorted(["Q-Trace", "Semgrep", "Bandit"], key=lambda t: h[t]["fp_rate"])
fig, ax = plt.subplots(figsize=(6.4, 2.7))
style(ax, grid_axis="x")
for i, t in enumerate(order):
    v = h[t]["fp_rate"] * 100
    ax.barh(i, max(v, 0.001), color=TOOLCOL[t], height=0.62, zorder=3,
            edgecolor=SURF, linewidth=1.5)
    lbl = f"{v:.1f}%" if v > 0 else "0.0%"
    ax.text(v + 0.12, i, f"{lbl}  ({h[t]['fp']}/{h[t]['fp_n']})", va="center",
            ha="left", color=INK, fontsize=10)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, color=INK, fontweight="bold")
ax.set_xlim(0, 8); ax.set_xlabel("False-positive rate on benign hard-negatives  (%)  →  lower is better")
save(fig, "fig4_fp")

# =============================================================================
# FIG 5 — Two-axis confidence separation (malicious vs benign clustering)
# =============================================================================
grid = D["confidence_grid"]
order_keys = ["Critical|High", "High|High", "High|Medium", "High|Low", "None|None"]
labels = ["Critical\n·High", "High\n·High", "High\n·Medium", "High\n·Low", "no\nfinding"]
mal = [grid.get(k, {}).get("mal", 0) for k in order_keys]
ben = [grid.get(k, {}).get("ben", 0) for k in order_keys]
x = np.arange(len(order_keys)); w = 0.4
fig, ax = plt.subplots(figsize=(6.6, 3.8))
style(ax, grid_axis="y")
ax.bar(x - w/2, mal, w, color=CRIT, zorder=3, label="Malicious (n=31)", edgecolor=SURF, linewidth=1.2)
ax.bar(x + w/2, ben, w, color=QT, zorder=3, label="Benign (n=34)", edgecolor=SURF, linewidth=1.2)
for xi, m, b in zip(x, mal, ben):
    if m: ax.text(xi - w/2, m + 0.5, str(m), ha="center", color=INK, fontsize=9, fontweight="bold")
    if b: ax.text(xi + w/2, b + 0.5, str(b), ha="center", color=INK, fontsize=9, fontweight="bold")
ax.axvspan(2.5, 4.5, color=GOOD, alpha=0.05, zorder=0)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9, color=INK)
ax.set_ylabel("Number of samples"); ax.set_ylim(0, 39)
ax.set_xlabel("Highest (severity · confidence) finding per sample")
ax.legend(frameon=False, loc="upper left", fontsize=9.5, bbox_to_anchor=(0.0, 1.0))
ax.axvline(2.5, color=BASE, linewidth=1, linestyle=":", zorder=2)
ax.annotate("CI gate fires  ⟵", (2.35, 24), fontsize=9, color=SEC, ha="right", fontweight="bold")
ax.annotate("⟶  gate stays silent", (2.65, 24), fontsize=9, color=SEC, ha="left", fontweight="bold")
save(fig, "fig5_confidence")

# =============================================================================
# FIG 6 — Ablation: severity-only gate vs two-axis gate
# =============================================================================
ab = D["ablation"]
metrics = ["Recall", "False-positive rate"]
so = [ab["severity_only"]["recall"]*100, ab["severity_only"]["fp_rate"]*100]
tw = [ab["two_axis"]["recall"]*100, ab["two_axis"]["fp_rate"]*100]
x = np.arange(2); w = 0.36
fig, ax = plt.subplots(figsize=(6.2, 3.6))
style(ax, grid_axis="y")
b1 = ax.bar(x - w/2, so, w, color=BASE, zorder=3, label="Severity-only gate (1 axis)", edgecolor=SURF, linewidth=1.2)
b2 = ax.bar(x + w/2, tw, w, color=QT, zorder=3, label="Severity × confidence (2 axes)", edgecolor=SURF, linewidth=1.2)
for rects in (b1, b2):
    for r in rects:
        ax.text(r.get_x()+r.get_width()/2, r.get_height()+1.2, f"{r.get_height():.1f}",
                ha="center", color=INK, fontsize=9.5, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(metrics, color=INK, fontweight="bold")
ax.set_ylabel("Percent"); ax.set_ylim(0, 112)
ax.legend(frameon=False, loc="upper right", fontsize=9)
ax.annotate("−5.9 pt FP\nfor −3.2 pt recall", (1, 20), fontsize=9, color=GOOD,
            ha="center", fontweight="bold")
save(fig, "fig6_ablation")

# =============================================================================
# FIG 7 — Confusion matrix (Q-Trace)
# =============================================================================
hd = D["headline"]
cm = np.array([[hd["tp"], hd["fn"]], [hd["fp"], hd["tn"]]])
fig, ax = plt.subplots(figsize=(4.2, 3.9))
# blue sequential ramp for magnitude
ramp = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]
vmax = cm.max()
for (i, j), v in np.ndenumerate(cm):
    frac = v / vmax
    col = ramp[min(int(frac * (len(ramp)-1) + 0.5), len(ramp)-1)] if v > 0 else "#f0efec"
    ax.add_patch(plt.Rectangle((j, 1-i), 1, 1, facecolor=col, edgecolor=SURF, linewidth=3))
    tcol = "white" if frac > 0.45 else INK
    lbl = ["TP", "FN", "FP", "TN"][i*2+j]
    ax.text(j+0.5, 1-i+0.58, str(v), ha="center", va="center", fontsize=20,
            fontweight="bold", color=tcol)
    ax.text(j+0.5, 1-i+0.28, lbl, ha="center", va="center", fontsize=10, color=tcol)
ax.set_xlim(0, 2); ax.set_ylim(0, 2)
ax.set_xticks([0.5, 1.5]); ax.set_xticklabels(["Malicious", "Benign"], color=INK, fontweight="bold")
ax.set_yticks([1.5, 0.5]); ax.set_yticklabels(["Alert", "Silent"], color=INK, fontweight="bold")
ax.set_xlabel("Ground truth", color=SEC); ax.set_ylabel("Q-Trace CI decision", color=SEC)
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
save(fig, "fig7_confusion")

# =============================================================================
# FIG 8 — Per-category coverage matrix (tool x threat class)
# =============================================================================
cats = D["category_matrix"]
tools = ["Q-Trace", "Semgrep", "Bandit"]
names = list(cats.keys())
fig, ax = plt.subplots(figsize=(6.8, max(4.5, 0.34*len(names))))
cell = {True: GOOD, False: RED, None: "#e6e5e0"}
for r, cat in enumerate(names):
    y = len(names) - r - 1
    for c, t in enumerate(tools):
        v = cats[cat][t]
        ax.add_patch(plt.Rectangle((c, y), 0.94, 0.94, facecolor=cell[v],
                     edgecolor=SURF, linewidth=2, alpha=0.9 if v is not None else 0.5))
        sym = "✓" if v is True else ("✕" if v is False else "–")
        ax.text(c+0.47, y+0.47, sym, ha="center", va="center", color="white" if v is not None else MUT,
                fontsize=12, fontweight="bold")
    ax.text(-0.15, y+0.47, cat.replace("_", " ").title(), ha="right", va="center",
            fontsize=8.3, color=INK)
ax.set_xlim(-3.2, len(tools)); ax.set_ylim(0, len(names))
ax.set_xticks([c+0.47 for c in range(len(tools))])
ax.set_xticklabels(tools, color=INK, fontweight="bold", fontsize=10)
ax.xaxis.tick_top()
ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
# legend
ax.text(-3.1, -0.9, "✓ detected      ✕ missed      – input class not supported",
        fontsize=8.5, color=SEC, transform=ax.transData)
save(fig, "fig8_matrix")

# =============================================================================
# FIG 9 — Latency distribution (per-sample analysis time, sorted ECDF-ish)
# =============================================================================
lat = D["latency_samples"]
fig, ax = plt.subplots(figsize=(6.4, 3.2))
style(ax, grid_axis="y")
xs = range(1, len(lat)+1)
ax.bar(xs, lat, color=QT, width=0.8, zorder=3, edgecolor=SURF, linewidth=0.4)
mean = hd["mean_latency_ms"]; med = hd["median_latency_ms"]
ax.axhline(mean, color=CRIT, linewidth=1.4, linestyle="--", zorder=4)
ax.annotate(f"mean {mean:.2f} ms", (len(lat)*0.62, mean), color=CRIT, fontsize=9,
            va="bottom", fontweight="bold")
ax.set_xlabel("Malicious code sample (sorted by analysis time)")
ax.set_ylabel("Full-audit time (ms)")
ax.set_xlim(0.4, len(lat)+0.6)
save(fig, "fig9_latency")

# =============================================================================
# FIG 10 — F1 by tool (computed from tp/fp/fn on the shared code corpus)
# =============================================================================
def prf(tp, fp, n):
    fn = n - tp
    prec = tp/(tp+fp) if (tp+fp) else 0
    rec = tp/(tp+fn) if (tp+fn) else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec) else 0
    return prec, rec, f1
f1s = {}
for t in tools:
    tp = h[t]["recall_tp"]; n = h[t]["recall_n"]; fp = h[t]["fp"]
    f1s[t] = prf(tp, fp, n)[2]
order = sorted(tools, key=lambda t: f1s[t])
fig, ax = plt.subplots(figsize=(6.4, 2.7))
style(ax, grid_axis="x")
for i, t in enumerate(order):
    v = f1s[t]
    ax.barh(i, v, color=TOOLCOL[t], height=0.62, zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.text(v-0.02, i, f"{v:.3f}", va="center", ha="right", color="white",
            fontweight="bold", fontsize=10.5)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, color=INK, fontweight="bold")
ax.set_xlim(0, 1.0); ax.set_xlabel("F1 score on the shared .py corpus  (higher is better)")
save(fig, "fig10_f1")

# =============================================================================
# FIG 11 — Stealth-class coverage: classes caught only by Q-Trace
# =============================================================================
matrix = D["matrix"]
only_q = []
for row in matrix:
    fq = row["flags"].get("Q-Trace")
    others = [row["flags"].get(t) for t in tools if t != "Q-Trace"]
    if fq and all(o in (False, None) for o in others):
        only_q.append(row["expected"])
# dedupe preserve order
seen = [];
for c in only_q:
    if c not in seen: seen.append(c)
counts = {c: sum(1 for r in matrix if r["expected"]==c) for c in seen}
fig, ax = plt.subplots(figsize=(6.6, 3.4))
style(ax, grid_axis="x")
ys = range(len(seen))
for i, c in enumerate(seen):
    ax.barh(i, counts[c], color=AQUA, height=0.6, zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.text(counts[c]+0.03, i, str(counts[c]), va="center", color=INK, fontsize=10, fontweight="bold")
ax.set_yticks(list(ys)); ax.set_yticklabels([c.replace("_"," ").title() for c in seen],
              color=INK, fontsize=9)
ax.set_xlim(0, max(counts.values())+0.8)
ax.set_xlabel("Malicious samples in this class that ONLY Q-Trace flagged")
save(fig, "fig11_onlyq")

# =============================================================================
# FIG 12 — Algorithm refinement: prior vs refined anti-analysis engine
# =============================================================================
# Prior-version numbers measured at session start (documented, reproducible).
prior = {"ci_recall": 93.5, "f1": 96.7, "antidebug_fp": 2, "gettrace": 0}
new = {"ci_recall": hd["ci_recall"]*100, "f1": hd["f1"]*100, "antidebug_fp": 0, "gettrace": 1}
groups = ["CI-gate recall (%)", "F1 × 100", "Anti-debug FPs\n(log.debug, retry sleep)", "Debugger-detection\ncoverage"]
pv = [prior["ci_recall"], prior["f1"], prior["antidebug_fp"], prior["gettrace"]]
nv = [new["ci_recall"], new["f1"], new["antidebug_fp"], new["gettrace"]]
x = np.arange(len(groups)); w = 0.36
fig, ax = plt.subplots(figsize=(6.8, 3.6))
style(ax, grid_axis="y")
ax.bar(x-w/2, pv, w, color=BASE, zorder=3, label="Prior heuristic", edgecolor=SURF, linewidth=1.2)
ax.bar(x+w/2, nv, w, color=QT, zorder=3, label="Refined (this work)", edgecolor=SURF, linewidth=1.2)
def _fmt(v):
    return f"{v:.1f}" if v >= 5 else f"{v:g}"
for xi, p, n in zip(x, pv, nv):
    ax.text(xi-w/2, p+1, _fmt(p), ha="center", color=SEC, fontsize=8.5)
    ax.text(xi+w/2, n+1, _fmt(n), ha="center", color=INK, fontsize=8.5, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=8.3, color=INK)
ax.set_ylim(0, 105); ax.set_ylabel("Value")
ax.legend(frameon=False, loc="center right", fontsize=9)
save(fig, "fig12_refine")

print("\nDerived F1 per tool:", {t: round(f1s[t],3) for t in tools})
print("ALL FIGURES DONE")
