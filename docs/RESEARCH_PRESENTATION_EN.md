# Current English outline: two slides, about two minutes

This is slide content and speaker notes, not an updated PPTX or a recorded video. The speech has 168 whitespace-separated words; rehearse for the actual duration.

## Slide 1 — Does coverage-aware training help free generation?

- HypoSpace: several compatible structural hypotheses, not a single correct answer.
- Pool verified complete-answer probabilities within official structural classes.
- Objective: `balanced SFT − mean_k[1−(1−q_k)^16]`.
- Matched training: shared 80-step warmup, 120 branch updates; ordinary SFT and string-coverage controls.
- Research question: additional recovery over matched SFT at a fixed 16-generation budget.

The coverage identity and LoRA are established tools; novelty is the task-specific formulation and evaluation. References: [HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html), [LoRA](https://arxiv.org/abs/2106.09685). See [method](METHOD.md) for the finite-alias assumptions and related work.

## Slide 2 — Results and limits

Known two-variable tasks, new inference seeds:

| Method | VR | NR | RR | Recovered classes / task |
|---|---:|---:|---:|---:|
| Base LLM | 13.58% | 34.25% | 12.25% | 1.23 |
| Balanced SFT | 33.65% | 67.79% | 39.54% | 3.60 |
| Canonical Coverage | 34.62% | 62.62% | 38.73% | 3.48 |
| String Coverage | 35.22% | 58.05% | 35.15% | 3.15 |

Primary coverage−SFT recovery difference: **-0.81 pp, 95% CI [-4.33, +2.69] pp**. The interval crosses zero: additional recovery over matched SFT is not established, which also does not prove equivalence.

Transfer check: 12 fresh three-variable tasks, no adaptation. Coverage−SFT RR: **+1.08 pp, 95% CI [-4.06, +6.17] pp**. Only one selected task requires a structure outside the original universe.

All 4,864 calls are new unrestricted generations; no catalog, forced uniqueness, repair or K-based budget. One original training seed. Existing two-variable observations were already used. COVE's 99% is supplementary catalog selection, not native LLM accuracy.

## Suggested speech

I study whether coverage-aware training helps LLMs recover more compatible structural hypotheses within sixteen generations.

I pool complete-answer probabilities by HypoSpace's structural classes and add a finite-budget coverage term to SFT. LoRA implements adaptation; it is not the innovation claim.

Ordinary SFT, structural coverage and string coverage share training data and budgets. The unadapted model is another baseline.

Our new audit uses unrestricted generation, without a candidate catalog, forced deduplication, repair or reference-count budget.

On twenty-six previously used observation tasks with new sampling seeds, structural coverage achieves 38.73 percent recovery, compared with 39.54 percent for matched SFT. The difference is -0.81 percentage points, with a task-bootstrap interval from -4.33 to +2.69. The interval crosses zero, so the additional recovery benefit is not established.

We also test twelve new three-variable tasks without adaptation. This is a limited transfer check, not comprehensive unseen-structure generalization.

My contribution is the task-aligned objective and controlled, reproducible evaluation. Only one training seed exists. Inconclusive results are retained; the earlier high-scoring catalog system remains supplementary.

Actual figures and all four controls should remain on the result slide; the speech does not need to read every column. Evidence: [new summary](../results/research_audit_v7/summary.json), [raw outputs](../results/research_audit_v7/evidence.jsonl.gz), [frozen protocol](../results/research_audit_v7/protocol.json).
