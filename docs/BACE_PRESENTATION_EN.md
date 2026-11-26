# Updated two-slide English presentation: Coverage LoRA + BACE

These slides describe the 2026-11-26 follow-up. The older PPTX and online deck retain the v1 results.

## Slide 1 — A budget-aware way to explore structural hypotheses

**Problem:** A learned LLM proposal can repeatedly generate the same structural explanation.

**Learned proposal:** Canonical Coverage LoRA, followed by 80 additional coverage updates on the original training split.

**BACE — Budget-Aware Canonical Exclusion**

- Target: at least 13 distinct official structural classes in 16 counted attempts.
- Keep ordinary IID sampling while the remaining budget has slack.
- When another duplicate would make the target unreachable, mask token prefixes that can only complete an already-seen class.
- All represented spellings of that class are blocked together. Observation validity is checked after generation, for scoring.

`slack = (16 - completed) - max(0, 13 - distinct_seen)`

The guarantee is at least 81.25% structural uniqueness while the support remains available. It is not a guarantee of validity or recovery.

References: [HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html), [GAPO](https://aclanthology.org/2025.emnlp-main.1649/), [PICARD](https://aclanthology.org/2021.emnlp-main.779/). LoRA, constrained decoding and non-replacement sampling are established ideas; the project tests this budget-aware structural intervention.

## Slide 2 — Higher recovery under the same proposal budget

| Method | Validity | Uniqueness | Recovery |
|---|---:|---:|---:|
| Original coverage model | 33.73% | 64.34% | 37.76% |
| Continued coverage, IID | 39.90% | 64.42% | 41.02% |
| Continued coverage + BACE | **36.38%** | **81.49%** | **50.34%** |
| Uniform + BACE, no LLM | 28.93% | 83.89% | 40.03% |

**Decoder contribution:** +9.32 recovery points versus the same checkpoint with IID; 95% task-bootstrap interval [5.90, 12.82]. Validity decreases by 3.53 points in that matched comparison.

26 Boolean tasks × 3 inference seeds × 16 counted attempts. One training seed; exploratory follow-up on the v1 observation test sets. Uniqueness exceeds the README guide; validity and recovery remain below their guides. An additional preference-training trial did not win validation and is not part of the selected deployment.

## Speaker notes — under two minutes

HypoSpace evaluates whether a model can produce a set of different explanations consistent with partial observations. My project uses Canonical Coverage LoRA to learn a proposal over structural hypotheses. However, a trained model can still spend its limited budget repeating the same structures.

I therefore designed Budget-Aware Canonical Exclusion, or BACE. With sixteen attempts, the target is thirteen distinct structural classes. The controller keeps normal sampling while there is enough slack. When another duplicate would make the target unreachable, a token-level grammar mask excludes every represented spelling of previously seen classes. This guarantees at least 81.25 percent uniqueness, but does not guarantee correctness.

I tested the method on twenty-six Boolean tasks with three inference seeds. The selected system achieved 36.38 percent validity, 81.49 percent uniqueness, and 50.34 percent recovery.

To isolate the decoder, I compared the same checkpoint with and without BACE. Recovery improved by 9.32 percentage points, with a task-bootstrap interval from 5.90 to 12.82 points, while validity decreased by 3.53 points.

The learned proposal also outperformed uniform sampling in recovery. The main contribution is therefore a measured coverage improvement from budget-aware structural exploration. The study remains limited to a small Boolean setting and one training seed.
