"""Publication-standard figures (IEEE/scientific convention) via pgf/pdflatex so
figure type is the SAME Times face as the manuscript. Conventions follow SciencePlots
and Rougier et al., 'Ten Simple Rules for Better Figures': full bounding box, inward
minor ticks on all four sides, restrained ink, B&W-safe hatching, multi-panel
composites with (a)/(b)/(c) labels. Vector PDF output. Data from paper_data.json."""
import json, os
import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt
import numpy as np

SC="/tmp/claude-0/-home-user--Q-Trace-pro/b8403377-1689-5a3f-82ed-d67d5cc8f269/scratchpad"
FIG=f"{SC}/figs"
D=json.load(open(f"{SC}/paper_data.json"))

# validated palette (references/palette.md)
INK="#0d0d10"; SEC="#33333a"; MUT="#5f5f66"; FRAME="#4a4a50"
QT="#1f6fd0"; SG="#5a4bbf"; BD="#e06a2a"; AQUA="#178a63"; CRIT="#c62f2f"; GOOD="#0a8a0a"
TOOLCOL={"Q-Trace":QT,"Semgrep":SG,"Bandit":BD}
HATCH={"Q-Trace":"","Semgrep":"////","Bandit":"...."}
RAMP=["#e7f0fb","#bcd6f4","#7fb0e8","#3f88d8","#1a56a0"]

COL=3.42; WIDE=7.0

plt.rcParams.update({
 "pgf.texsystem":"pdflatex","text.usetex":True,"pgf.rcfonts":False,"font.family":"serif",
 "pgf.preamble":r"\usepackage{mathptmx}\usepackage[T1]{fontenc}\usepackage{amssymb}",
 "font.size":8,"axes.titlesize":8.5,"axes.labelsize":8,
 "xtick.labelsize":7.2,"ytick.labelsize":7.2,"legend.fontsize":7.0,
 "figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white",
 "axes.linewidth":0.6,"axes.edgecolor":FRAME,
 "xtick.direction":"in","ytick.direction":"in","xtick.top":True,"ytick.right":True,
 "xtick.major.size":3,"ytick.major.size":3,"xtick.minor.size":1.6,"ytick.minor.size":1.6,
 "xtick.major.width":0.5,"ytick.major.width":0.5,"xtick.minor.width":0.5,"ytick.minor.width":0.5,
 "xtick.color":INK,"ytick.color":INK,"axes.labelcolor":INK,"text.color":INK,
 "legend.fancybox":False,"legend.edgecolor":FRAME,"legend.framealpha":1.0,
 "hatch.linewidth":0.5,"savefig.dpi":600,
})

def sci(ax, minor=True, cat_axis=None):
    for s in ax.spines.values(): s.set_visible(True); s.set_linewidth(0.6); s.set_color(FRAME)
    ax.tick_params(which="both",direction="in",top=True,right=True)
    if minor: ax.minorticks_on()
    if cat_axis=="x": ax.tick_params(axis="x",which="minor",bottom=False,top=False)
    if cat_axis=="y": ax.tick_params(axis="y",which="minor",left=False,right=False)

def save(fig,name):
    fig.savefig(f"{FIG}/{name}.pdf",bbox_inches="tight",pad_inches=0.02)
    plt.close(fig); print("wrote",name)

def panel(ax,tag,dx=-0.20,dy=1.06):
    ax.text(dx,dy,rf"\textbf{{({tag})}}",transform=ax.transAxes,fontsize=8.5,va="top",ha="left")

pct=r"\%"
h=D["headtohead"]; hd=D["headline"]; ab=D["ablation"]; tools=["Q-Trace","Semgrep","Bandit"]

def prf(tp,fp,n):
    fn=n-tp; p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return 2*p*r/(p+r) if p+r else 0
F1={t:prf(h[t]["recall_tp"],h[t]["fp"],h[t]["recall_n"]) for t in tools}

# =========== FIG 2 : quadrant (single) =====================================
fig,ax=plt.subplots(figsize=(COL,2.7)); sci(ax)
ax.axhspan(92,103,xmin=0,xmax=0.12,color=GOOD,alpha=0.07,lw=0)
mk={"Q-Trace":"o","Semgrep":"s","Bandit":"^"}
for t in tools:
    x=h[t]["fp_rate"]*100; y=h[t]["recall"]*100
    ax.scatter(x,y,s=64,marker=mk[t],color=TOOLCOL[t],zorder=5,edgecolor="white",linewidth=0.8,label=t)
