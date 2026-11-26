"""Create the final reviewable optimization report from verified test results."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from explorer.tasks import write_json
from scripts.report_canonical_decode import paired

OUT=ROOT/'results/canonical_preference_v5'
LABELS={
 'base_iid':'Base IID', 'balanced_sft_iid':'Balanced SFT',
 'canonical_coverage_iid':'Coverage v1', 'string_coverage_iid':'String coverage v1',
 'coverage_continuation_iid':'Coverage +80 / IID',
 'canonical_preference_iid':'Preference +80 / IID',
 'coverage_continuation_bace':'Coverage +80 / BACE',
 'canonical_preference_bace':'Preference +80 / BACE', 'uniform_bace':'Uniform / BACE'}


def percent(x):return f'{100*x:.2f}%'
def pp(x):return f'{100*x:+.2f}'
def ci(row):return '['+', '.join(f'{100*x:+.2f}' for x in row['task_bootstrap_95_interval'])+']'


def main():
    test=json.loads((OUT/'test/summary.json').read_text())
    val=json.loads((OUT/'validation/summary.json').read_text())
    selection=json.loads((OUT/'selection.json').read_text())
    assert json.loads((OUT/'test/verification.json').read_text())['pass']
    stats=test['metrics'];main_method=selection['selected_method']
    preference='canonical_preference_bace'
    candidate=main_method or preference
    s=stats[candidate]
    old=stats['canonical_coverage_iid'];control='coverage_continuation_bace'
    diff=test['comparisons'][preference][control]
    order=['base_iid','balanced_sft_iid','canonical_coverage_iid','coverage_continuation_iid',
           'canonical_preference_iid','coverage_continuation_bace',preference,'uniform_bace']
    table='| Method | Validity | Uniqueness | Recovery |\n|---|---:|---:|---:|\n'+''.join(
        f"| {LABELS[m]} | {percent(stats[m]['VR'])} | {percent(stats[m]['NR'])} | {percent(stats[m]['RR'])} |\n" for m in order)
    decision=('验证规则选定 '+LABELS[main_method]+'；选定方法在测试前冻结。' if main_method else
              '验证阶段没有候选同时满足全部采用条件；保留第一版主方法，新增 BACE 结果作为取舍方案报告。')
    deployment=('实际选用继续覆盖训练 80 步＋BACE；新增偏好项没有通过验证选择，保留为未选用的对照实验。'
                if main_method=='coverage_continuation_bace' else '')
    test_guard=(s['VR']>=old['VR']-.02 and s['RR']>old['RR'] and s['NR']>.8)
    guard_note=('跟进测试仍满足相对第一版的数值保护条件。' if test_guard else
                '跟进测试未维持全部数值保护条件；新增结果应作为指标取舍报告，不称为全面改进，第一版仍保留。')
    own_iid=candidate.removesuffix('_bace')+'_iid' if candidate.endswith('_bace') else None
    secondary={}
    if own_iid:
        with (OUT/'test/episodes.csv').open() as f:
            episodes=[{**r,**{k:float(r[k]) for k in ['VR','NR','RR']}} for r in csv.DictReader(f)]
        ids=json.loads((ROOT/'results/coverage_plan/split_manifest.json').read_text())['splits']['test']
        secondary={m:paired(episodes,candidate,m,ids) for m in [own_iid,'uniform_bace']}
        write_json(OUT/'secondary_selected_comparisons.json',{'label':'Exploratory decoder/learned-proposal attribution; selected model fixed on validation','target':candidate,'comparisons':secondary})
    decoder_note=('同检查点 BACE 相对 IID：Validity '+pp(secondary[own_iid]['VR']['difference'])+
                  '、Uniqueness '+pp(secondary[own_iid]['NR']['difference'])+'、Recovery '+pp(secondary[own_iid]['RR']['difference'])+
                  ' 个百分点。NR 的 95% 区间 '+ci(secondary[own_iid]['NR'])+'，RR 的区间 '+ci(secondary[own_iid]['RR'])+
                  '。这项对照检验解码模块本身，额外训练不能归因给 BACE。' if own_iid else '')
    attribution=('该设置下支持新增偏好损失提供额外合法率收益，但仍是单训练种子的探索性结果。'
                 if diff['VR']['task_bootstrap_95_interval'][0]>0 else
                 '新增偏好损失相对匹配继续训练的额外合法率优势尚未获得清晰支持。')
    chinese=f'''# README 参考指标优化：最终对比

本次优化以官方 README 的 Uniqueness >80% 为主要接近目标，同时公开 Validity >90%、Recovery >80% 的差距。参考值不是课程评分线。

{decision}

{deployment} {guard_note}

## 正式跟进测试

与第一版相同的 26 道 Boolean 题、三个推理种子 17/29/43、每题 16 次尝试。题目、提示文本、基础模型、温度、采样器和评分方法一致。原始模型结果保留；本次测试集合此前已在第一版报告，因此这是探索性跟进，不是全新未见的确认集。

{table}

验证阶段选定组合 **{LABELS[candidate]}** 相对第一版覆盖模型：Validity {pp(s['VR']-old['VR'])}、Uniqueness {pp(s['NR']-old['NR'])}、Recovery {pp(s['RR']-old['RR'])} 个百分点。新增偏好损失是否采用，以验证记录为准；不能根据测试结果反向更换选择。

对照额外训练和解码后，新偏好损失相对 Coverage +80 / BACE：Validity {pp(diff['VR']['difference'])} 个百分点，按题配对 bootstrap 95% 区间 {ci(diff['VR'])}；Recovery {pp(diff['RR']['difference'])} 个百分点，区间 {ci(diff['RR'])}。{attribution}区间未做次要多重比较校正，不能推广到所有模型或训练种子。

{decoder_note}

## 改了什么

1. **训练端：结构类别偏好学习。** 在原有 16 道训练题的 143 组正例上构造恰好违反一条观测的负例，尽量匹配长度。用两个同结构写法的完整序列概率之和构造 DPO 风格偏好损失。保留同起点、同数据、同更新数的继续训练对照，两组各加 80 步；基础权重冻结。
2. **推理端：BACE。** 先正常采样；当再重复一次就无法在剩余预算内凑齐 13 个不同结构时，使用语法 trie 排除已见结构的所有等价写法。13/16=81.25%，超过 80% 指引。它不通过检查观测答案来筛选生成结果。

不重复率保证来自解码约束，不能归功于模型已经学会多样性。训练模块的独立作用看同一解码策略下的匹配对照；第一版覆盖损失相对普通 SFT 的额外恢复率贡献也不能被这次结果追溯证明。

## 官方参考值与取舍

| 指标 | {LABELS[candidate]} | README 参考 | 超过参考值 |
|---|---:|---:|---|
| Validity | {percent(s['VR'])} | >90% | {'是' if s['VR']>.9 else '否'} |
| Uniqueness | {percent(s['NR'])} | >80% | {'是' if s['NR']>.8 else '否'} |
| Recovery | {percent(s['RR'])} | >80% | {'是' if s['RR']>.8 else '否'} |

在每题 16 次输出、合法结构数量较少时，提高不重复率可能需要更多错误输出。对 v2 完全语法池的分析显示：其宏平均 Validity 若至少 90%，宏平均 Uniqueness 的一个上界为 66.73%，因而三条指引在那个具体有限支持设置下不能同时满足。这个界仅适用于完全使用该语法池的解码器，不覆盖任意自由文本或其他任务规模。应结合观测、预算和参考空间大小解释指标。

## 预算、证据和实现检查

- 新增训练、验证和测试轨迹均独立保存，没有覆盖原始检查点或 6720 次第一版正式生成。
- 测试中新实际模型生成 {test['counts']['new_model_calls']} 次，复用同一新检查点的 IID 前缀 {test['counts']['replayed_model_calls']} 次，均匀控制 {test['counts']['uniform_draws']} 次。复用前缀仍计入每个策略的 16 次逻辑预算、token 与耗时。
- 原始输出逐条用第一版评分器重新打分，验证 prompt 一致、缓存前缀一致、排重状态及指标。见 `results/canonical_preference_v5/test/verification.json`。
- 模型训练仅修改 311,296 个 LoRA 参数。响应位置词表投影经过实际量化模型损失/梯度对照；资源探针额外完成 14 次更新并被单独记录，两组最终训练重新从同一第一版检查点起步。
- 原始报告包含全部两组训练、两种采样和均匀控制。验证选定记录在测试前保存，最终不根据测试挑选超参数或隐藏失败方案。

## 未采用的尝试

始终排除结构、观测/无观测概率对比、延迟排除这三个仅解码的验证试验均公开。前两个方案会明显降低合法率；延迟排除虽达到 81.25% 不重复率，验证合法率仍下降 6.25 个百分点。它们不能单独被称为全面改进，促使本轮加入观察约束负例训练。

## 创新边界与课程要求

本轮是对课程要求“设计 ML 方法改善 HypoSpace”的任务特定尝试：训练阶段利用观测错误的结构类别对，推理阶段在有限预算下控制结构重复。DPO、LoRA、语法约束和无放回抽样都有已有研究，不能宣称全球首创。独立贡献的证据应来自匹配对照，而非方法名称或单个较高数字。

仍局限于两变量、深度 2 的 Boolean 子集；只有一个训练种子。没有与组员的模型、题目及修复调用预算对齐，不能用截图直接排名。10 次的曲线点是按 16 次总预算设计的策略前缀，不能当作 BACE 在总预算 10 下重新运行的成绩。课程视频仍需成员自己参与录制。

## 文件与复现

- [训练理论与数据](CANONICAL_PREFERENCE.md)、[BACE 原理与保证](BACE_METHOD.md)。
- [机器可读测试汇总](../results/canonical_preference_v5/test/summary.json)、[逐题结果](../results/canonical_preference_v5/test/episodes.csv)、[原始证据](../results/canonical_preference_v5/test/evidence.jsonl.gz)。
- [训练协议](../results/canonical_preference_v5/protocol.json)、[新增损失分析计划](../results/canonical_preference_v5/analysis_plan.json)、[验证选择](../results/canonical_preference_v5/selection.json)。
- [指标图](../results/canonical_preference_v5/metrics.png)、[恢复率曲线](../results/canonical_preference_v5/coverage.png)。

运行环境、固定基础模型和第一版恢复步骤见根 README。训练与评分命令见方法文档。CPU 复核已发布原始证据可运行 `.venv/bin/python scripts/verify_optimization.py`，无需模型推理。
'''
    (ROOT/'docs/OPTIMIZATION_RESULTS_ZH.md').write_text(chinese)
    english=f'''# Optimization follow-up results

{table}

Validation-selected deployment: **{LABELS[candidate]}**. The added preference loss was {'selected' if selection['new_preference_term_selected'] else 'not selected'} on validation. Test metrics do not change that selection.

Same 26 Boolean observation tasks, three inference seeds, and 16 counted attempts. These task observations were reported in v1; this is an exploratory follow-up, not an untouched confirmation set. The new preference and continuation arms each add 80 matched updates from the same v1 coverage checkpoint.

Preference+BACE versus matched continuation+BACE: validity difference {pp(diff['VR']['difference'])} percentage points, task-bootstrap 95% interval {ci(diff['VR'])}; recovery difference {pp(diff['RR']['difference'])}, interval {ci(diff['RR'])}. One training seed; secondary intervals are not multiplicity-adjusted.

Uniqueness comes from a decoding guarantee, not proof of learned diversity. BACE keeps IID sampling until another duplicate would make 13 distinct structures unreachable at N=16. Class exclusions then block every represented alias. The observation-violating negative pairs target validity during training. Both components require their respective controls.

README guides (>90% validity, >80% uniqueness, >80% recovery) are setting-dependent diagnostic references, not course marks. The system's remaining gaps are disclosed above. Selection was frozen on validation before test; all arms are published.

See [full discussion](OPTIMIZATION_RESULTS_ZH.md), [training method](CANONICAL_PREFERENCE.md), [decoding method](BACE_METHOD.md), and [raw evidence](../results/canonical_preference_v5/test/evidence.jsonl.gz).
'''
    (ROOT/'docs/OPTIMIZATION_RESULTS_EN.md').write_text(english)
    banner=f'''<!-- OPTIMIZATION_UPDATE_BEGIN -->
## README 参考指标优化：新增实测结果

新增结构类别偏好训练对照与 BACE 预算控制，原始结果完整保留。**验证选定的 {LABELS[candidate]}：VR {percent(s['VR'])}、NR {percent(s['NR'])}、RR {percent(s['RR'])}**。不重复率超过 README 的 >80% 指引；其余指标以实际表格为准，不能据此宣称三项全面达标或课程高分。

{decision}

{deployment} {guard_note}

{decoder_note}

{table}

两组新训练各增加 80 步，同起点、同数据、同预算。完整跟进测试仍是 26 题×3 种子×16 次，沿用第一版评分方式；已见过这些测试观测，因此结果属于探索性跟进。

**新增损失相对同解码的匹配继续训练：VR {pp(diff['VR']['difference'])} 个百分点，95% 区间 {ci(diff['VR'])}。** {attribution}

[详细中文报告](docs/OPTIMIZATION_RESULTS_ZH.md) · [English results](docs/OPTIMIZATION_RESULTS_EN.md) · [训练原理](docs/CANONICAL_PREFERENCE.md) · [BACE 原理](docs/BACE_METHOD.md) · [原始对比数据](results/canonical_preference_v5/test/summary.json)

![Optimization metrics](results/canonical_preference_v5/metrics.png)

旧版演示稿和下方原始表报告第一版；讲解新增优化请使用本节和新增报告。

新增复核与复用：

```bash
.venv/bin/python scripts/verify_optimization.py
.venv/bin/python scripts/restore_preference_adapters.py
# 完成下方 Apple Silicon 固定模型环境后，可重新生成新适配器的验证结果：
../runtime/mlx-env/bin/python -m explorer.preference_experiment validation
```

[新版英文两页展示与两分钟讲稿](docs/BACE_PRESENTATION_EN.md) · [新版组内对齐配置](results/optimization_group_packet.json)。模型对合法覆盖的作用与强制唯一率分开检验，完整数据包含无 LLM 均匀控制。
<!-- OPTIMIZATION_UPDATE_END -->

'''
    readme=(ROOT/'README.md').read_text()
    readme=readme.replace('**完整训练、验证与固定测试已完成。全部数字来自真实模型输出。**','**第一版训练、验证与固定测试已完成。该段概述指第一版；新增优化见下节。**')
    readme='\n'.join(line for line in readme.split('\n') if not line.startswith('> **README 指标优化实验进行中'))
    if '<!-- OPTIMIZATION_UPDATE_BEGIN -->' in readme:
        start=readme.index('<!-- OPTIMIZATION_UPDATE_BEGIN -->');end=readme.index('<!-- OPTIMIZATION_UPDATE_END -->')+len('<!-- OPTIMIZATION_UPDATE_END -->')
        readme=readme[:start]+banner+readme[end:]
    else:
        readme=readme.replace('## 最终测试结果',banner+'## 第一版测试结果（保留）',1)
    (ROOT/'README.md').write_text(readme)
    for arm in ['coverage_continuation','canonical_preference']:
        dest=ROOT/'artifacts/preference_adapters'/arm;dest.mkdir(parents=True,exist_ok=True)
        for name in ['adapters.safetensors','adapter_config.json']:
            source=ROOT/'runs/canonical_preference_v5/adapters'/arm/name
            shutil.copyfile(source,dest/name)
    write_json(ROOT/'artifacts/preference_adapters/manifest.json',{
        'base_model_lock':'model.local_mlx.lock.json','initial_adapter':'v1 canonical_coverage',
        'new_updates_per_arm':80,'training_summary':json.loads((OUT/'training_summary.json').read_text()),
        'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/preference_adapters').rglob('*') if p.is_file() and p.suffix in ['.safetensors','.json'] and p.name!='manifest.json'}})
    campaign={'v2_grammar_pilot':json.loads((ROOT/'results/canonical_decode_v2/validation/summary.json').read_text()),
              'v3_guidance_pilot':json.loads((ROOT/'results/contrastive_decode_v3/summary.json').read_text()),
              'v4_budget_pilot':json.loads((ROOT/'results/target_decode_v4/validation/summary.json').read_text()),
              'v5_selection':selection,'v5_test_summary':'results/canonical_preference_v5/test/summary.json',
              'startup_generation_errors':1,'resource_probe':json.loads((OUT/'resource_probe.json').read_text()),
              'all_v1_results_preserved':True}
    write_json(ROOT/'results/optimization_campaign.json',campaign)
    plot(test,order,candidate)
    print(json.dumps({'report':'docs/OPTIMIZATION_RESULTS_ZH.md','validation_selected_method':main_method,'recommended_metrics':s,'primary_validity_comparison':diff['VR']},indent=2))


def plot(test,order,highlight):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    stats=test['metrics']
    labels=[LABELS[m] for m in order]
    fig,axes=plt.subplots(1,3,figsize=(13,5.8),sharey=True)
    for ax,metric,guide,title in zip(axes,['VR','NR','RR'],[90,80,80],['Validity','Uniqueness','Recovery']):
        values=[stats[m][metric]*100 for m in order]
        colors=['#245f9e' if m==highlight else '#83b0ce' if m.startswith('canonical_preference') else '#b9c2cd' for m in order]
        ax.barh(np.arange(len(order)),values,color=colors)
        ax.axvline(guide,color='#a54435',ls='--',lw=1)
        for y,v in enumerate(values):ax.text(min(v+1.2,95),y,f'{v:.1f}',va='center',fontsize=8)
        ax.set_title(title);ax.set_xlim(0,103);ax.set_xlabel('Percent')
        ax.set_yticks(range(len(order)))
        if ax is axes[0]:ax.set_yticklabels(labels)
        else:ax.tick_params(axis='y',labelleft=False)
        ax.spines[['top','right']].set_visible(False)
    axes[0].invert_yaxis()
    fig.suptitle('26 Boolean tasks / 3 inference seeds / 16 counted attempts',fontsize=13)
    fig.text(.5,.015,'Dashed lines: setting-dependent README guides. Exploratory follow-up; one training seed.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.94])
    for ext in ['png','pdf']:fig.savefig(OUT/f'metrics.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    with (OUT/'test/curves.csv').open() as f:rows=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(7.5,4.8))
    for method in ['coverage_continuation_iid','canonical_preference_iid','coverage_continuation_bace','canonical_preference_bace','uniform_bace']:
        y=[100*np.mean([float(r['RR']) for r in rows if r['method']==method and int(r['queries'])==n]) for n in range(1,17)]
        ax.plot(range(1,17),y,label=LABELS[method],lw=2 if method==highlight else 1.4)
    ax.set(xlabel='Counted proposals (policy planned for total N=16)',ylabel='Recovery (%)',xlim=(1,16),ylim=(0,100))
    ax.axhline(80,ls='--',color='#a54435',lw=1,label='README recovery guide')
    ax.legend(fontsize=8);ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(OUT/f'coverage.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':main()
