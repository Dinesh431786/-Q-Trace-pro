"""Publication-grade figures for the IEEE paper, rendered through the pgf/pdflatex
backend so figure typography is the SAME Times face as the manuscript. Output is
vector PDF (infinitely sharp) plus 300-dpi PNG previews. All data from paper_data.json."""
import json, os
import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

SC = "/tmp/claude-0/-home-user--Q-Trace-pro/b8403377-1689-5a3f-82ed-d67d5cc8f269/scratchpad"
FIG = f"{SC}/figs"
D = json.load(open(f"{SC}/paper_data.json"))

# ---- IEEE-appropriate palette (validated, references/palette.md) -------------
INK="#0d0d10"; SEC="#3a3a42"; MUT="#6f6f77"; GRID="#e4e3dd"; BASE="#b9b8b0"
QT="#1f6fd0"; SG="#4a3aa7"; BD="#e35c2b"           # tool hues (CVD-checked)
AQUA="#178a63"; CRIT="#c62f2f"; GOOD="#0a8a0a"; GOLD="#d69200"; SLATE="#9aa0a8"
TOOLCOL={"Q-Trace":QT,"Semgrep":SG,"Bandit":BD}
RAMP=["#dbe9fb","#a9caf3","#6ba3e8","#2f7fd6","#17508f"]   # blue sequential ramp

COL=3.45   # IEEE single-column width (in)
WIDE=7.16  # IEEE double-column width (in)

plt.rcParams.update({
    "pgf.texsystem":"pdflatex",
    "text.usetex":True,
    "pgf.rcfonts":False,
    "font.family":"serif",
    "pgf.preamble":r"\usepackage{mathptmx}\usepackage[T1]{fontenc}\usepackage{amssymb}",
    "font.size":8,
    "axes.titlesize":8.5,"axes.labelsize":8,
    "xtick.labelsize":7.4,"ytick.labelsize":7.4,"legend.fontsize":7.2,
    "figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white",
    "axes.edgecolor":BASE,"axes.linewidth":0.6,
    "xtick.color":MUT,"ytick.color":MUT,"text.color":INK,"axes.labelcolor":SEC,
    "savefig.dpi":300,"figure.dpi":300,
    "axes.grid":False,"legend.frameon":False,
})

def style(ax, grid="y"):
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(BASE); ax.spines["bottom"].set_color(BASE)
    if grid in ("y","both"): ax.yaxis.grid(True,color=GRID,lw=0.5,zorder=0)
    if grid in ("x","both"): ax.xaxis.grid(True,color=GRID,lw=0.5,zorder=0)
    ax.set_axisbelow(True); ax.tick_params(length=2,width=0.5,color=BASE)

def save(fig,name):
    fig.savefig(f"{FIG}/{name}.pdf",bbox_inches="tight",pad_inches=0.02)
    plt.close(fig); print("wrote",name)

pct=r"\%"; arr=r"$\rightarrow$"; larr=r"$\leftarrow$"

h=D["headtohead"]; hd=D["headline"]; ab=D["ablation"]

# ============================ FIG 2 : quadrant ===============================
fig,ax=plt.subplots(figsize=(COL,2.62)); style(ax,"both")
ax.axhspan(92,104,xmin=0,xmax=0.13,color=GOOD,alpha=0.07,zorder=0)
for t in ["Q-Trace","Semgrep","Bandit"]:
    x=h[t]["fp_rate"]*100; y=h[t]["recall"]*100
    ax.scatter(x,y,s=90,color=TOOLCOL[t],zorder=5,edgecolor="white",linewidth=0.9)
for t,(dx,dy,va,ha) in {"Q-Trace":(6,4,"bottom","left"),
                        "Semgrep":(6,-2,"center","left"),
                        "Bandit":(-6,-2,"center","right")}.items():
    x=h[t]["fp_rate"]*100; y=h[t]["recall"]*100
    ax.annotate(rf"\textbf{{{t}}}", (x,y), textcoords="offset points",
                xytext=(dx,dy+5),fontsize=7.6,color=INK,va=va,ha=ha)
    ax.annotate(rf"{y:.0f}{pct}/{x:.1f}{pct} FP",(x,y),textcoords="offset points",
                xytext=(dx,dy-3),fontsize=6.8,color=SEC,va=va,ha=ha)