for t,(dx,dy,ha) in {"Q-Trace":(0.28,4.5,"left"),"Semgrep":(0.28,-1,"left"),"Bandit":(-0.28,-4.5,"right")}.items():
    x=h[t]["fp_rate"]*100; y=h[t]["recall"]*100
    ax.annotate(rf"{h[t]['recall_tp']}/{h[t]['recall_n']}, {y:.0f}{pct}",(x,y),
                textcoords="offset points",xytext=(9 if ha=='left' else -9,dy),fontsize=6.6,color=SEC,ha=ha)
ax.set_xlim(-0.7,8.6); ax.set_ylim(45,103)
ax.set_xlabel(rf"False-positive rate ({pct})"); ax.set_ylabel(rf"Malware recall ({pct})")
ax.annotate(r"\textit{ideal}",(0.05,90),fontsize=6.6,color=GOOD,ha="left",va="top")
ax.legend(loc="lower left",bbox_to_anchor=(0.02,0.02),handletextpad=0.3,borderpad=0.4)
save(fig,"fig2_quadrant")

# =========== FIG COMPARE : 1x3 (recall / FP / F1) ==========================
fig,axs=plt.subplots(1,3,figsize=(WIDE,2.15))
data=[("Malware recall (\\%)",[h[t]["recall"]*100 for t in tools],(0,100),"{:.0f}"),
      ("False-positive rate (\\%)",[h[t]["fp_rate"]*100 for t in tools],(0,8),"{:.1f}"),
      ("$F_1$ score",[F1[t] for t in tools],(0,1),"{:.3f}")]
tags="abc"
for k,(ax,(ttl,vals,ylim,fmt)) in enumerate(zip(axs,data)):
    sci(ax,cat_axis="x")
    for i,t in enumerate(tools):
        ax.bar(i,vals[i],width=0.66,color=TOOLCOL[t],edgecolor=FRAME,linewidth=0.6,
               hatch=HATCH[t],zorder=3)
        yv=vals[i]; off=(ylim[1]-ylim[0])*0.03
        ax.text(i,yv+off,fmt.format(yv),ha="center",va="bottom",fontsize=6.6,color=INK)
    ax.set_xticks(range(3)); ax.set_xticklabels([t.replace("Q-Trace","Q-T").replace("Semgrep","Sem").replace("Bandit","Ban") for t in tools],fontsize=6.8)
    ax.set_ylim(ylim[0],ylim[1]*1.14 if k<2 else 1.12); ax.set_ylabel(ttl,fontsize=7.6)
    panel(ax,tags[k],dx=-0.30)
save(fig,"fig_compare")

# =========== FIG 5 : confidence separation (single) ========================
grid=D["confidence_grid"]
keys=["Critical|High","High|High","High|Medium","High|Low","None|None"]
labels=[r"Cr$\cdot$Hi",r"Hi$\cdot$Hi",r"Hi$\cdot$Me",r"Hi$\cdot$Lo",r"none"]
mal=[grid.get(k,{}).get("mal",0) for k in keys]; ben=[grid.get(k,{}).get("ben",0) for k in keys]
x=np.arange(len(keys)); w=0.4
fig,ax=plt.subplots(figsize=(COL,2.5)); sci(ax,cat_axis="x")
ax.axvspan(2.5,4.5,color=GOOD,alpha=0.06,lw=0)
ax.bar(x-w/2,mal,w,color=CRIT,edgecolor=FRAME,linewidth=0.6,label="Malicious (31)",zorder=3)
ax.bar(x+w/2,ben,w,color=QT,edgecolor=FRAME,linewidth=0.6,hatch="////",label="Benign (34)",zorder=3)
for xi,m,b in zip(x,mal,ben):
    if m: ax.text(xi-w/2,m+0.5,str(m),ha="center",fontsize=6.3,color=INK)
    if b: ax.text(xi+w/2,b+0.5,str(b),ha="center",fontsize=6.3,color=INK)
