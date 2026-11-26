# 官方 README 的 Good Score 参考值

核对日期：2026-11-26。

官方 README 的 Understanding the Metrics 表格明确列出以下 Good Score 指引：

| 指标 | README 参考值 | 本项目结构类别覆盖 LoRA | 数值上达到参考值 |
|---|---:|---:|---|
| Validity | >90% | 33.73% | 否 |
| Uniqueness | >80% | 64.34% | 否 |
| Recovery | >80% | 37.76% | 否 |

来源：[官方 README](https://github.com/CTT-Pavilion/_HypoSpace/blob/main/README.md)。本项目锁定版本 c69e9318577b34b5b896996571aefd4ba6053f58 的 README 也包含这张表。

这些是仓库给出的模型指标参考，不是课程项目的分数或合格线。课程说明按 novelty、importance、quality 评价方法与完成质量，没有规定必须达到上述三项数值。README 本身将基准定位为覆盖诊断工具，并允许更换模型、数据参数和生成预算；它没有给出跨设置通用的综合等级评分公式。

因此，本项目应表述为：在明确的布尔受控子集和固定预算下，相对本项目重跑的原始模型有明显改善，但绝对指标仍低于官方 README 的 Good Score 指引，新增模块相对匹配 SFT 的恢复率优势未证实。工程与复现交付较完整，不等于模型性能已经优秀。

README 中的 mean_validity 0.92、mean_uniqueness 0.78、mean_recovery 0.65 位于输出结构示例中，应按示例理解，不能直接当成某模型在相同实验条件下的已复现基线。跨模型和任务难度的比较需要对齐任务、预算和评分实现；本项目已披露共同评分门控与上游的区别。
