# Personal presentation script: Canonical Coverage LoRA

Use this as the English alternative to PERSONAL_TALK_ZH.md, not as an additional segment. Target roughly 2–3 minutes; actual timing requires the speaker to rehearse. The slide suggestions and all interpretation limits are in the Chinese guide. No new training or results are introduced.

I focused on parameter-level optimization through Canonical Coverage LoRA. I studied the Boolean subset of HypoSpace, where partial observations can admit several valid expressions. My goal was to improve recovery of distinct valid structures under a fixed sampling budget.

The method groups verified training answers using the benchmark's structural equivalence rules. It sums the probabilities of two complete answer forms per class, then applies a finite-budget coverage surrogate: the probability of hitting that class at least once in sixteen draws. I combine this surrogate with balanced supervised fine-tuning and update a small set of LoRA parameters. The design contribution is this task-aligned training objective.

I implemented and evaluated the approach on a Mac using a four-bit Qwen model with 1.5 billion parameters. The split contains sixteen training, six validation, and twenty-six test observation sets. Evaluation uses sixteen attempts per task, three inference seeds, and five methods. The three fine-tuned controls share matched data and training budgets, and all outputs are available for verification.

Recovery rises from 13.67 percent for the original model to 37.76 percent for canonical coverage. However, balanced fine-tuning already reaches 36.86 percent. The additional 0.89 percentage points has a confidence interval spanning zero, so I cannot claim a reliable recovery advantage. Exploratory analysis instead shows a validity increase of about 3.1 percentage points, accompanied by lower structural uniqueness.

My completed contribution is the task-specific objective, its controlled implementation, and reproducible ablation evidence. The results show both improvements and limits. This is a small Boolean study with one training seed, so broader gains remain unverified.

For a shorter version, omit the exact split counts and the sentence about exploratory validity; retain the matched-SFT result and uncertainty. Do not imply that the three inference seeds are independent training runs. Describe responsibilities according to the actual group division.

Evidence and contribution boundaries: [contribution audit](CONTRIBUTION_AUDIT_ZH.md), [final results](../results/final/test/summary.json), [full README](../README.md).
