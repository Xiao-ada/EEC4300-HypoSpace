"""Standalone scientific plots, using only exported final experiment data."""
import csv,json
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1].parent/'runtime/mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'results/final';data=json.loads((out/'test/summary.json').read_text())
methods=list(data['metrics']);names={'base_iid':'Base IID','balanced_sft_iid':'Balanced SFT','canonical_coverage_iid':'Canonical coverage','string_coverage_iid':'String coverage','base_memory':'Base + history'}
colors=['#64748b','#2563eb','#16a34a','#9333ea','#d97706']
plt.rcParams.update({'font.size':10,'figure.dpi':150,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(7,4))
for m,c in zip(methods,colors):
 q=sorted(map(int,data['budget_metrics']))
 ax.plot(q,[100*data['budget_metrics'][str(n)][m]['RR'] for n in q],marker='o',label=names[m],color=c)
ax.set(xlabel='Counted generation attempts per task',ylabel='Mean recovery (%)',title='Held-out Boolean tasks: recovery versus budget',ylim=(0,100));ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'coverage.png');fig.savefig(out/'coverage.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4));x=np.arange(len(methods));width=.25
for j,k in enumerate(['VR','NR','RR']):ax.bar(x+(j-1)*width,[100*data['metrics'][m][k] for m in methods],width,label=k)
ax.set_xticks(x,[names[m] for m in methods],rotation=12);ax.set(ylabel='Macro average (%)',title='Validity, structural uniqueness and reference recovery',ylim=(0,100));ax.legend();fig.tight_layout();fig.savefig(out/'metrics.png');fig.savefig(out/'metrics.pdf');plt.close(fig)
comp=data['canonical_vs']['balanced_sft_iid'];delta=list(comp['per_task_RR_difference'].values())
fig,ax=plt.subplots(figsize=(8,3.7));ax.bar(np.arange(1,len(delta)+1),np.array(delta)*100,color=['#16a34a' if d>=0 else '#dc2626' for d in delta]);ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Held-out task index (fixed manifest order)',ylabel='RR difference (percentage points)',title='Canonical coverage minus matched balanced SFT');fig.tight_layout();fig.savefig(out/'paired_differences.png');fig.savefig(out/'paired_differences.pdf');plt.close(fig)
print('Wrote three PNG/PDF figures')