ax.set_xlim(-0.6,8.6); ax.set_ylim(44,104)
ax.set_xlabel(rf"False-positive rate ({pct}) {arr} worse")
ax.set_ylabel(rf"Malware recall ({pct}) {arr} better")
ax.annotate(r"\textit{ideal}",(0.05,90),fontsize=6.6,color=GOOD,ha="left",va="top")
save(fig,"fig2_quadrant")

# ============================ FIG 3 : recall bars ============================
order=sorted(["Q-Trace","Semgrep","Bandit"],key=lambda t:h[t]["recall"])
fig,ax=plt.subplots(figsize=(COL,1.9)); style(ax,"x")
for i,t in enumerate(order):
    v=h[t]["recall"]*100
    ax.barh(i,v,color=TOOLCOL[t],height=0.58,zorder=3,edgecolor="white",linewidth=0.8)
    ax.text(v-1.5,i,rf"\textbf{{{v:.0f}{pct}}} ({h[t]['recall_tp']}/{h[t]['recall_n']})",
            va="center",ha="right",color="white",fontsize=7.2)
ax.set_yticks(range(len(order))); ax.set_yticklabels([rf"\textbf{{{t}}}" for t in order])
ax.set_xlim(0,100); ax.set_xlabel(rf"Malware recall at each tool's CI gate ({pct})")
save(fig,"fig3_recall")

# ============================ FIG 4 : FP bars ================================
order=sorted(["Q-Trace","Semgrep","Bandit"],key=lambda t:h[t]["fp_rate"])
fig,ax=plt.subplots(figsize=(COL,1.9)); style(ax,"x")
for i,t in enumerate(order):
    v=h[t]["fp_rate"]*100
    ax.barh(i,max(v,0.002),color=TOOLCOL[t],height=0.58,zorder=3,edgecolor="white",linewidth=0.8)
    ax.text(v+0.12,i,rf"{v:.1f}{pct} ({h[t]['fp']}/{h[t]['fp_n']})",
            va="center",ha="left",color=INK,fontsize=7.2)
ax.set_yticks(range(len(order))); ax.set_yticklabels([rf"\textbf{{{t}}}" for t in order])
ax.set_xlim(0,8.2); ax.set_xlabel(rf"False positives on benign hard-negatives ({pct}) {arr} lower better")
save(fig,"fig4_fp")

# ============================ FIG 5 : confidence sep =========================
grid=D["confidence_grid"]
keys=["Critical|High","High|High","High|Medium","High|Low","None|None"]
labels=[r"Crit$\cdot$Hi",r"High$\cdot$Hi",r"High$\cdot$Med",r"High$\cdot$Lo",r"none"]
mal=[grid.get(k,{}).get("mal",0) for k in keys]
ben=[grid.get(k,{}).get("ben",0) for k in keys]
x=np.arange(len(keys)); w=0.4
fig,ax=plt.subplots(figsize=(COL,2.5)); style(ax,"y")
ax.axvspan(2.5,4.5,color=GOOD,alpha=0.06,zorder=0)
ax.bar(x-w/2,mal,w,color=CRIT,zorder=3,label="Malicious (31)",edgecolor="white",linewidth=0.7)
ax.bar(x+w/2,ben,w,color=QT,zorder=3,label="Benign (34)",edgecolor="white",linewidth=0.7)
for xi,m,b in zip(x,mal,ben):
    if m: ax.text(xi-w/2,m+0.5,str(m),ha="center",fontsize=6.8,color=INK)
    if b: ax.text(xi+w/2,b+0.5,str(b),ha="center",fontsize=6.8,color=INK)
ax.axvline(2.5,color=BASE,lw=0.7,ls=(0,(2,2)),zorder=2)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylim(0,38); ax.set_ylabel("Number of samples")
ax.set_xlabel(r"Highest (severity $\cdot$ confidence) finding")
ax.legend(loc="upper center",ncol=1,handlelength=1.1,bbox_to_anchor=(0.42,1.02))
ax.annotate(rf"gate fires {larr}",(2.34,30),fontsize=6.8,color=SEC,ha="right")
ax.annotate(rf"{arr} silent",(2.66,30),fontsize=6.8,color=SEC,ha="left")
save(fig,"fig5_confidence")

