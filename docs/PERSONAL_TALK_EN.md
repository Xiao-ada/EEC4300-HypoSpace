> This is the frozen v1 talk. The updated BACE two-slide outline and English speaker notes are in [BACE_PRESENTATION_EN.md](BACE_PRESENTATION_EN.md).

# English personal presentation: two slides, under two minutes

Target approximately 1 minute 45 seconds to 2 minutes. This is an estimate, not a measured recording. Rehearse once with a timer.

## Slide 1: Canonical Coverage LoRA (about 55 seconds)

My work targets hypothesis coverage through a coverage objective tailored to HypoSpace.

HypoSpace shows that valid outputs can still concentrate on a few hypotheses. GAPO studies diversity using group-level rewards. Building on this idea, I explored a supervised objective based on the benchmark's structural classes.

I sum the complete-sequence probabilities of two verified answer forms per class, then estimate whether each class will be reached within sixteen draws. This coverage surrogate supplements balanced supervised fine-tuning. I use LoRA to update a small set of parameters.

## Slide 2: Results and Contribution (about 55 seconds)

On my Mac, I evaluated a 1.5-billion-parameter Qwen model with five methods, twenty-six test tasks and three inference seeds. Fine-tuning data and budgets were matched.

Recovery increased from 13.67 percent for the base model to 37.76 percent. However, balanced SFT already reached 36.86 percent. The additional gain of 0.89 percentage points remains uncertain because its confidence interval spans zero. Exploratory analysis shows higher validity but lower uniqueness. All three metrics remain below the README good-score guides.

My contribution is the task-specific objective and controlled, reproducible evaluation, with conclusions limited to this small Boolean subset.

## Delivery notes

Read percentages as, for example, "thirteen point six seven percent." Read SFT as the letters S-F-T. Do not read equations or references symbol by symbol. Three inference seeds are not three independent training runs.

If rehearsal exceeds two minutes, omit the sentence about LoRA and the sentence about exploratory validity. Retain the matched-SFT result and uncertainty.

## References and roles

- [Chen et al., HypoSpace, ICML 2026](https://proceedings.mlr.press/v306/chen26bz.html): benchmark and coverage-failure motivation.
- [Anschel et al., GAPO, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1649/): prior group-level diversity training. This project does not reproduce its RL algorithm.
- [Hu et al., LoRA](https://arxiv.org/abs/2106.09685): the adaptation tool, not the original contribution.

Evidence: [contribution audit](CONTRIBUTION_AUDIT_ZH.md), [test results](../results/final/test/summary.json). Actual video recording remains for the speaker.
