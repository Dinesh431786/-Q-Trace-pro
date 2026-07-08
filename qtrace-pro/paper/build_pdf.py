import base64, subprocess, glob, os
SC = "/tmp/claude-0/-home-user--Q-Trace-pro/b8403377-1689-5a3f-82ed-d67d5cc8f269/scratchpad"
FIG = f"{SC}/figs"

def datauri(path):
    b = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:image/svg+xml;base64,{b}"

mapping = {
    "{{FIG_ARCH}}":  "fig1_arch.svg",
    "{{FIG_CONF}}":  "figA_confflow.svg",
    "{{FIG_SEP}}":   "fig5_confidence.svg",
    "{{FIG_ABL}}":   "fig6_ablation.svg",
    "{{FIG_QUAD}}":  "fig2_quadrant.svg",
    "{{FIG_REC}}":   "fig3_recall.svg",
    "{{FIG_FP}}":    "fig4_fp.svg",
    "{{FIG_F1}}":    "fig10_f1.svg",
    "{{FIG_CM}}":    "fig7_confusion.svg",
    "{{FIG_MAT}}":   "fig8_matrix.svg",
    "{{FIG_ONLYQ}}": "fig11_onlyq.svg",
    "{{FIG_REF}}":   "fig12_refine.svg",
    "{{FIG_LAT}}":   "fig9_latency.svg",
}
html = open(f"{SC}/paper.html").read()
for ph, fn in mapping.items():
    html = html.replace(ph, datauri(f"{FIG}/{fn}"))
assert "{{FIG" not in html, "unreplaced placeholder!"
open(f"{SC}/paper_final.html", "w").write(html)
print("wrote paper_final.html", len(html), "bytes")

chrome = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))[-1]
out = f"{SC}/QTracePro_ResearchPaper.pdf"
cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
       "--no-pdf-header-footer", f"--print-to-pdf={out}",
       f"file://{SC}/paper_final.html"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
print("chrome rc", r.returncode, (r.stderr or "")[-300:])
print("pdf bytes:", os.path.getsize(out))
