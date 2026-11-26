# Budget-Aware Canonical Exclusion (BACE)

BACE is an inference extension to the existing Canonical Coverage LoRA. It keeps the trained model and its ordinary IID proposal for as long as a requested number of distinct structural hypotheses remains feasible, then applies a canonical-class exclusion mask. It changes token probabilities rather than adding a diversity prompt. It is distinct from generating a hypothesis conditional on a specified prediction difference at an unobserved input.

## Why another extension?

The v1 adapter has 64.34% uniqueness at 16 attempts, compared with 68.51% for matched SFT. Its additional recovery benefit over SFT remains uncertain. The official README suggests >80% uniqueness, >90% validity and >80% recovery, but these guides depend on the size of the reference set and the sampling budget. Improving uniqueness alone does not establish better scientific hypotheses.

Two exploratory pilots are retained. Always-on canonical exclusion guarantees uniqueness but loses validity; observation-contrastive guidance at scales 2 and 4 also fails the validation validity guard. These pilots are not silently discarded or presented as the final method. The final candidate delays exclusion to preserve the useful part of the original sampler.

## Algorithm and guarantee

Let N=16, M=13, and S_t be the set of distinct official mechanistic keys among the first t space-admissible outputs. Observation consistency is not required for membership in S_t, matching the implemented uniqueness metric. The target M is the smallest integer with M/N > .8, set before the BACE pilot.

At each attempt:

1. Compute slack D_t = (N-t) - max(0, M-|S_t|).
2. If D_t > 0, use the original LoRA model's IID sampler, unchanged.
3. If D_t <= 0 and the target is still unmet, allow only token prefixes that can complete a grammar-admissible expression whose canonical key is outside S_t.
4. Count the generated answer regardless of its observation validity, score it, and update S_t. No failed candidate is replaced for free.

Before intervention, an invalid or duplicate proposal consumes one unit of slack; a new structural key does not consume slack. When slack reaches zero, every remaining attempt supplies a new key, so |S_N| >= M, provided the finite support is not exhausted and the engine completes normally. There are 33 support classes and only 16 attempts here. Exhaustion raises an error rather than silently resetting the history.

This is the latest safe intervention under a worst-case guarantee: when D_t=0, allowing one more arbitrary IID failure could make M unreachable. It is not a theorem that the number of interventions is minimal in expectation, or that validity/recovery improves.

For active decoding, with A(prefix,S_t) the allowed next-token IDs, the policy is

    p_BACE(a | prefix,O,S_t) proportional to p_LoRA(a | prefix,O)
                                      * 1[a in A(prefix,S_t)].

The local renormalization is not claimed to equal the original LM distribution conditioned globally on validity. This is not Gumbel-Top-k sampling from the original sequence distribution.

## What builds the support?

`explorer/canonical_decode.py` enumerates a fixed finite syntax grammar from the variables, operators and depth limit only. It applies the same parser and space gate as every scored method and groups aliases using the pinned official mechanistic key. It does not read task observations or reference sets. The result is 300 strings in 33 structural classes. All aliases of a completed class are excluded together; the string-control arm excludes only the exact completed spelling.

The proposal never checks whether a candidate satisfies observations. Those observations enter the original LLM prompt; their validator is used only after the answer is generated. Thus low validity cannot be hidden by rejection sampling. The known upstream NOR inconsistency and the full reference denominator are retained.

## Learned component and controls

No v1 model weights, training data or final results are overwritten. The learned component is the existing 311,296-parameter adapter trained on the 16 training observation sets. This update adds inference control; it is not a second fine-tuning experiment.

The study includes BACE with Canonical Coverage LoRA, BACE with matched SFT, BACE with the base model, a same-switch string-exclusion control, a no-LLM uniform-class control, and the original IID results. Achieving the uniqueness guarantee is an algorithmic consequence, not evidence that the learned component is necessary. Recovery, validity and the matched controls determine the usefulness of the learned proposal and structural exclusion.

## Fairness and reproducibility

All BACE arms use the immutable v1 prompts byte-for-byte, the same checkpoints, temperature 1, sampler, per-attempt request seeds, 128-token cap and 16 counted attempts. The upstream prompt formatter iterates over an unordered operator set, so regenerating the prompt in another Python process can otherwise change its wording. BACE reads the recorded text to avoid that confound.

Before any intervention, its IID prefix is identical to the original run and can be replayed from that cache. Every replayed draw still counts in the logical 16-attempt budget, token use and inference time. Physical new model calls, cache reuse and no-LLM draws are reported separately. Original histories are never replayed after the first intervention.

The 26 test observation sets were already reported in v1. The new results are an exploratory follow-up, not an untouched confirmatory test. Task-paired bootstrap intervals average the three inference seeds within each task. One training seed and related expression families limit generalization claims.

## Limitations and novelty boundary

- The >80% uniqueness target can coexist with lower validity. A Pareto trade-off must be reported as such; it is not dominance over the original method.
- The finite grammar grows rapidly with depth/variables. This implementation supports basic Boolean depth <=2 and should not be presented as a scalable solution to unrestricted scientific discovery.
- The same grammar and exclusion logic can help an untrained model or a uniform sampler. Their controls are essential.
- Original Canonical Coverage LoRA's additional recovery contribution over balanced SFT remains an empirical question. The inference extension does not retroactively prove its loss is superior.
- Grammar constraints and sampling without replacement are established ideas. The project contribution being tested is a budget-aware intervention at the benchmark's structural equivalence classes, combined with the existing learned proposal. No global first-invention claim is made.

## References

- Chen et al., [HypoSpace, ICML 2026](https://proceedings.mlr.press/v306/chen26bz.html), and [official README](https://github.com/CTT-Pavilion/_HypoSpace).
- Scholak et al., [PICARD, EMNLP 2021](https://aclanthology.org/2021.emnlp-main.779/): established precedent for rejecting inadmissible tokens during generation.
- Kool et al., [Stochastic Beams and Where To Find Them, ICML 2019](https://proceedings.mlr.press/v97/kool19a.html): established sequence sampling without replacement; BACE does not implement their exact stochastic beam sampler.
- Shi et al., [Trusting Your Evidence: Context-aware Decoding, NAACL 2024](https://aclanthology.org/2024.naacl-short.69/): precedent for the unsuccessful observation-versus-no-observation contrastive pilot, not a new contrastive-decoding invention.
