"""Build the final README from measured outputs; never fill in invented scores."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/final'
s=json.loads((out/'test/summary.json').read_text());train=json.loads((out/'training_summary.json').read_text())
metrics=s['metrics'];names={'base_iid':'原始模型 / Base IID','balanced_sft_iid':'均衡 SFT','canonical_coverage_iid':'结构类别覆盖 LoRA','string_coverage_iid':'字符串覆盖消融','base_memory':'原始模型＋历史'}
training_log=[json.loads(line) for line in (out/'training_log.jsonl').read_text().splitlines()]
training_minutes=sum(r['seconds'] for r in training_log)/60
matched=json.loads((out/'test/matched_validity_exploratory.json').read_text())
matched_delta=100*matched['task_mean_expected_RR_difference']
rows=['| 方法 | VR 合法率 | NR 结构唯一率 | RR 参考覆盖率 | 平均每题推理秒数 |','|---|---:|---:|---:|---:|']
for m in names:
 a=metrics[m];rows.append(f"| {names[m]} | {a['VR']*100:.2f}% | {a['NR']*100:.2f}% | {a['RR']*100:.2f}% | {a['seconds']:.2f} |")
comparison=s['canonical_vs']['balanced_sft_iid'];delta=comparison['RR_difference']*100;lo,hi=[x*100 for x in comparison['task_bootstrap_95_interval']]
ab=s['canonical_vs']['string_coverage_iid'];ab_delta=100*ab['RR_difference'];ab_lo,ab_hi=[100*x for x in ab['task_bootstrap_95_interval']]
if ab_delta<=0:ab_note='结构类别合并在本次测试中未超过字符串覆盖消融，不能宣称合并模块是已验证优势。'
elif ab_lo<=0:ab_note='结构类别合并的平均 RR 高于字符串覆盖，但区间跨零，模块贡献仍不确定。'
else:ab_note='结构类别合并相对字符串覆盖的 RR 配对区间为正，结论限于本次设定。'
base_delta=(metrics['canonical_coverage_iid']['RR']-metrics['base_iid']['RR'])*100
vr_delta=(metrics['canonical_coverage_iid']['VR']-metrics['balanced_sft_iid']['VR'])*100
threshold_note='本次达到该数值门槛。' if delta>=5 and vr_delta>=-2 else '本次未达到该数值门槛，保留为研究结果，不据此宣称覆盖目标是确定胜出的方案。'
if delta>0 and lo>0:conclusion='结构类别覆盖的平均 RR 高于匹配的均衡 SFT，按题配对区间未跨零；结论仍限于本次小题库。'
elif delta>0:conclusion='结构类别覆盖的平均 RR 较高，但配对区间跨零，额外优势尚不确定。'
else:conclusion='结构类别覆盖没有获得相对均衡 SFT 的平均 RR 提升；不能把常规微调收益归因于覆盖损失。'
readme=f'''# Canonical Coverage LoRA for HypoSpace

在 Apple M5、24GB Mac 上实际完成的小模型课程研究：用经过校验的合法表达式训练 LoRA，并检验官方结构类别覆盖目标相对均衡 SFT 是否提供额外收益。

**完整训练、验证与固定测试已完成。全部数字来自真实模型输出。** 基础模型为固定的四比特 Qwen2.5-1.5B-Instruct；使用 16 道训练题、6 道验证题、26 道测试题。正式生成共 6720 次，其中测试 6240 次。没有使用付费模型 API。

English summary: This project studies parameter-level coverage adaptation for a frozen quantized language model on a task-derived HypoSpace Boolean subset. It compares matched LoRA training objectives and a practical history baseline. Results are small-model, held-out-observation evidence, not a reproduction of the paper's model scores or a claim of globally new diversity training.

## 最终测试结果

每题生成 16 次，三个随机运行编号 17/29/43，先按题和运行算指标，再宏平均。失败、重复和不合规答案都保留在调用预算内。

{chr(10).join(rows)}

结构类别覆盖相对原始模型的 RR 差为 **{base_delta:+.2f} 个百分点**；相对均衡 SFT 为 **{delta:+.2f} 个百分点**，按题配对 bootstrap 的 95% 区间为 **[{lo:+.2f}, {hi:+.2f}] 个百分点**，VR 差为 **{vr_delta:+.2f} 个百分点**。{conclusion}

相对字符串覆盖消融的 RR 差为 **{ab_delta:+.2f} 个百分点**，区间 **[{ab_lo:+.2f}, {ab_hi:+.2f}]**。{ab_note}

预先提出的实际采用门槛是相对 SFT 的 RR 增加至少 5 个百分点且 VR 下降不超过 2 个百分点；它不是显著性检验或效果承诺。{threshold_note} 不要仅凭超过原始模型就宣称覆盖损失有效。

- [完整测试汇总](results/final/test/summary.json)与[逐题及运行结果](results/final/test/episodes.csv)。
- [验证结果](results/final/validation/summary.json)，与最终测试明确分开。
- [核验记录](results/final/verification.json)及[组内比较包](results/final/group_comparison_packet.json)，含 RR@10 和固定配置。
- [压缩原始测试证据](results/final/test/evidence.jsonl.gz)：每次提示、观测、原回答、种子、用量与评分。
- [参考集合外校验通过项](results/final/test/out_of_reference.json)及[原始私有轨迹哈希](results/final/test/raw_manifest.json)。

![Recovery versus budget](results/final/coverage.png)

![Validity uniqueness and recovery](results/final/metrics.png)

![Paired differences](results/final/paired_differences.png)

图表同时提供独立 PDF 文件，可用于小组视频和报告。预算 10 的结果也包含在汇总中，不能在未对齐题目和模型时与同组截图直接排名。

## 课程要求与研究定位

老师 Part 1.2 占总评 30%，要求设计新颖 ML 方法改善 HypoSpace 上的 LLM 表现，方法自由；按 novelty、importance、quality 评分，最终提交十分钟小组视频和公开 GitHub 仓库，每位成员讲解，全组同分。

本仓库交付源码、真实适配器、原始记录、对照、消融、分析、复现说明及[视频录制提纲](docs/VIDEO_GUIDE_ZH.md)。**视频尚需组员实际参与录制，仓库和提纲不能替代视频。** 代码中的 NR 是结构唯一率，与课程创新性评分不是同一个概念。

拟研究贡献是把官方 mechanistic key、有限别名覆盖下界和合法性学习结合到适配器训练，并在同训练预算下验证它的作用。LoRA、均衡训练和期望覆盖公式不是首次提出；已有 GAPO 等多样性训练工作需要正常引用。

## 方法与对照

每道训练题枚举兼容参考类别；仅保留通过共同校验的表达式和固定外层括号格式变体，构成每类最多两个完整回答。训练器只读取训练题标签。当前有效目标为 143 个题目与类别配对、286 条写法，另有六个配对没有可用合法写法。所有回答保留真实结束 token，提示与填充不参与交叉熵。

设 A_k 为类别 k 的有限完整回答事件，p(y|O) 为包含结束 token 的序列概率：

```text
p_tilde[k] = sum(p(y | O) for y in A_k)
C_16 = (1/K) * sum(1 - (1 - p_tilde[k])**16)
L = balanced_SFT_loss - C_16
```

固定提示独立采样时，有限互斥完成事件提供期望参考覆盖下界；它不是所有可能写法的完整类别概率，也不适用于动态历史的独立同分布解释。p(y|O) 来自 token 对数概率求和，不能使用平均 token 概率，也不在合法候选池中重新归一化。

训练先做 80 步共享 SFT 预热，再复制参数和 Adam 状态给三个各 120 步的分支：均衡 SFT、类别覆盖、字符串覆盖。每个最终适配器有相同的 200 步训练路径；分支使用匹配的样本顺序、有效批量和学习率。字符串消融分别奖励写法，保留相同分母与 SFT 权重，检验类别合并的作用。

配置：rank 8，MLX scale 16，dropout 0，最后八个 transformer block 的 q/v 投影，学习率 1e-4，梯度检查点，每次更新四个类别组、共八条回答。温度 1、top-p 1、关闭 top-k/min-p 和重复惩罚、最多 128 输出 token。

这是离线参数训练，主方法测试只读取原始观测与任务规则。它不采用 DCHG 的未观测输入选择、指定预测差异、历史条件构造或修复循环。固定括号变体只是训练编码；详细说明见[方法文档](docs/METHOD.md)和[组内比较协议](docs/GROUP_COMPARISON_ZH.md)。

## 数据与评分边界

使用上游布尔 x/y、AND/OR/NOT、深度 2 的规则构造受控题目。固定环境枚举到 34 个参考结构类别；从一至三条观测、至少四个兼容类别的规则得到 48 个观测题。按内容固定划分为 16/6/26，见[清单](results/coverage_plan/split_manifest.json)。这是任务规则派生子实验，不是论文所有题目、任务域和模型的复现。

不同观测题可以共享表达式结构，结论只涉及未见观测条件，不是未见表达式家族或跨域泛化。官方结构规则不额外使用吸收律、分配律或德摩根律合并表达式。

- VR：符合共同解析、空间和观测规则的尝试比例。
- NR：不同的空间内 mechanistic key 数除以全部尝试数，可能包含违反观测的结构。
- RR：不同合法参考类别命中数除以该题完整参考集合大小。

共同评分保留上游枚举分母，并增加一致的解析/空间先行拒绝检查。上游存在双向生成器与校验器差异：某些参考写法被拒绝，某些校验通过结构不在枚举中。训练目标先验证，参考外输出单列，所有方法使用同一口径；没有把修复评分算作方法提升。绝对成绩不与论文表格直接排名。

固定测试为 26×3×5×16=6240 次；验证为 6×1×5×16=480 次。共享预热与各分支的计算开销另行记录。主四组固定提示；第五组使用完整历史，是不同的实用采样策略。主要区间以题为重采样单位，三个运行先在题内平均，不能把全部输出当成独立题目。

覆盖目标本身也会增加合法答案的概率质量，因此 RR 上升不能自动解释为更均匀的长尾分布。另提供[匹配合法命中数的探索性分析](results/final/test/matched_validity_exploratory.json)，从实际输出等量抽取参考内合法命中，比较期望去重覆盖。纳入 {matched['included_episodes']}/{matched['total_paired_episodes']} 组配对输出，零共同命中情况被排除；覆盖方法相对 SFT 的 RR 差为 **{matched_delta:+.2f} 个百分点**。这个诊断也未提供额外多样性收益的支持。它是事后诊断，不替代主要同调用预算比较。

## 已测资源与训练真实性

[训练汇总](results/final/training_summary.json)记录 trainable parameters、预算、冻结检查和峰值内存；[训练日志](results/final/training_log.jsonl)逐步记录目标值和耗时；[生成账本](results/final/generation_ledger.json)记录调用和 token。[源文件记录](results/final/source_manifest.json)固定执行时的代码和数据哈希。

适配器参数数量为 **{train['trainable_parameters']:,}**，训练峰值 MLX 内存约 **{train['peak_memory_gb']:.2f}GB**。共享预热与三个分支共执行 **{len(training_log)} 次更新**，训练循环累计约 **{training_minutes:.1f} 分钟**，不含下载、准备和评估。基础张量逐一检查未改变，适配器检查为已改变。不同分支优化的目标值定义不同，不能直接用它们的 loss 大小比较性能。

早期另有 256 次控制器试跑和 96 次原始验证诊断，不纳入正式统计。旧控制器保留为历史原型，其文档不是当前结果的复现入口。

## 无 GPU 核查公开结果

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/verify_results.py
```

该脚本取得校验过的上游文件及全题库缓存，重新解析、校验公开原始回答，检查逐题汇总与 VR/NR/RR。它不调用 LLM、不需要 API 密钥或 GPU。

## 在 Apple Silicon 上完整复现

```bash
python3.12 -m venv ../runtime/mlx-env
../runtime/mlx-env/bin/python -m pip install -r requirements-mlx-lock.txt
../runtime/mlx-env/bin/python -m explorer fetch
../runtime/mlx-env/bin/python -m explorer prepare
HF_HOME=../runtime/hf-cache ../runtime/mlx-env/bin/python scripts/local_mlx.py --download-only
../runtime/mlx-env/bin/python -m unittest discover -s tests -v
../runtime/mlx-env/bin/python scripts/restore_training_targets.py
../runtime/mlx-env/bin/python -m explorer.coverage_lora train
../runtime/mlx-env/bin/python -m explorer.coverage_lora validation
../runtime/mlx-env/bin/python -m explorer.coverage_lora test
../runtime/mlx-env/bin/python -m explorer.final_report
../runtime/mlx-env/bin/python scripts/plot_final.py
../runtime/mlx-env/bin/python scripts/verify_results.py
```

`explorer prepare` 生成全部 48 题缓存，正式 runner 使用冻结的 16/6/26 清单覆盖旧原型划分。`restore_training_targets.py` 从公开压缩文件还原执行时的完整训练 token，并核对训练前哈希；这避免上游等价表达式的代表写法顺序影响复现。另可用 `explorer.coverage_lora prepare` 重新构造合法目标池，但完整复现应采用冻结目标。权重按固定 Hugging Face 修订下载并校验 SHA256，不启用远程代码。完整复现不需要 HTTP 服务或 `.env`。

训练防止覆盖已有日志；在新克隆目录复现或先归档旧运行。生成逐条断点恢复，并核对方法、配置和步骤。`runs/final_v1` 是私有运行目录，公开的证据和适配器已经单独导出。固定种子不保证跨芯片、系统或库版本逐位相同。

跳过重新训练时，在新克隆中仅准备环境、题库缓存和基础模型，直接运行 `python scripts/restore_adapters.py`（不要先还原训练目标到运行目录），将公开适配器恢复到空运行目录，再执行 validation/test。原始基础权重不在仓库内，体积约 869MB。

查看不重新推理的固定验证题演示：`python scripts/show_demo.py`。

## 文件入口与发布

- `explorer/coverage_lora.py`：数据、掩码、训练和直接 MLX 评估。
- `explorer/final_report.py`：完整性检查、指标、预算曲线和配对区间。
- `explorer/experiment.py`、`upstream.py`：共同校验及固定版本加载。
- `artifacts/adapters/`：三个最终 LoRA、配置、许可证及哈希。
- `results/final/`：本次真实结果、原始压缩证据和图表。
- `scripts/verify_results.py`：独立 CPU 核查入口。
- `docs/`：方法、视频提纲、历史方案和组内对比说明；`ci_example.yml` 是可选 CI 模板。

源码使用 MIT；适配器的基础模型为 Apache 2.0，见 [NOTICE](NOTICE.md) 和适配器目录许可证。不要上传 `.env`、完整模型、环境、缓存、校内制度文件和账户信息。临时工作放父目录 `.work`，本次结束后清理；模型缓存和可复现运行按用途保留。

同组 DCHG 的实际模型、题目和修复计数尚未取得，未把其截图分数冒充共同测试结果。公开项目由 GitHub 账号 Xiao-ada 维护；每位组员在视频中的实际贡献需由小组填写。

## 参考文献

- Chen et al. [HypoSpace, ICML 2026](https://proceedings.mlr.press/v306/chen26bz.html)；[官方代码](https://github.com/CTT-Pavilion/_HypoSpace)。
- Anschel et al. [GAPO, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1649/)。
- Fan et al. [Prefix-conditioned SFT](https://aclanthology.org/2026.acl-long.9/)。
- [MLX LM LoRA](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)。
- [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)；固定转换版本见 model.local_mlx.lock.json。
'''
if (ROOT/'results/diagnostics/v1_gradient_probe/summary.json').exists():
    readme += '\n## 后续机制诊断\n\n第一版之后补做了仅使用训练样本的只读梯度探针和有限语法写法审计，未修改模型、测试结果或生成调用数。采样点上的覆盖梯度与 SFT 高度同向；训练类别在有限语法池中的合法写法数为 1–50，第一版每类固定使用两个写法。诊断提供新的研究方向，尚不证明额外性能收益。见[诊断证据与下一步实验](docs/NEXT_EXPERIMENT_ZH.md)。\n'
if (ROOT/'results/contribution_audit/secondary_metrics.json').exists():
    readme += '\n## 已完成版本的独立贡献审查\n\n[贡献审查与可直接使用的报告陈述](docs/CONTRIBUTION_AUDIT_ZH.md)整理了已有工作的定位、目标的数学性质和匹配对照证据。对现有结果补做的探索性次要推断显示：相对匹配 SFT，VR 增加 3.125 个百分点，同时 NR 降低 4.167 个百分点；RR 的额外优势仍未证实。全部四个对照、三个最终指标统一纳入十二项比较，保留代价与不确定性。次要推断不是新的预注册确认性结果，也不证明全球首创。\n\n无需训练或 GPU 可复核：`.venv/bin/python scripts/verify_contribution_audit.py`。第二版重训不安排执行；原始主结果、模型和 6720 次正式生成记录保持不变。\n'
if (ROOT/'docs/PERSONAL_TALK_ZH.md').exists():
    readme += '\n## 个人两至三分钟讲解\n\n按各成员分别介绍自己方法的分工，已准备[中文说明、主讲稿、精简稿、两页内容和问答](docs/PERSONAL_TALK_ZH.md)，以及[英文备选稿](docs/PERSONAL_TALK_EN.md)。[全组视频指南](docs/VIDEO_GUIDE_ZH.md)给出三人或四人组的十分钟分配参考。稿件时长为估算，实际视频仍需成员试读和录制。\n'
if (ROOT/'docs/PERSONAL_TALK_2MIN_ZH.md').exists():
    readme += '\n当前推荐的个人口头稿：[两分钟以内，含文献逻辑与最终成果](docs/PERSONAL_TALK_2MIN_ZH.md)。\n'
if (ROOT/'presentations/personal_method_results.pptx').exists():
    readme += '\n[Editable principle and results slides](presentations/personal_method_results.pptx), with [page previews](presentations/README.md).\n'
(ROOT/'README.md').write_text(readme)
write={'base_RR_gain_pp':base_delta,'vs_SFT_RR_gain_pp':delta,'vs_SFT_RR_interval_pp':[lo,hi],'vs_SFT_VR_gain_pp':vr_delta,'interpretation':conclusion,'string_ablation_interpretation':ab_note,'practical_threshold_met':delta>=5 and vr_delta>=-2}
(out/'interpretation.json').write_text(json.dumps(write,ensure_ascii=False,indent=2)+'\n')
print('Generated measured README and bounded interpretation')
english_names={'base_iid':'Base IID','balanced_sft_iid':'Balanced SFT','canonical_coverage_iid':'Canonical coverage LoRA','string_coverage_iid':'String coverage ablation','base_memory':'Base + history'}
etable=['| Method | VR | NR | RR |','|---|---:|---:|---:|']
for m in english_names:
 a=metrics[m];etable.append(f"| {english_names[m]} | {100*a['VR']:.2f}% | {100*a['NR']:.2f}% | {100*a['RR']:.2f}% |")
interpretation=('The additional RR benefit over matched SFT has a positive task-bootstrap interval.' if delta>0 and lo>0 else 'The task-bootstrap interval includes zero; an additional benefit over matched SFT is uncertain.' if delta>0 else 'No additional mean RR benefit over matched SFT was observed. Base-relative training gains must not be attributed solely to coverage.')
(ROOT/'docs/RESULTS_EN.md').write_text(f'''# Final held-out results\n\nReal 4-bit Qwen2.5-1.5B-Instruct experiments on 26 held-out observation sets, three inference repetitions and 16 calls per episode. The three inference seeds do not represent three independent adapter-training runs. The single training seed is 4300.\n\n{chr(10).join(etable)}\n\nCanonical coverage minus base RR: {base_delta:+.2f} percentage points. Canonical coverage minus balanced SFT RR: {delta:+.2f} points; paired task-bootstrap 95% interval [{lo:+.2f}, {hi:+.2f}] points. {interpretation}\n\nAll five methods, fixed data and matched adapter-training paths are retained. Shared warm-up is counted once in total project cost; each adapter has a 200-update path. Scoring keeps full reference denominators and exposes validator/generator mismatches. This is a small-model task-derived study, not replication of paper tables, cross-domain generalization or a matched comparison against the teammate DCHG screenshot.\n\nSee [method](METHOD.md), [machine-readable test report](../results/final/test/summary.json), [raw evidence](../results/final/test/evidence.jsonl.gz) and [root README](../README.md).\n''')
p=ROOT/'README.md';text=p.read_text().replace('## 最终测试结果','[English method](docs/METHOD.md) · [English results](docs/RESULTS_EN.md)\n\n## 最终测试结果',1)
text=text.replace('三个运行先在题内平均，不能把全部输出当成独立题目。','三个运行先在题内平均，不能把全部输出当成独立题目。三个种子指推理随机性，不代表三次独立的适配器训练；训练种子只有 4300。')
p.write_text(text)
# Preserve the preregistered narrative while replacing stale live-status prose.
for source,archive in [('docs/PROPOSAL_ZH.md','docs/PROPOSAL_PRE_RUN_ZH.md'),('docs/PROTOCOL.md','docs/PROTOCOL_PRE_RUN.md')]:
 src=ROOT/source;dst=ROOT/archive
 if not dst.exists():dst.write_text('> Pre-execution planning record. Current execution and results are in README.md and docs/METHOD.md.\n\n'+src.read_text())
(ROOT/'docs/PROPOSAL_ZH.md').write_text(f'''# 已执行的结构类别覆盖 LoRA 项目\n\n本方案的训练、验证与固定测试已完成。技术实现和真实对比见[完整 README](../README.md)、[方法](METHOD.md)及[最终测试汇总](../results/final/test/summary.json)。\n\n{chr(10).join(rows)}\n\n覆盖方法对原始模型的 RR 差为 {base_delta:+.2f} 个百分点，对匹配均衡 SFT 为 {delta:+.2f} 个百分点。{conclusion} {ab_note}\n\n设计与诊断过程保留在 PROPOSAL_PRE_RUN_ZH.md；冻结的机器可读计划保留设计时状态，不代表训练尚未完成。当前事实见 results/STATUS.json。最终十分钟小组视频仍需每位成员实际参与录制，见 VIDEO_GUIDE_ZH.md。\n''')
(ROOT/'docs/PROTOCOL.md').write_text('''# Executed experiment protocol\n\nThe matched LoRA experiment has completed. See [the method](METHOD.md), [English results](RESULTS_EN.md), [root README](../README.md) and [machine-readable final reports](../results/final/test/summary.json).\n\nFrozen 16/6/26 observation split; 80 shared SFT updates plus three matched 120-update continuations; rank 8 q/v LoRA on the last eight blocks; 480 validation and 6240 test calls, temperature 1, 16 calls per episode, three test inference seeds. All formal methods use the same direct MLX backend. Earlier HTTP diagnostics are not formal baseline rows.\n\nFull reference denominators and common fail-closed scoring are unchanged. Generator/validator mismatches are exposed. Task-bootstrap comparisons average repetitions within each task. Complexity and equal-valid-draw diagnostics are explicitly exploratory. No parameters, split or method selection changed after test generation began.\n\nThe original narrative is in PROTOCOL_PRE_RUN.md. The immutable plan JSON retains its pre-execution status; actual state is results/STATUS.json. Published evidence can be independently rescored with scripts/verify_results.py without a GPU or model inference.\n''')
(ROOT/'docs/PUBLICATION.md').write_text('''# Publication and reproducibility\n\nProject repository: https://github.com/Xiao-ada/EEC4300-HypoSpace. The course final deliverable is a public repository plus a ten-minute group video with every member presenting. Current publication state is recorded in results/STATUS.json.\n\nSource, measured aggregate results, compressed raw evidence and three reviewed LoRA-only adapters are included. Original base weights, environments, caches, raw private runs, institutional documents and credentials are excluded. MIT covers original source; adapter/base-model attribution and Apache terms are under artifacts/adapters and NOTICE.md.\n\nBefore release run scripts/audit_upload.py and scripts/verify_results.py, inspect the figures and links, then commit and push the reviewed tree. Public evidence uses only benchmark observations and model outputs. The optional CI definition is docs/ci_example.yml. No new repository-access scopes are required for the supplied local validation commands.\n\nThe team's actual video recording and speaker contributions cannot be replaced by generated notes. Use docs/VIDEO_GUIDE_ZH.md for structure and scripts/show_demo.py for a fixed saved-evidence demonstration.\n''')
