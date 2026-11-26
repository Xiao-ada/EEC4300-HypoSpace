"""Render current research claims from the complete, independently checked audit."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/research_audit_v7'
s = json.loads((OUT / 'summary.json').read_text())
p = json.loads((OUT / 'protocol.json').read_text())
c = json.loads((OUT / 'costs.json').read_text())
v = json.loads((OUT / 'verification.json').read_text())
assert v['pass'] and s['calls'] == 4864
names = {'base_iid': 'Base LLM', 'balanced_sft_iid': 'Balanced SFT',
         'canonical_coverage_iid': 'Canonical Coverage', 'string_coverage_iid': 'String Coverage'}


def table(cohort):
    lines = ['| Method | VR | NR | RR | Recovered classes / task |', '|---|---:|---:|---:|---:|']
    for method in p['methods']:
        m = s['metrics'][cohort][method]
        lines.append(f'| {names[method]} | {m["VR"]*100:.2f}% | {m["NR"]*100:.2f}% | {m["RR"]*100:.2f}% | {m["recovered"]:.2f} |')
    return '\n'.join(lines)


def interpretation(cohort):
    item = s['comparisons'][cohort]['balanced_sft_iid']['RR']
    delta = item['difference_pp']
    lo, hi = item['task_bootstrap_95_interval_pp']
    if lo > 0:
        zh = '本轮在这一固定设置下有额外恢复率改善的正向证据；只有一个训练种子，不能外推为稳定全面优势。'
        en = 'This replication provides positive within-setting evidence of additional recovery, with only one training seed and no claim of broad superiority.'
    elif hi < 0:
        zh = '本轮覆盖模型的恢复率低于匹配SFT，不能声称该新增目标胜出。'
        en = 'Coverage recovery is lower than matched SFT in this audit; the added objective is not a winning result.'
    else:
        zh = '区间跨零，本轮未证实覆盖目标相对匹配SFT的额外恢复率收益；这也不是两者等效的证明。'
        en = 'The interval crosses zero: additional recovery over matched SFT is not established, which also does not prove equivalence.'
    return f'{delta:+.2f} pp, 95% CI [{lo:+.2f}, {hi:+.2f}] pp', zh, en


primary, claim_zh, claim_en = interpretation('known_2var')
transfer, transfer_zh, transfer_en = interpretation('fresh_3var')
common = '''
| 项目 | 本轮规则 |
|---|---|
| 推理 | 每题16次自由自回归生成，温度1、top-p 1、最多128输出token |
| 方法 | 原始模型＋三个原200步匹配训练检查点，不根据新测试重新选择 |
| 输入 | 只有给定观测和规则，没有参考答案成员、真实K、候选目录或历史答案 |
| 输出 | 不强制去重、不修复、不拒绝重采样；重复和无效回答均计入16次 |
| 数据 | 26道已知两变量题的新采样重复；另有12道新三变量迁移题 |
| 不确定性 | 两个推理种子，先按题平均，再配对bootstrap；只有一个训练种子 |
'''

zh = f'''# 固定预算自由生成：重新测试结果

本轮不追求超过某个指标阈值，而是检验原有训练方法的收益和边界。事前协议已在任何新增输出之前固定为提交 `f6ab465`，四组共完成 **4,864次全新LLM生成**，没有使用历史输出重放。

## 1. 主实验：已知两变量题的新采样重复

26道观测题仍是原测试集合；两个推理种子18617、28657为新增采样随机性，不是新训练或全新未见数据。所有模型均使用统一修正过格式问题的相同提示，因此不要把本表与原提示下的旧表直接拼接。

{table('known_2var')}

**事前主要比较：Canonical Coverage减Balanced SFT的RR@16为 {primary}。{claim_zh}**

原始模型与适配器之间的改善包含普通监督微调的收益，不能全部归功于覆盖项。字符串覆盖消融也完整展示，不按最好的指标改选主方法。

## 2. 新三变量迁移题

12道题由固定哈希从官方深度2布尔语法派生观测集合中选出，每个观测数1/2/3各4道。在选择之前没有运行这些题的模型实验；检查点不做迁移训练。参考空间125类，其中91类不在原两变量空间中。它是本项目扩展的任务规则测试，不是论文发布模型分数的复现。

{table('fresh_3var')}

覆盖模型相对SFT的迁移RR差为 **{transfer}**。{transfer_zh} 这是次要迁移分析，不能替代主要比较；两种变量数的成绩不混合。

三变量题参考解集大小6–71，固定16次只能覆盖其中有限部分。保留原始RR分母，不重新归一化为更高的“达标率”。12道题中只有1道必须使用原空间之外的结构，其余题也允许旧结构作为部分合法答案，因此这不是全面的未见结构泛化证明。新旧结构命中另有事后诊断，不能替换主要指标。

## 3. 从主结论中移除了什么

{common}

此前的COVE从33类目录选择，执行器单独使用也达到同分；其99%不能证明LLM原生生成达到99%。此前BACE的唯一率目标由解码规则保证，也不能算模型学到多样性的证据。二者作为历史补充保留，相关结果、未选用的偏好训练和精确求解对照均未删除。

训练本身仍可使用原训练题的合法参考表达式，这属于监督信号；测试提议不读取参考集合。模型runner与评分器分开，后者在全部生成完成后才解析原文。

## 4. 为什么仍是有价值的课程研究

核心设计是将完整回答按官方结构类别聚合概率，再优化有限预算期望覆盖代理。它有与评估指标相关的数学解释，与普通SFT和字符串目标存在形式区别。价值来自任务相关设计和匹配实验，而不是给方法起名或跨过80%。

若主要比较没有胜出，应报告所测试设置中的局限，并分析有限别名概率、与SFT梯度同向以及训练规模的影响。当前结果只支持表中范围，不证明全球首创、跨任务优势或所有训练种子都有效。详见[研究定位](RESEARCH_POSITIONING_ZH.md)和[方法](METHOD.md)。

## 5. 成本与核验

新增生成 **{c['actual_new_generation_calls']:,}次**；重放0次、候选评分0次、修复0次。生成累计 **{c['generation_seconds']/60:.2f}分钟**，共享前缀处理另计 **{c['prefix_prefill_seconds']:.2f}秒**。这些是运行计时，不包含之前的训练、准备、评分和文档时间。相同输出上限不代表严格相同FLOPs，因为实际回答长度不同。

全部{v['outputs_rescored']:,}条输出、304个完整episode、指标及配对区间通过独立CPU核验；新题固定哈希选择也重新生成比对。原代码和适配器哈希保持一致。

上游枚举与校验仍存在差异：两变量有1个、三变量有3个参考代表写法被空间校验拒绝；这不等于整个类别必然不可达。参考分母不改，所有组使用相同解析/空间门控。参考外校验通过项单列在诊断文件中，主要RR不会给这些项加分。绝对成绩不能直接与论文榜单比较。

## 6. 交付与入口

- [冻结协议](../results/research_audit_v7/protocol.json)与[选题和解释规则](RESEARCH_AUDIT_PROTOCOL_ZH.md)。
- [完整汇总及全部比较](../results/research_audit_v7/summary.json)、[逐题结果](../results/research_audit_v7/episodes.json)。
- [完整压缩输出](../results/research_audit_v7/evidence.jsonl.gz)、[独立核验](../results/research_audit_v7/verification.json)、[成本](../results/research_audit_v7/costs.json)。
- [评分差异诊断](../results/research_audit_v7/scoring_diagnostics.json)、[原始参考写法诊断](../results/research_audit_v7/reference_representation_audit.json)。

CPU复核：`.venv/bin/python scripts/verify_research_audit.py`。小组10分钟视频仍需成员实际参与录制，本研究结果不保证课程分数。

![Fixed budget metrics](../results/research_audit_v7/metrics.png)

![Recovery versus budget](../results/research_audit_v7/coverage.png)
'''
(ROOT / 'docs/RESEARCH_RESULTS_ZH.md').write_text(zh)

en = f'''# Fixed-budget free-generation audit

The revised project tests a task-specific coverage objective, without a minimum score target. The protocol was frozen before new outputs in commit `f6ab465`. Four methods produce **4,864 genuine new LLM responses**, with no replay, candidate catalog, forced uniqueness, rejection sampling or repair.

## Known two-variable tasks: fresh sampling repetitions

All original matched 200-update checkpoints are retained: 80 shared SFT warmup updates plus 120 branch updates. No new checkpoint selection or training occurs. The 26 observation tasks were previously used; only sampling randomness is fresh, with seeds 18617/28657. Common prompt formatting defects are corrected for all arms, so these scores must not be spliced into the old-prompt table.

{table('known_2var')}

**Primary predeclared comparison, canonical coverage minus matched SFT RR@16: {primary}. {claim_en}** Base-relative improvement cannot all be attributed to the new coverage term. The string-coverage ablation remains visible regardless of which column looks better.

## Fresh three-variable transfer tasks

Twelve observation tasks are selected by a fixed salted hash before any model runs: four each with one, two or three observations. The official depth-2 Boolean grammar is used to derive this project extension. Its 125 structural classes include 91 absent from the two-variable space. Models receive no transfer adaptation. Only one selected task strictly requires a class absent from the old space; the others also allow old structures as some valid answers. This is an expanded-input transfer check, not comprehensive unseen-family generalization.

{table('fresh_3var')}

Coverage minus SFT transfer RR is **{transfer}**. {transfer_en} Transfer is secondary, and its scores are not combined with the known-task replication. Reference-set sizes range from 6 to 71; the fixed 16-output budget naturally limits recovery. Full denominators remain unchanged.

## Attribution and limits

Generation reads only public observations, task rules and a common prompt. It never opens the separate reference file or receives K. All16 attempts count. Unchanged parsing/space/observation checks are applied only by the offline scorer after generation.

The original coverage objective pools complete-answer probabilities by official structural class and applies a finite-budget hit objective alongside SFT. Its finite-alias expected-coverage interpretation is a task-specific formulation, not a claim to invent LoRA or coverage probability. Extra benefit over SFT is judged using the predeclared comparison, with negative or inconclusive results retained.

Earlier COVE catalog scores are supplementary: removing the LLM matches its result, and the finite catalog simplifies generation. Earlier BACE uniqueness is enforced by structured decoding and is not learned diversity. Their evidence and unsuccessful preference-training controls remain archived; they do not become the main evidence of improved unrestricted LLM ability.

Only one original training seed exists. Two inference seeds are averaged within each task before 10,000 paired task-bootstrap resamples. Secondary intervals are exploratory. Shared formal structure and previously used two-variable observations restrict external validity. This is not an untouched in-domain confirmation set or a reproduction of the paper's model leaderboard.

The upstream representative spelling audit finds 1 rejected two-variable and 3 rejected three-variable references; this does not prove those entire classes unreachable. All reference denominators stay intact. Out-of-reference validity artifacts are exposed separately and earn no recovery credit. The common fail-closed gate differs slightly from the monolithic upstream runner.

## Cost and reproducibility

New free generations: **{c['actual_new_generation_calls']:,}**; replay 0, candidate scoring 0, repair 0. Summed generation time is **{c['generation_seconds']/60:.2f} minutes**, plus **{c['prefix_prefill_seconds']:.2f} seconds** for shared prompt prefills, excluding prior training and preparation/reporting. Equal output caps do not imply equal FLOPs because completion lengths differ.

CPU verification re-scores all 4,864 outputs and 304 episodes, recomputes metrics/intervals, regenerates the selected task set, and checks frozen source/adapter hashes. Run `.venv/bin/python scripts/verify_research_audit.py`.

See [frozen protocol](../results/research_audit_v7/protocol.json), [raw outputs](../results/research_audit_v7/evidence.jsonl.gz), [all comparisons](../results/research_audit_v7/summary.json), [verification](../results/research_audit_v7/verification.json), and [method](METHOD.md). The course's group video still requires actual member participation; this study does not guarantee a grade.

![Metrics](../results/research_audit_v7/metrics.png)

![Coverage](../results/research_audit_v7/coverage.png)
'''
(ROOT / 'docs/RESEARCH_RESULTS_EN.md').write_text(en)

readme = f'''# Canonical Coverage LoRA for HypoSpace

本项目在Mac上研究：**按HypoSpace官方结构类别设计覆盖训练目标，能否改善LLM在固定采样预算下的合法假设恢复？** 目前以自由生成、匹配训练对照和泛化边界为主线，不以跨过某个指标阈值作为研究成功标准。

The project evaluates a task-specific structural-coverage LoRA objective against matched SFT using unrestricted generation. Strong catalog-selection scores are supplementary, not claims of native LLM capability.

[中文完整结果](docs/RESEARCH_RESULTS_ZH.md) · [English results](docs/RESEARCH_RESULTS_EN.md) · [研究定位](docs/RESEARCH_POSITIONING_ZH.md) · [方法与文献](docs/METHOD.md) · [事前实验协议](docs/RESEARCH_AUDIT_PROTOCOL_ZH.md)

## 当前主结果：固定16次自由生成

四组均使用相同任务提示、采样器和预算。三个适配器均由80步共享SFT预热加120步分支训练得到，原始模型不微调。新增测试不再训练或按成绩选择检查点。基础模型为固定四比特Qwen2.5-1.5B-Instruct，原训练种子只有一个。

**两变量：26道原测试观测题，新增两个采样种子。观测题已经使用过，不是全新测试集。**

{table('known_2var')}

**主要RR差（Coverage−SFT）：{primary}。{claim_zh}**

**三变量：12道运行前固定哈希选出的新迁移题，不适配模型。**

{table('fresh_3var')}

迁移RR差：{transfer}。{transfer_zh}

所有输出均保留，包括无效和重复回答。生成不读取参考答案、真实K、历史回答或固定目录，不强制唯一、不修复。参考空间大小变化会影响RR，两种变量数不混合统计；三变量题不是论文全部任务的复现。

![Free-generation metrics](results/research_audit_v7/metrics.png)

## 方法与独立贡献

对训练题的每个合法结构类k，将固定有限合法写法A_k的完整回答概率聚合：

```text
q_k = sum_{{y in A_k}} P_theta(y | O)       # includes EOS
C_16 = (1/K) * sum_k [1 - (1-q_k)^16]
L = balanced_SFT - C_16
```

该有限写法目标在相应独立采样条件下与期望参考覆盖下界相关。测试时从完整词表自由生成，并不从训练答案库选择。普通SFT和字符串覆盖与主方法使用相同数据、训练路径和优化设置。

任务相关的结构对齐、目标实现和受控实验是本项目贡献；覆盖概率恒等式、LoRA和多样性训练思想不是本项目首创。原始模型到微调模型的全部提升不能归因给新增覆盖项。与同组DCHG不同，本方法不选择未观测位置或指定预测差异。

## 本轮修改了哪些容易误解的部分

- 主实验只报告固定16次自由生成，不用N=K的目录选择结果宣称LLM达到99%。
- 不使用BACE的13/16唯一率保证来证明模型学到了多样性。
- 使用原200步匹配检查点，不将额外训练80步的结果直接归因于新损失。
- 所有方法和负结果保留；主要比较在新输出前固定，不挑好看的指标或种子。
- 两变量重复采样与新三变量迁移分开报告；推理种子与训练种子分开说明。

旧实验是有条件的辅助研究，未被认定为伪造。它们仍可用于理解结构约束和学习执行器，但作用边界必须明确。

## 证据与复核

本轮完成**4,864次全新真实LLM生成**，零重放、零候选评分、零修复；全部输出与304个episode通过独立CPU重算。配对区间按题计算，只有一个训练种子，不包含训练不确定性。

共同评分保留官方完整参考分母，并增加一致的先行解析/空间拒绝门控。上游枚举和校验有已披露差异；所有方法同口径，参考外命中不计RR，不与论文绝对分数直接排名。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/verify_research_audit.py
```

核验不调用LLM或付费API；自动取得校验过的上游源码。关键文件：

- [冻结协议与哈希](results/research_audit_v7/protocol.json)、[模型公开输入](results/research_audit_v7/public_tasks.json)。
- [实际汇总](results/research_audit_v7/summary.json)、[逐题结果](results/research_audit_v7/episodes.json)、[完整压缩输出](results/research_audit_v7/evidence.jsonl.gz)。
- [独立核验](results/research_audit_v7/verification.json)、[成本账本](results/research_audit_v7/costs.json)、[评分诊断](results/research_audit_v7/scoring_diagnostics.json)。
- [模型runner](explorer/research_audit.py)、[公开输入与独立参考文件准备](explorer/research_audit_data.py)。

## 在Apple Silicon上重新推理

基础环境与模型锁见requirements-mlx-lock.txt、model.local_mlx.lock.json。模型约869MB，不在仓库中；原训练得到的LoRA适配器已经公开。建议使用新克隆，保留附带结果后重新执行：

```bash
python3.12 -m venv ../runtime/mlx-env
../runtime/mlx-env/bin/python -m pip install -r requirements-mlx-lock.txt
../runtime/mlx-env/bin/python -m explorer fetch
../runtime/mlx-env/bin/python -m explorer prepare
HF_HOME=../runtime/hf-cache ../runtime/mlx-env/bin/python scripts/local_mlx.py --download-only
mv results/research_audit_v7 .cache/research-audit-published
../runtime/mlx-env/bin/python -m explorer.research_audit_data
../runtime/mlx-env/bin/python -m explorer.research_audit
../runtime/mlx-env/bin/python scripts/report_research_audit.py
../runtime/mlx-env/bin/python scripts/verify_research_audit.py
../runtime/mlx-env/bin/python scripts/plot_research_audit.py
../runtime/mlx-env/bin/python scripts/write_research_docs.py
```

本轮直接读取公开的原版适配器，不必恢复旧运行目录。不同芯片和库版本不保证随机输出逐位一致。完整原版训练流程见[固定历史说明](https://github.com/Xiao-ada/EEC4300-HypoSpace/blob/fdb968e659545626e3275679d965ae29e1c408a5/README.md)；新实验不重写原训练日志。

## 历史研究与封存

- [第一版方法与结果](docs/RESULTS_EN.md)：覆盖目标相对匹配SFT的额外恢复率优势未证实。
- [BACE跟进](docs/OPTIMIZATION_RESULTS_ZH.md)：固定预算结构排重的收益与合法率代价；唯一率保证来自规则。
- [COVE目录选择](docs/ALL80_RESULTS_ZH.md)：受限系统的高指标；执行器单独使用与LLM组合同分，LLM额外价值未证实。
- [原贡献审查](docs/CONTRIBUTION_AUDIT_ZH.md)：原理论性质和探索性分析。

原BACE完整只读本地备份已交付用户，提交fdb968e；COVE版本用标签`cove-exploration-9215146`保留。私有完整模型/环境归档不进入GitHub。历史演示稿不能替代本轮结果表。

## 课程交付与研究边界

老师Part1.2要求新颖ML方法改善HypoSpace上的LLM表现，按novelty、importance、quality评分，提交公开GitHub和10分钟小组视频，每位成员参与、全组同分。README参考指标不是课程合格线，研究可以得到不显著或负向结果。

源码、原始记录、模型适配器、对照、方法与复核已提供；实际小组视频仍需成员录制。同组实验未对齐模型、题目和预算，暂不直接排名。项目范围较小、训练种子单一，不能保证课程分数或推广到全HypoSpace。

代码MIT；适配器及基础模型许可见NOTICE.md及artifacts/adapters/。禁止将.env、完整基础模型、环境、私有运行、账户信息或校内制度文件上传到公开仓库。
'''
(ROOT / 'README.md').write_text(readme)
a = s['metrics']['known_2var']['canonical_coverage_iid']['RR'] * 100
b = s['metrics']['known_2var']['balanced_sft_iid']['RR'] * 100
d = s['primary']['difference_pp']
lo, hi = s['primary']['task_bootstrap_95_interval_pp']
spoken_conclusion = ('The interval crosses zero, so the additional recovery benefit is not established.'
                     if lo <= 0 <= hi else 'The result is limited to this setting and one training seed.')
speech = f'''I study whether coverage-aware training helps LLMs recover more compatible structural hypotheses within sixteen generations.

I pool complete-answer probabilities by HypoSpace's structural classes and add a finite-budget coverage term to SFT. LoRA implements adaptation; it is not the innovation claim.

Ordinary SFT, structural coverage and string coverage share training data and budgets. The unadapted model is another baseline.

Our new audit uses unrestricted generation, without a candidate catalog, forced deduplication, repair or reference-count budget.

On twenty-six previously used observation tasks with new sampling seeds, structural coverage achieves {a:.2f} percent recovery, compared with {b:.2f} percent for matched SFT. The difference is {d:+.2f} percentage points, with a task-bootstrap interval from {lo:+.2f} to {hi:+.2f}. {spoken_conclusion}

We also test twelve new three-variable tasks without adaptation. This is a limited transfer check, not comprehensive unseen-structure generalization.

My contribution is the task-aligned objective and controlled, reproducible evaluation. Only one training seed exists. Inconclusive results are retained; the earlier high-scoring catalog system remains supplementary.'''
presentation = f'''# Current English outline: two slides, about two minutes

This is slide content and speaker notes, not an updated PPTX or a recorded video. The speech has {len(speech.split())} whitespace-separated words; rehearse for the actual duration.

## Slide 1 — Does coverage-aware training help free generation?

- HypoSpace: several compatible structural hypotheses, not a single correct answer.
- Pool verified complete-answer probabilities within official structural classes.
- Objective: `balanced SFT − mean_k[1−(1−q_k)^16]`.
- Matched training: shared 80-step warmup, 120 branch updates; ordinary SFT and string-coverage controls.
- Research question: additional recovery over matched SFT at a fixed 16-generation budget.

The coverage identity and LoRA are established tools; novelty is the task-specific formulation and evaluation. References: [HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html), [LoRA](https://arxiv.org/abs/2106.09685). See [method](METHOD.md) for the finite-alias assumptions and related work.

## Slide 2 — Results and limits

Known two-variable tasks, new inference seeds:

{table('known_2var')}

Primary coverage−SFT recovery difference: **{primary}**. {claim_en}

Transfer check: 12 fresh three-variable tasks, no adaptation. Coverage−SFT RR: **{transfer}**. Only one selected task requires a structure outside the original universe.

All 4,864 calls are new unrestricted generations; no catalog, forced uniqueness, repair or K-based budget. One original training seed. Existing two-variable observations were already used. COVE's 99% is supplementary catalog selection, not native LLM accuracy.

## Suggested speech

{speech}

Actual figures and all four controls should remain on the result slide; the speech does not need to read every column. Evidence: [new summary](../results/research_audit_v7/summary.json), [raw outputs](../results/research_audit_v7/evidence.jsonl.gz), [frozen protocol](../results/research_audit_v7/protocol.json).
'''
(ROOT / 'docs/RESEARCH_PRESENTATION_EN.md').write_text(presentation)
print('Wrote current README, bilingual reports and English presentation outline from verified complete results')
