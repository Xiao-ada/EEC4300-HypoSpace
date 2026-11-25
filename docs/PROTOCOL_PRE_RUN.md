> Pre-execution planning record. Current execution and results are in README.md and docs/METHOD.md.

# Canonical coverage LoRA experiment protocol

Status: design specification before training implementation or test generation. Existing `explorer` commands implement the archived controller pilot, not the LoRA method. See the Chinese proposal and `results/coverage_plan/plan.json`. This protocol supersedes the controller protocol for future work; old configuration files and cached splits remain intact.

## Model and data

Use the pinned 4-bit Qwen2.5-1.5B-Instruct conversion and MLX LM 0.32.2 on Apple M5. Defaults: rank 8, MLX scale 16, dropout zero, last eight transformer blocks, q/v projections, learning rate 1e-4, gradient checkpointing, full-sequence limit 1024. A 20-update timing/memory probe precedes resource-setting freeze. No base weight is trainable.

Use Boolean x/y, extended operators, depth 2 and official mechanistic keys. Keep 16 training and six validation observation sets. Before test generation, append 20 unused sets to the six untouched test sets, giving 26. Public IDs are in `results/coverage_plan/split_manifest.json`. Shared expression families are expected; only held-out observation constraints are claimed. The old 16/6/6 cache is not overwritten.

## Targets and loss

Only training references supply optimization labels. Construct at most two complete answer token sequences per mechanistic class: the serialized formula and a fixed redundant outer-parenthesis variant. These aliases are training encodings, not an inference rewriting algorithm. Validate every alias with the common parser, in-space gate, observation checker and canonicalizer. Deduplicate token sequences. Include the actual answer end token and mask all prompt tokens. Do not introduce truth-functional equivalences beyond upstream structural rules.

Sample tasks, positive classes and aliases hierarchically for balanced SFT. Compute complete answer probabilities through summed conditional token log probabilities, not average token probabilities. Sum mutually exclusive alias events within each class. With K reference classes, use C_B = mean_k[1-(1-p_tilde[k])**B], B=16 and lambda=1; objective is balanced SFT minus lambda*C_B. Empty alias sets contribute zero. Do not normalize probabilities over the candidate pool.

For fixed-prompt IID sampling, the finite complete-event pool gives a lower bound on expected reference coverage, subject to matched tokenization, termination and sampling distributions. It is not an exact adaptive-history or complete-class probability calculation. Use stable log-sum-exp and log1p/expm1; check probability bounds, finite gradients, frozen base weights and prompt masks.

The surface-string ablation applies the same saturation to each alias separately with the same K denominator. It may exceed one and is not a recovery metric. SFT weights, targets, optimizer settings and data exposure stay matched.

## Training budgets

Run 80 shared balanced-SFT updates, then copy both weights and optimizer state to three 120-update continuations: balanced SFT, canonical coverage and string coverage. Reset continuation RNGs and target schedules to the same state; each final adapter has a 200-update path. Attribute shared computation once to total project cost, and the full path to each method's resource comparison.

Use the fixed final checkpoint. Resource-driven changes follow the 20-step probe, precede formal validation/test, are recorded in a versioned amendment and apply to all branches. Formal validation is diagnostic; open-ended tuning is outside this plan.

## Generation

Four primary methods use fixed empty-prior prompts: base, balanced SFT, canonical coverage, string coverage. A fifth baseline uses base plus the upstream full accumulated prior-answer prompt. Label it history-dependent; the IID coverage derivation does not apply to it.

Use the same upstream prompt template and evaluator, temperature 1.0, top-p 1, top-k/min-p disabled, repetition penalty disabled and at most 128 output tokens. Use stochastic repetition labels 17/29/43 and record actual sampler seed support. Randomize method execution order reproducibly. Every failed or duplicate output consumes a call; no hidden rejection sampling or solver answers.

Validation: 6 tasks * 1 repetition * 5 methods * 16 = 480 calls. Test: 26 * 3 * 5 * 16 = 6240 calls. New directory: `runs/coverage_lora_v1`; generation cap: 7500. Training teacher-forcing work is recorded separately. Old controller temperature 0.8, 1400-call cap and 256 random-action outputs do not enter the formal comparison.

## Outcomes

Primary outcome: paired RR@16 difference against balanced SFT. Report VR/NR/RR at 1/2/4/8/10/16, training/inference time, tokens and peak memory. NR counts distinct in-space keys including observationally invalid ones; RR counts valid recovered reference keys. Keep the full reference denominator and expose valid keys outside that reference as a diagnostic.

Average repetitions within task, then bootstrap paired observation sets, not hypotheses. Report all tasks and methods including failures. Provisional adoption target: five percentage points RR gain with no more than two points VR loss versus balanced SFT. This is not a significance test or promised result. A zero-crossing interval means uncertain evidence. Improvements over base alone do not establish a coverage-loss benefit; also compare the practical history baseline.

## Compatibility and reproducibility

Keep pinned upstream commit and hashes. Preserve the generator/validator inconsistency: validate training targets, count empty alias classes, retain test denominators. Apply the same additional fail-closed lexical/space gate to every method. Do not claim replication of paper scores or violation of coverage bounds.

Record model/tokenizer/template hashes, adapters, optimizer budgets, grouped aliases, masks, splits, raw outputs, usage, sampler settings and analysis scripts. Separate reference scoring from generation inputs. Publish source, reviewed aggregates and selected small artifacts deliberately; environments, weights caches, institutional materials and credentials stay outside Git.

## Independence from the teammate method

The core method is offline parameter training with observation-only fixed-prompt generation. It has no previous-answer input, unobserved-input selection, prediction-difference target, added synthetic test observation, repair loop, variable-permutation sampler or behavior-preserving rewrite sampler. The history baseline remains a labelled baseline, not the proposed algorithm. Full-truth-table equality does not imply the same upstream mechanistic class; preserve this distinction.

The supplied teammate screenshot describes 34 development tasks, three seeds and ten calls, but does not establish full configuration compatibility. RR@10 prefixes are additionally exported; internal RR@16 remains primary. Shared-model group comparison needs the same base checkpoint, task IDs, prompt, sampling, evaluator and attempt accounting; adapter training cost is reported separately. Development tasks used by either method are not a fresh joint test. The joint protocol is pending the teammate configuration and task overlap audit; see GROUP_COMPARISON_ZH.md.

## Baseline implementation and validation diagnostic

`python -m explorer.baseline --split validation --method base_iid` now implements the original fixed-prompt baseline. It reuses the pinned evaluator, excludes reference labels and history from generation inputs, explicitly requests sampling controls and unique per-call seeds, and persists the 96 validation calls and token usage. No adapter is loaded by the documented base-model server command. Twelve infrastructure tests pass, including IID prompt isolation and validation/test report separation; the proposed LoRA loss remains unimplemented.

The completed one-repetition validation diagnostic is VR 18.75%, NR 38.54%, RR 14.35%. Four validator-passing outputs have a key outside the enumerated reference set and are excluded from RR without changing its denominator. They are preserved in `results/coverage_baseline/validation/verification.json`. This reverse-direction generator/validator discrepancy is additional to the previously noted rejected serialized reference. It is not a final test score or evidence of an improvement.