ax.axvline(2.5,color=FRAME,lw=0.6,ls=(0,(2,2)),zorder=2)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0,37)
ax.set_ylabel("Number of samples"); ax.set_xlabel(r"Highest (severity$\cdot$confidence) finding")
ax.legend(loc="upper center",bbox_to_anchor=(0.42,1.0),borderpad=0.4)
ax.annotate(r"gate",(1.9,33),fontsize=6.4,color=SEC,ha="center")
ax.annotate(r"silent",(3.5,33),fontsize=6.4,color=SEC,ha="center")
save(fig,"fig5_confidence")

# =========== FIG ABLREFINE : 1x2 (ablation / refinement) ===================
fig,axs=plt.subplots(1,2,figsize=(WIDE,2.35))
# (a) ablation
ax=axs[0]; sci(ax,cat_axis="x")
mets=["Recall","FP rate"]; so=[ab["severity_only"]["recall"]*100,ab["severity_only"]["fp_rate"]*100]
tw=[ab["two_axis"]["recall"]*100,ab["two_axis"]["fp_rate"]*100]; x=np.arange(2); w=0.36
b1=ax.bar(x-w/2,so,w,color="#b9bcc4",edgecolor=FRAME,linewidth=0.6,label="Severity only",zorder=3)
b2=ax.bar(x+w/2,tw,w,color=QT,edgecolor=FRAME,linewidth=0.6,hatch="////",label=r"Sev.$\times$conf.",zorder=3)
for rs in (b1,b2):
    for r in rs: ax.text(r.get_x()+r.get_width()/2,r.get_height()+1.4,f"{r.get_height():.1f}",ha="center",fontsize=6.4)
ax.set_xticks(x); ax.set_xticklabels(mets); ax.set_ylim(0,116); ax.set_ylabel(rf"Percent ({pct})")
ax.legend(loc="upper right",borderpad=0.4); panel(ax,"a",dx=-0.24)
ax.annotate(r"$-5.9$ pt FP",(1,30),fontsize=6.6,color=GOOD,ha="center")
# (b) refinement
ax=axs[1]; sci(ax,cat_axis="x")
groups=[r"CI recall",r"$F_1\!\times\!100$",r"A-dbg FP",r"Dbg det."]
pv=[93.5,96.7,2,0]; nv=[hd["ci_recall"]*100,hd["f1"]*100,0,1]; x=np.arange(4); w=0.36
c1=ax.bar(x-w/2,pv,w,color="#b9bcc4",edgecolor=FRAME,linewidth=0.6,label="Prior",zorder=3)
c2=ax.bar(x+w/2,nv,w,color=AQUA,edgecolor=FRAME,linewidth=0.6,hatch="....",label="Refined",zorder=3)
def fm(v): return f"{v:.1f}" if v>=5 else f"{v:g}"
for xi,p,n in zip(x,pv,nv):
    ax.text(xi-w/2,p+1.5,fm(p),ha="center",fontsize=5.8,color=SEC)
    ax.text(xi+w/2,n+1.5,fm(n),ha="center",fontsize=5.8,color=INK)
ax.set_xticks(x); ax.set_xticklabels(groups,fontsize=6.3); ax.set_ylim(0,110); ax.set_ylabel("Value")
ax.legend(loc="center right",borderpad=0.4); panel(ax,"b",dx=-0.20)
save(fig,"fig_ablrefine")

# =========== FIG 7 : confusion matrix ======================================
cm=np.array([[hd["tp"],hd["fp"]],[hd["fn"],hd["tn"]]]); vmax=cm.max()
fig,ax=plt.subplots(figsize=(COL,2.5)); labs=[["TP","FP"],["FN","TN"]]
for (i,j),v in np.ndenumerate(cm):
    frac=v/vmax; col=RAMP[min(int(frac*(len(RAMP)-1)+0.5),len(RAMP)-1)] if v>0 else "#f4f3f0"
    ax.add_patch(plt.Rectangle((j,1-i),1,1,facecolor=col,edgecolor=FRAME,linewidth=0.6))
    tc="white" if frac>0.5 else INK
    ax.text(j+0.5,1-i+0.60,rf"\textbf{{{v}}}",ha="center",va="center",fontsize=14,color=tc)
    ax.text(j+0.5,1-i+0.30,labs[i][j],ha="center",va="center",fontsize=7.5,color=tc)
