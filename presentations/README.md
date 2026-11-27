# 个人两页展示：原理与结果

**当前选用的BACE展示：** 新版为三页英文内容，前两页讲BACE原理和匹配结果，第三页用两句话说明COVE系统输出收益的边界。见 [bace_final](bace_final/README.md)、[完整英文讲稿](bace_final/English_script.txt)和[逐句中文对照](bace_final/Script_and_translation.md)。讲稿167个口播词，建议约两分钟。以下PPTX为历史第一版，不要与新展示混用。

**历史演示稿。** 当前项目主线已转为固定预算自由生成，最新结果见[研究报告](../docs/RESEARCH_RESULTS_ZH.md)，可使用[新版英文两页内容与讲稿](../docs/RESEARCH_PRESENTATION_EN.md)。本目录PPTX和预览仍报告第一版，未自动替换为新实验。

[可编辑 PPTX](personal_method_results.pptx)

英文两页演示已保存到当前对话的在线演示，可从查看器导出 PPTX；[英文讲稿](../docs/PERSONAL_TALK_EN.md)约 179 词，报告第一版冻结结果。[官方指标参考核对](../docs/BENCHMARK_SCORE_GUIDANCE_ZH.md)区分仓库模型指引和课程评分。后续训练与 BACE 的新数字单独见[优化报告](../docs/OPTIMIZATION_RESULTS_ZH.md)，不能把第一版演示误认为本轮更新后的成绩。

1. 原理页：HypoSpace 与 GAPO 文献启发、官方结构类别的概率聚合、有限预算覆盖代理及联合训练损失。LoRA 是实现工具。
2. 结果页：完整五组 VR/NR/RR 对照，区分相对原始模型的整体收益与相对匹配 SFT 尚不确定的恢复率增益。

建议第一页约 65 秒，第二页约 55 秒，总计两分钟。页面信息不需要逐字念出，实际时长需要本人试读。讲稿见[个人两分钟稿](../docs/PERSONAL_TALK_2MIN_ZH.md)。

![原理页](principle.png)

![结果页](results.png)

PPT 中公式为可编辑文本，结果为原生可编辑表格，备注包含讲解提示和来源。实际数据及结论未改变，未新增训练或模型生成。

构建源码为 scripts/build_personal_slides.mjs，需要工作区提供的 @oai/artifact-tool、Presentations 技能工具及 Python 运行库。按运行库发现结果设置 ARTIFACT_NODE_MODULES、PRESENTATION_SKILL_DIR、PRESENTATION_PYTHON，再以相应 Node 运行脚本。已有输出需先另行归档。

[更新后的英文两页内容与两分钟口头稿](../docs/BACE_PRESENTATION_EN.md)包含 BACE 原理及 36.38% / 81.49% / 50.34% 的正式跟进结果；现有 PPTX 与在线演示保留第一版。
