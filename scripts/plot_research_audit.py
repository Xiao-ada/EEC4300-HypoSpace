"""Publication figures for actual free-generation scores; no target thresholds."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/research_audit_v7'
data = json.loads((OUT / 'summary.json').read_text())
methods = ['base_iid', 'balanced_sft_iid', 'canonical_coverage_iid', 'string_coverage_iid']
labels = ['Base LLM', 'Balanced SFT', 'Canonical\ncoverage', 'String\ncoverage']
cohorts = ['known_2var', 'fresh_3var']
titles = ['Known 2-variable tasks: new sampling repetitions', 'Fresh 3-variable tasks: transfer without adaptation']
colors = ['#3b6fa1', '#cd853f', '#3c9279']
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
x = np.arange(4)
for ax, cohort, title in zip(axes, cohorts, titles):
    for j, metric in enumerate(['VR', 'NR', 'RR']):
        values = [100 * data['metrics'][cohort][m][metric] for m in methods]
        bars = ax.bar(x + (j - 1) * .24, values, width=.24, label=metric, color=colors[j])
        ax.bar_label(bars, fmt='%.1f', fontsize=7, padding=2)
    ax.set_xticks(x, labels, fontsize=9)
    ax.set_title(title, fontsize=11, pad=10)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=.15)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].legend(ncol=3, frameon=False)
axes[0].set_ylabel('Macro score (%)')
fig.suptitle('Matched checkpoints, unrestricted generation, fixed 16 attempts per task', fontsize=13)
fig.text(.5, .01, 'No catalog, forced uniqueness, repair or reference-count budget. Two inference seeds; one original training seed.', ha='center', fontsize=9)
fig.tight_layout(rect=(0, .05, 1, .96))
for ext in ['png', 'pdf']:
    fig.savefig(OUT / f'metrics.{ext}', dpi=180, bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
line_colors = ['#777777', '#3b6fa1', '#3c9279', '#cd853f']
for ax, cohort, title in zip(axes, cohorts, titles):
    for method, label, color in zip(methods, labels, line_colors):
        n = [1, 2, 4, 8, 16]
        ax.plot(n, [data['budget_metrics'][cohort][str(k)][method]['RR'] * 100 for k in n],
                marker='o', label=label.replace('\n', ' '), color=color)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('Generation attempts')
    ax.set_ylabel('Macro reference recovery (%)')
    ax.set_xticks([1, 2, 4, 8, 16])
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.15)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
for ext in ['png', 'pdf']:
    fig.savefig(OUT / f'coverage.{ext}', dpi=180, bbox_inches='tight')
plt.close(fig)
print('Wrote metric and budget figures (PNG and PDF)')