ax.set_xlim(0,2); ax.set_ylim(0,2); ax.set_aspect("equal")
ax.set_xticks([0.5,1.5]); ax.set_xticklabels(["Malicious","Benign"]); ax.xaxis.tick_top(); ax.xaxis.set_label_position("top")
ax.set_yticks([1.5,0.5]); ax.set_yticklabels(["Alert","Silent"])
ax.set_xlabel("Ground truth"); ax.set_ylabel("Q-Trace decision")
ax.tick_params(which="both",length=0); [s.set_visible(True) or s.set_color(FRAME) for s in ax.spines.values()]
save(fig,"fig7_confusion")

# =========== FIG 8 : coverage matrix (wide) ================================
cats=D["category_matrix"]; names=list(cats.keys()); n=len(names)
fig,ax=plt.subplots(figsize=(WIDE,0.28*n+0.5))
cell={True:GOOD,False:CRIT,None:"#dedcd5"}
for r,cat in enumerate(names):
    y=n-r-1
    for c,t in enumerate(tools):
        v=cats[cat][t]
        ax.add_patch(plt.Rectangle((c,y),0.92,0.84,facecolor=cell[v],edgecolor="white",linewidth=1.4,
                     alpha=1 if v is not None else 0.65))
        sym=r"$\checkmark$" if v is True else (r"$\times$" if v is False else r"--")
        ax.text(c+0.46,y+0.42,sym,ha="center",va="center",color="white" if v is not None else MUT,fontsize=8.5)
    ax.text(-0.12,y+0.42,cat.replace("_"," ").title(),ha="right",va="center",fontsize=7.4,color=INK)
ax.set_xlim(-3.4,len(tools)); ax.set_ylim(-0.1,n)
ax.set_xticks([c+0.46 for c in range(len(tools))]); ax.set_xticklabels([rf"\textbf{{{t}}}" for t in tools],fontsize=8)
ax.xaxis.tick_top(); ax.set_yticks([]); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
save(fig,"fig8_matrix")

# =========== FIG 9 : latency CDF ===========================================
lat=sorted(D["latency_samples"]); nlat=len(lat)
ys=[100*(i+1)/nlat for i in range(nlat)]
fig,ax=plt.subplots(figsize=(COL,2.3)); sci(ax)
ax.step([0]+lat,[0]+ys,where="post",color=QT,linewidth=1.3,zorder=3)
ax.scatter(lat,ys,s=9,color=QT,zorder=4,edgecolor="white",linewidth=0.3)
med=hd["median_latency_ms"]
ax.axvline(med,color=CRIT,lw=0.9,ls=(0,(3,2)),zorder=2)
ax.annotate(rf"median {med:.1f} ms",(med*1.15,32),color=CRIT,fontsize=6.6,rotation=0)
ax.set_xscale("log"); ax.set_xlim(0.3,60); ax.set_ylim(0,102)
ax.set_xlabel("Full-audit time per sample (ms, log scale)"); ax.set_ylabel(rf"Cumulative ({pct})")
save(fig,"fig9_latency")

# =========== FIG 11 : only-Q (single) ======================================
matrix=D["matrix"]; seen=[]
for row in matrix:
    others=[row["flags"].get(t) for t in tools if t!="Q-Trace"]
    if row["flags"].get("Q-Trace") and all(o in (False,None) for o in others):
        if row["expected"] not in seen: seen.append(row["expected"])
counts={c:sum(1 for r in matrix if r["expected"]==c) for c in seen}
seen=sorted(seen,key=lambda c:counts[c])
fig,ax=plt.subplots(figsize=(COL,2.4)); sci(ax,cat_axis="y")
for i,c in enumerate(seen):
    ax.barh(i,counts[c],color=AQUA,height=0.62,edgecolor=FRAME,linewidth=0.6,zorder=3)
    ax.text(counts[c]+0.05,i,str(counts[c]),va="center",fontsize=6.8,color=INK)
ax.set_yticks(range(len(seen))); ax.set_yticklabels([c.replace("_"," ").title() for c in seen],fontsize=6.9)
ax.set_xlim(0,max(counts.values())+0.8); ax.set_xlabel("Samples flagged only by Q-Trace")
save(fig,"fig11_onlyq")

print("F1",{t:round(F1[t],3) for t in tools}); print("DONE")
