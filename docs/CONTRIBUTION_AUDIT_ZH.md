# 已完成方法的创新性与独立贡献审查

审查日期：2026-11-25。本文范围是已完成的 Canonical Coverage LoRA 第一版，保留其相关工作定位、数学论证和已有记录的探索性次要指标推断。后续的预算控制解码与偏好训练单独记录于[新增优化报告](OPTIMIZATION_RESULTS_ZH.md)，不追溯改变本审查中的原始模型、划分、回答或主分析。

## 审查结论与主张边界

可以明确陈述的独立设计贡献是：围绕 HypoSpace 官方结构类，构造有限合法写法的概率聚合与有限采样预算覆盖代理，并用共享预热、匹配数据及训练路径的 LoRA 实验检验它。它与已完成的均衡 SFT、字符串覆盖及用户描述的 DCHG 具有明确设计差异。

现有证据还支持有限的指标层面贡献：在固定训练种子和本次题库下，覆盖训练相对匹配 SFT 的合法率提高 3.125 个百分点，伴随结构唯一率降低；相对字符串覆盖的结构唯一率提高，但有效参考恢复率没有获得有力改善证据。次要指标推断属于事后探索，不能把它改写成原主指标的成功。

目前不能确认“新模块稳定提高 Recovery”“类别合并提高有效假设多样性”“全面优于普通微调”或“该组合在全部文献中首次提出”。方法差异、可证明的数学性质、已有实验中的收益与全球首创是不同层次的主张。

绝对表现也需单列：官方 README 的 Good Score 指引为 Validity >90%、Uniqueness >80%、Recovery >80%，本模型三项均未达到。相对改善、方法贡献和技术交付完成度不能替代这项事实，见[指标参考核对](BENCHMARK_SCORE_GUIDANCE_ZH.md)。

## 一、已实现的设计贡献是什么

方法使用官方 mechanistic key 定义类别；完整真值表相同的表达式仍可能属于不同类别。因此，它对齐的是基准的结构恢复指标。例：`x` 与 `x AND (x OR y)` 在所有输入上的行为相同，但官方 key 不同，见[已验证例子](../results/coverage_plan/structural_distinction_example.json)。

每道训练题只有训练参考类别进入优化。为每类验证两个完整回答写法，求包含结束 token 的真实序列概率之和，不在合法候选池中重新归一化。用预算 16 的覆盖函数构造辅助目标，与均衡 SFT 联合训练 311,296 个 LoRA 参数。测试主方法只读取原始观测与规则。

| 比较对象 | 已有或对方机制 | 本项目的明确设计差异 | 可主张的范围 |
|---|---|---|---|
| 匹配均衡 SFT | 同类数据上的回答 token 交叉熵 | 额外聚合类别概率并优化有限预算覆盖代理 | 目标函数不同；是否更好要看实验 |
| 字符串覆盖消融 | 对每个写法分别使用饱和覆盖奖励 | 先按官方结构类别求和，再计算覆盖奖励 | 表征单元不同；保留全部消融结果 |
| 同组 DCHG，按用户描述 | 推理期根据未观测位置的预测差异构造条件 | 离线更新参数，主方法无历史或差异条件 | 设计独立；未审查对方完整源码，不作成绩排名 |
| HypoSpace 原论文 | 提出基准、覆盖诊断及分层解码分析 | 本项目实现任务相关的覆盖适配器训练与匹配实验 | 应用与方法组合贡献，不认领基准或覆盖公式的发明 |

源码证据见 [coverage_lora.py](../explorer/coverage_lora.py) 的 prepare、coverage_value、loss_function、train 和 evaluate；预执行代码哈希见 [source_manifest.json](../results/final/source_manifest.json)。三分支共享 80 步预热参数和 Adam 状态，继续各训练 120 步，保持目标池、样本计划和超参数一致。这是模块归因对照的基础。

## 二、相关工作定位：已有思想与本项目组合

以下定位基于可核对的公开摘要、方法介绍及本项目实现，不是穷尽性文献查重，也没有复现这些论文的性能。