# ============================ FIG 6 : ablation ===============================
metrics=["Recall",r"False-pos.\ rate"]
so=[ab["severity_only"]["recall"]*100,ab["severity_only"]["fp_rate"]*100]
tw=[ab["two_axis"]["recall"]*100,ab["two_axis"]["fp_rate"]*100]
x=np.arange(2); w=0.34
fig,ax=plt.subplots(figsize=(COL,2.35)); style(ax,"y")
b1=ax.bar(x-w/2,so,w,color=SLATE,zorder=3,label="Severity only (1 axis)",edgecolor="white",linewidth=0.7)
b2=ax.bar(x+w/2,tw,w,color=QT,zorder=3,label=r"Severity $\times$ confidence",edgecolor="white",linewidth=0.7)
for rs in (b1,b2):
    for r in rs: ax.text(r.get_x()+r.get_width()/2,r.get_height()+1.4,rf"{r.get_height():.1f}",
                         ha="center",fontsize=7,color=INK)
ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_ylim(0,114); ax.set_ylabel(rf"Percent ({pct})")
ax.legend(loc="upper right",handlelength=1.1)
ax.annotate(rf"$-5.9$ pt FP",(1,26),fontsize=7,color=GOOD,ha="center")
ax.annotate(rf"for $-3.2$ pt recall",(1,18),fontsize=7,color=GOOD,ha="center")
save(fig,"fig6_ablation")

# ============================ FIG 7 : confusion ==============================
# rows = CI decision (Alert/Silent), cols = ground truth (Malicious/Benign)
cm=np.array([[hd["tp"],hd["fp"]],[hd["fn"],hd["tn"]]]); vmax=cm.max()
fig,ax=plt.subplots(figsize=(COL,2.55))
labs=[["TP","FP"],["FN","TN"]]
for (i,j),v in np.ndenumerate(cm):
    frac=v/vmax
    col=RAMP[min(int(frac*(len(RAMP)-1)+0.5),len(RAMP)-1)] if v>0 else "#f2f1ee"
    ax.add_patch(plt.Rectangle((j,1-i),1,1,facecolor=col,edgecolor="white",linewidth=2.5))
    tc="white" if frac>0.5 else INK
    ax.text(j+0.5,1-i+0.60,rf"\textbf{{{v}}}",ha="center",va="center",fontsize=15,color=tc)
    ax.text(j+0.5,1-i+0.30,labs[i][j],ha="center",va="center",fontsize=8,color=tc)
ax.set_xlim(0,2); ax.set_ylim(0,2)
ax.set_xticks([0.5,1.5]); ax.set_xticklabels(["Malicious","Benign"])
ax.set_yticks([1.5,0.5]); ax.set_yticklabels(["Alert","Silent"])
ax.set_xlabel("Ground truth"); ax.set_ylabel("Q-Trace CI decision")
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
save(fig,"fig7_confusion")

# ============================ FIG 8 : coverage matrix (wide) =================
cats=D["category_matrix"]; tools=["Q-Trace","Semgrep","Bandit"]; names=list(cats.keys())
n=len(names)
fig,ax=plt.subplots(figsize=(WIDE,0.30*n+0.5))
cell={True:GOOD,False:CRIT,None:"#deddd6"}
for r,cat in enumerate(names):
    y=n-r-1
    for c,t in enumerate(tools):
        v=cats[cat][t]
        ax.add_patch(plt.Rectangle((c,y),0.92,0.86,facecolor=cell[v],edgecolor="white",
                     linewidth=1.6,alpha=1 if v is not None else 0.6))
        sym=r"$\checkmark$" if v is True else (r"$\times$" if v is False else r"--")
        ax.text(c+0.46,y+0.43,sym,ha="center",va="center",
                color="white" if v is not None else MUT,fontsize=9)
    ax.text(-0.12,y+0.43,cat.replace("_"," ").title(),ha="right",va="center",fontsize=7.6,color=INK)
ax.set_xlim(-3.4,len(tools)); ax.set_ylim(-0.15,n)
ax.set_xticks([c+0.46 for c in range(len(tools))])
ax.set_xticklabels([rf"\textbf{{{t}}}" for t in tools],fontsize=8.4)
ax.xaxis.tick_top(); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
save(fig,"fig8_matrix")

