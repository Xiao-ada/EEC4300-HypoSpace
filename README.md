# Canonical Coverage LoRA for HypoSpace

本项目在Mac上研究：**按HypoSpace官方结构类别设计覆盖训练目标，能否改善LLM在固定采样预算下的合法假设恢复？** 目前以自由生成、匹配训练对照和泛化边界为主线，不以跨过某个指标阈值作为研究成功标准。

The project evaluates a task-specific structural-coverage LoRA objective against matched SFT using unrestricted generation. Strong catalog-selection scores are supplementary, not claims of native LLM capability.

[中文完整结果](docs/RESEARCH_RESULTS_ZH.md) · [English results](docs/RESEARCH_RESULTS_EN.md) · [研究定位](docs/RESEARCH_POSITIONING_ZH.md) · [方法与文献](docs/METHOD.md) · [事前实验协议](docs/RESEARCH_AUDIT_PROTOCOL_ZH.md)

## 当前主结果：固定16次自由生成

四组均使用相同任务提示、采样器和预算。三个适配器均由80步共享SFT预热加120步分支训练得到，原始模型不微调。新增测试不再训练或按成绩选择检查点。基础模型为固定四比特Qwen2.5-1.5B-Instruct，原训练种子只有一个。

**两变量：26道原测试观测题，新增两个采样种子。观测题已经使用过，不是全新测试集。**

| Method | VR | NR | RR | Recovered classes / task |
|---|---:|---:|---:|---:|
| Base LLM | 13.58% | 34.25% | 12.25% | 1.23 |
| Balanced SFT | 33.65% | 67.79% | 39.54% | 3.60 |
| Canonical Coverage | 34.62% | 62.62% | 38.73% | 3.48 |
| String Coverage | 35.22% | 58.05% | 35.15% | 3.15 |

**主要RR差（Coverage−SFT）：-0.81 pp, 95% CI [-4.33, +2.69] pp。区间跨零，本轮未证实覆盖目标相对匹配SFT的额外恢复率收益；这也不是两者等效的证明。**

**三变量：12道运行前固定哈希选出的新迁移题，不适配模型。**

| Method | VR | NR | RR | Recovered classes / task |
|---|---:|---:|---:|---:|
| Base LLM | 16.15% | 46.88% | 5.28% | 1.75 |
| Balanced SFT | 33.85% | 71.88% | 11.25% | 3.88 |
| Canonical Coverage | 38.28% | 69.01% | 12.33% | 4.08 |
| String Coverage | 47.92% | 69.53% | 15.30% | 4.67 |

迁移RR差：+1.08 pp, 95% CI [-4.06, +6.17] pp。区间跨零，本轮未证实覆盖目标相对匹配SFT的额外恢复率收益；这也不是两者等效的证明。

所有输出均保留，包括无效和重复回答。生成不读取参考答案、真实K、历史回答或固定目录，不强制唯一、不修复。参考空间大小变化会影响RR，两种变量数不混合统计；三变量题不是论文全部任务的复现。

![Free-generation metrics](results/research_audit_v7/metrics.png)

## 方法与独立贡献

对训练题的每个合法结构类k，将固定有限合法写法A_k的完整回答概率聚合：

```text
q_k = sum_{y in A_k} P_theta(y | O)       # includes EOS
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