| 已有工作 | 已有思想 | 本项目的定位 |
|---|---|---|
| [HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html) | 将 LLM 视为假设采样器，评价合法性、唯一性与恢复率，分析分层解码 | 使用其结构类和评估思想，研究离线覆盖适配 |
| [GAPO](https://aclanthology.org/2025.emnlp-main.1649/) | 组级强化学习奖励与频次相关多样性训练 | 本项目在有限、验证过的训练写法池上直接计算序列概率，构造可微覆盖代理；不认领组级多样性学习的首创 |
| [PKPO](https://arxiv.org/abs/2505.15201) | 通过变换采样奖励直接优化 pass@k | 本项目对多个指定结构类别分别计算命中概率并取平均；不认领有限预算命中函数的首创 |
| [Semantic Uncertainty](https://arxiv.org/abs/2302.09664) | 按等价意义聚合概率以估计语义不确定性 | 本项目按确定性官方结构 key 聚合并用于参数训练；不认领类别概率聚合的首创 |
| [P-SFT](https://aclanthology.org/2026.acl-long.9/) | 用不同前缀条件分离多回答训练条件 | 本项目保持同一原始观测条件，修改训练目标 |
| [LoRA](https://arxiv.org/abs/2106.09685) | 冻结基础权重、训练低秩参数 | 本项目采用已有训练工具，不把使用 LoRA 本身计为创新 |

适合课程报告的定位是“任务相关的目标设计、结构规范化对齐和受控实证研究”。公开论文已有覆盖、多样性与概率聚合思想，不能仅凭方法命名声称全局首创。

## 三、可以严格论证的数学性质

以下是本项目目标的数学说明，不是新概率定理的优先权声明。

### 性质 A：有限写法池给出期望参考覆盖的下界

固定观测 O，兼容结构类别数为 K。令 rho_k 为生成任意合法第 k 类完成序列的总概率，A_k 为验证过的有限完整 token 序列集合，含终止 token。

```text
q_k = sum_{y in A_k} p_theta(y | O) <= rho_k
f_N(p) = 1 - (1-p)^N
C_A(theta) = (1/K) sum_k f_N(q_k)
```

在固定提示独立采样、完成事件互斥、生成温度与停止规则匹配、池内答案可在输出上限内完整生成的条件下，第 k 类在 N 次采样中至少被命中的概率为 f_N(rho_k)。由指标变量期望的可加性，真实期望 RR 是这些命中概率的平均。f_N 单调递增，因此 C_A <= E[RR@N]。

该论证解释覆盖项与评估目标的联系。有限池遗漏的写法使代理可能很松；优化下界并不保证有限训练后的真实 RR 增长。

### 性质 B：保持类别总概率时，分组目标不依赖写法拆分

若同一类的写法事件被重新划分，但总概率仍为 q_k，则 f_N(q_k) 不变。反之，字符串目标 sum_a f_N(p_ka) 会随着概率拆分改变，且不能解释为按类别归一化的 Recovery。

例如 N=16，同类的 .1 和 .2 两个完成事件，分组值为 f_16(.3)，按字符串分别计算则为 f_16(.1)+f_16(.2)，两者不同。这里要求“总概率不变”；新增可捕获概率质量的写法会改变有限池代理，不属于不变性保证。

### 性质 C：覆盖目标一般不是 SFT 的常数倍

考虑 K 个类别、类内均匀分配写法、回答长度均为 T 的简化分布模型，q_k 为类总概率。均衡 SFT 对 log(q_k) 的导数为 -1/(KT)，而负覆盖项的导数是：

```text
d(-C_A)/d log(q_k) = -(N/K) q_k (1-q_k)^(N-1)
```

后者随类别概率变化，不能一般表示为统一常数乘 SFT 梯度。N=16、K=2、T=10、q=(.1,.01) 时，两个类别上的覆盖/SFT 梯度比例不同，构成非等价的反例。

这一点证明目标设计具有区别；它不证明模型参数空间中的每次更新都具有不同方向。真实探针确实发现明显同向成分，且均衡 SFT 在理想条件下也可能形成均衡类别分布。因此没有更好全局最优值或稳定性能优势的保证。

对应既有代码检查见 tests/test_coverage_loss.py；确定性算例见 [formal_examples.json](../results/contribution_audit/formal_examples.json)，通过 scripts/prove_coverage_properties.py 复核。算例不是 LLM 实验成绩。

## 四、已有实验能支持的独立性能证据

主分析保持 26 道测试题、3 个推理种子、每题 16 次调用。只有一个独立训练种子 4300。为完整审查次要指标，对结构覆盖相对其余四种方法的 VR/NR/RR 共 12 项最终预算比较统一推断，未挑选某个更有利预算或子集。

先在题内平均三个推理重复，再按题 bootstrap 10,000 次计算逐点区间。VR/NR 可恢复为每题 48 次调用的整数计数，使用动态规划精确计算双侧任务级符号翻转概率；RR 使用 200,000 次蒙特卡洛符号翻转及加一校正。全部 12 个 p 值统一 Holm 校正。精确推断代码与小样本穷举对照等三项测试已通过。

| 相对对象 | 指标 | 差值，百分点 | 逐点 95% 区间 | Holm 校正 p | 解释 |
|---|---|---:|---|---:|---|
| 均衡 SFT | VR | +3.125 | [+0.96,+5.37] | 0.0481 | 固定设定下，合法率存在边缘的次要正向证据 |
| 均衡 SFT | NR | -4.167 | [-6.65,-1.60] | 0.0285 | 同时出现结构唯一率下降，不是全面占优 |
| 均衡 SFT | RR，原主要指标 | +0.894 | [-1.97,+3.72] | 1.0000 | 恢复率额外优势仍未证实 |
| 字符串覆盖 | VR | -4.087 | [-8.58,+0.40] | 0.2957 | 平均合法率较低，不能认定等效或无损 |
| 字符串覆盖 | NR | +4.808 | [+2.40,+7.13] | 0.0064 | 分组对结构唯一统计有正向影响 |
| 字符串覆盖 | RR | +0.144 | [-4.86,+4.97] | 1.0000 | 尚不能确认有效参考覆盖改善 |

完整 12 项、逐题差异、方法和输入哈希见 [secondary_metrics.json](../results/contribution_audit/secondary_metrics.json)。原 RR 区间与[原始主报告](../results/final/test/summary.json)逐项检查一致。

无需模型或 GPU 的复核命令：`.venv/bin/python scripts/verify_contribution_audit.py`。它在自动清理的临时目录重新计算推断和数学算例，逐项比较公开 JSON，不覆盖原始审查记录。

解释限制：

- 新增的是对已观察结果的探索性次要推断。Holm 校正不将其变为预注册确认性研究，也不覆盖此前所有探索选择。
- 区间是逐点区间；Holm 调整的是 p 值，不是这些区间。VR 的校正 p 接近 .05，应视为有限证据。
- 符号翻转依赖零假设下任务内方法标签的可交换性。不同观测题共享结构家族，不能无条件外推到独立任务域。
- 只有一个训练种子；这里不包括重新训练的不确定性，也不代表最优调参 SFT 的比较。
- NR 包含空间内但违反观测的结构，因此 NR 上升不能直接称为有效假设多样性上升，更不等于课程创新性。

因此，最有依据的模块级实证表述是：覆盖项在这一固定预算实验中改变了合法性与结构唯一性的权衡；合法率相对匹配 SFT 有有限的次要改善证据。整体方法相对原始模型的 RR 大幅改善仍成立，但不能把全部 24.09 个百分点收益归因于覆盖项。

## 五、可直接用于报告或视频的贡献陈述

> 我们针对 HypoSpace 的结构假设恢复问题，设计并实现了 Canonical Coverage LoRA：将验证过的完整回答按官方结构类别聚合概率，并以有限采样预算的覆盖代理辅助监督微调。该目标具有与真实期望覆盖相关的下界解释和保持类别质量的写法划分不变性，并一般区别于常数缩放的 SFT。受控实验显示整体方法明显优于原始模型；相对匹配 SFT，合法率提高 3.125 个百分点，结构唯一率下降，恢复率额外提升尚不确定。工作贡献包括任务相关的目标设计、匹配消融、可复现的小模型实现，以及对覆盖训练收益与局限的实证分析。

此陈述不把有限实验变成首创证明，也不把次要指标收益替换为恢复率成功。与同组工作的独立性基于其已提供的方法描述，公平性能比较仍需对齐实际模型、题目和调用预算。

English presentation statement:

> We implement a task-specific canonical-class coverage surrogate for HypoSpace and combine it with balanced supervised LoRA training. Verified complete-answer probabilities are pooled using the benchmark's mechanistic equivalence rules before applying a finite-budget hit objective. We justify the finite-pool lower bound, mass-preserving partition invariance and general non-equivalence to scaled SFT. Matched experiments show substantial gains over the base model. Exploratory secondary inference indicates a validity improvement over matched SFT accompanied by lower structural uniqueness; additional recovery improvement remains unresolved. Our contribution is the task-aligned formulation, controlled implementation and reproducible analysis, without a claim of global priority or consistently superior coverage.

## 后续 BACE 的独立贡献（与第一版结论分开）

2026-11-26 的跟进实验使用相同的继续训练检查点，对比 IID 与 BACE：Recovery 增加 **9.32 个百分点**，按题配对 bootstrap 95% 区间 **[5.90, 12.82]**；Uniqueness 增加 **17.07 个百分点**，Validity 点估计下降 **3.53 个百分点**。这支持预算结构排重模块在该设置中的独立覆盖贡献，并披露合法率取舍。

同一 BACE 策略下，训练模型相对无 LLM 的均匀控制多获得 **10.31 个百分点** Recovery，区间 **[5.36, 15.23]**。所以结构不重复率本身来自约束保证，而合法参考覆盖的收益仍需要学习提议分布。新增偏好损失相对匹配继续训练的优势没有得到支持，未被验证规则选用。

上述都是单训练种子、已见过第一版测试观测的探索性跟进，不是全新确认性检验；不追溯证明第一版 C16 损失相对均衡 SFT 的额外优势。见[方法与全部对比](OPTIMIZATION_RESULTS_ZH.md)。