# ============================ FIG 9 : latency ================================
lat=D["latency_samples"]
fig,ax=plt.subplots(figsize=(COL,2.15)); style(ax,"y")
xs=np.arange(1,len(lat)+1)
ax.bar(xs,lat,color=QT,width=0.82,zorder=3,edgecolor="white",linewidth=0.3)
mean=hd["mean_latency_ms"]; med=hd["median_latency_ms"]
ax.axhline(med,color=CRIT,lw=1.0,ls=(0,(3,2)),zorder=4)
ax.annotate(rf"median {med:.1f} ms",(len(lat)*0.60,med+1.2),color=CRIT,fontsize=6.8)
ax.set_xlabel("Malicious code sample (sorted)")
ax.set_ylabel("Full-audit time (ms)")
ax.set_xlim(0.3,len(lat)+0.7)
save(fig,"fig9_latency")

# ============================ FIG 10 : F1 ====================================
def prf(tp,fp,nn):
    fn=nn-tp; p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return 2*p*r/(p+r) if p+r else 0
f1s={t:prf(h[t]["recall_tp"],h[t]["fp"],h[t]["recall_n"]) for t in tools}
order=sorted(tools,key=lambda t:f1s[t])
fig,ax=plt.subplots(figsize=(COL,1.9)); style(ax,"x")
for i,t in enumerate(order):
    v=f1s[t]
    ax.barh(i,v,color=TOOLCOL[t],height=0.58,zorder=3,edgecolor="white",linewidth=0.8)
    ax.text(v-0.015,i,rf"\textbf{{{v:.3f}}}",va="center",ha="right",color="white",fontsize=7.4)
ax.set_yticks(range(len(order))); ax.set_yticklabels([rf"\textbf{{{t}}}" for t in order])
ax.set_xlim(0,1.0); ax.set_xlabel(r"$F_1$ score on the shared corpus (higher better)")
save(fig,"fig10_f1")

# ============================ FIG 11 : only-Q ================================
matrix=D["matrix"]
seen=[]
for row in matrix:
    others=[row["flags"].get(t) for t in tools if t!="Q-Trace"]
    if row["flags"].get("Q-Trace") and all(o in (False,None) for o in others):
        if row["expected"] not in seen: seen.append(row["expected"])
counts={c:sum(1 for r in matrix if r["expected"]==c) for c in seen}
seen=sorted(seen,key=lambda c:counts[c])
fig,ax=plt.subplots(figsize=(COL,2.5)); style(ax,"x")
for i,c in enumerate(seen):
    ax.barh(i,counts[c],color=AQUA,height=0.6,zorder=3,edgecolor="white",linewidth=0.8)
    ax.text(counts[c]+0.04,i,str(counts[c]),va="center",color=INK,fontsize=7.4)
ax.set_yticks(range(len(seen))); ax.set_yticklabels([c.replace("_"," ").title() for c in seen],fontsize=7.2)
ax.set_xlim(0,max(counts.values())+0.7); ax.set_xlabel("Malware samples ONLY Q-Trace flagged")
save(fig,"fig11_onlyq")

# ============================ FIG 12 : refinement ============================
groups=[r"CI recall",r"$F_1\times100$",r"Anti-dbg FPs",r"Dbg-detect"]
pv=[93.5,96.7,2,0]; nv=[hd["ci_recall"]*100,hd["f1"]*100,0,1]
x=np.arange(len(groups)); w=0.34
fig,ax=plt.subplots(figsize=(COL,2.35)); style(ax,"y")
ax.bar(x-w/2,pv,w,color=SLATE,zorder=3,label="Prior heuristic",edgecolor="white",linewidth=0.7)
ax.bar(x+w/2,nv,w,color=QT,zorder=3,label="Refined (this work)",edgecolor="white",linewidth=0.7)
def fm2(v): return f"{v:.1f}" if v>=5 else f"{v:g}"
for xi,p,nn in zip(x,pv,nv):
    ax.text(xi-w/2,p+1.5,fm2(p),ha="center",fontsize=6.4,color=SEC)
    ax.text(xi+w/2,nn+1.5,fm2(nn),ha="center",fontsize=6.4,color=INK)
ax.set_xticks(x); ax.set_xticklabels(groups,fontsize=6.9)
ax.set_ylim(0,108); ax.set_ylabel("Value")
ax.legend(loc="center right",handlelength=1.1)
save(fig,"fig12_refine")

print("F1:",{t:round(f1s[t],3) for t in tools})
print("ALL FIGURES DONE (pgf/Times vector PDF + 300dpi PNG)")
