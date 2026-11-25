# Canonical Coverage LoRA

The method trains a small adapter to increase recovery of the benchmark's mechanistic hypothesis classes. Generation is conditioned only on the original observations and task rules. It does not select unobserved inputs, prescribe prediction differences, perform repair, or use the teammate's DCHG procedure.

## Verified supervision

We use the pinned Boolean x/y generator with AND/OR/NOT and depth 2. Sixteen training observation sets are disjoint from six validation and 26 test sets. Only training references enter optimization. Each reference expression and a fixed redundant outer-parenthesis variant are verified under the common parser, space gate, observation validator and mechanistic key. The two variants are training encodings, not a rewriting search algorithm.

The final training pool has 143 nonempty observation/class pairs, 286 aliases and six empty reference pairs. A mechanistic class is not a full truth-table equivalence class: absorption, distributivity and De Morgan normalization are not added to the official rules.

For the exact chat template we construct the prompt with the assistant-start marker, append the answer, and retain tokens through the first actual end token. Prompt tokens and padding are masked from the loss. No observation or end token is truncated. The longest prepared sequence is 557 tokens.

## Objective

Let A_k be the finite set of complete answer token sequences for class k, and let p_theta(y|O) be the complete autoregressive probability, including termination. Define:

    p_tilde[k] = sum_y_in_Ak p_theta(y|O)
    C_16 = (1/K) sum_k [1 - (1 - p_tilde[k])^16]
    L = L_balanced_SFT - C_16

Complete sequence log probability is the sum, not mean, of answer-token log probabilities. The SFT anchor is mean per-answer-token cross entropy, averaged over aliases. Each update samples tasks uniformly, positive classes uniformly within task, and uses all verified aliases of that class.

If K_positive classes have usable aliases, the sampled coverage term is multiplied by K_positive/K. Its expectation over the sampled positive class is the full sum divided by the original reference count K. Empty groups have zero coverage contribution and never require undefined SFT targets.

Under fixed-prompt IID sampling, disjoint complete answer events and matched sampling/termination rules, the finite alias pool provides a lower bound on expected reference coverage. It is not the full probability mass of every possible wording, and no normalization over valid candidates is performed. The coverage term exponentiates complete-sequence log probabilities, sums alias probabilities and uses log1p/expm1 with bounded probability arithmetic.

Balanced SFT can also approach a uniform class distribution in an ideal limit. Our question is whether grouping and finite-budget coverage gradients help under a fixed finite training budget; a better theoretical optimum is not claimed.

## Matched controls

The frozen base is the public pinned 4-bit Qwen2.5-1.5B-Instruct conversion. LoRA uses rank 8, MLX scale 16, dropout zero, q/v projections in the final eight transformer blocks, learning rate 1e-4 and gradient checkpointing. Four class microbatches (two aliases each) form each optimizer update.

After 80 shared balanced-SFT updates, the weights and Adam state are copied to three continuations of 120 updates each. The continuations have the same class schedule and optimizer settings. They optimize balanced SFT alone, class coverage, or surface-string coverage. Thus each final adapter has a 200-update path. Shared computation is counted once in the project total and included in each method's individual training-path cost.

The string control applies the saturating term separately to aliases, retaining denominator K. In the small-probability limit its scale matches the grouped objective. It may exceed one and is not a recovery percentage. This isolates grouping while keeping data and SFT exposure matched.

A 20-update timing probe, included in warm-up, can reduce all training budgets uniformly if a projected 440 updates exceed three hours. The decision uses resources only, before adapter validation or final testing. The selected budget and probe are exported with the results.

## Inference and scoring

The four IID methods use the upstream prompt with an empty prior list. The fifth practical control uses the unadapted model with the full accumulated prior-answer prompt. All use temperature 1, top-p 1, no top-k/min-p filtering, no repetition penalty and at most 128 tokens per generation. Each call records a per-task/per-step deterministic request seed. Model/backend reproducibility is bounded by MLX numerical behavior, not guaranteed bitwise across hardware.

The evaluator is shared. It adds a fail-closed lexical/space gate before the pinned upstream observation validator. Recovery retains the complete original reference denominator. No hidden retries, repair calls or solver-generated test answers are included. Out-of-reference validator passes are separately exposed rather than inserted into the denominator.

The primary comparison is class coverage versus matched balanced SFT on 26 held-out observation sets, three repetitions and 16 calls per episode. RR is macro-averaged; repetitions are averaged within task before paired task bootstrap. VR, NR, RR at 1/2/4/8/10/16 and resource costs are reported. Higher base-relative performance alone does not establish a coverage-loss contribution.

## Limits

The reference generator and validator disagree in both directions for some expressions. Targets are verified, empty classes are recorded, and every method uses the same disclosed scoring rule. Absolute scores are not a reproduction of the paper's tables. The task split establishes unseen observations, not unseen expression families or cross-domain generalization. Teammate development results are not directly ranked without matching their model, tasks and budget accounting.

Related work includes [HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html), [GAPO](https://aclanthology.org/2025.emnlp-main.1649/) and [prefix-conditioned SFT](https://aclanthology.org/2026.acl-long.9/). LoRA, balancing, diversity training and the expected coverage identity are existing ideas; this project evaluates their task-specific combination and its measured limits.

A subsequent [contribution audit](CONTRIBUTION_AUDIT_ZH.md) gives analytic properties, primary-source positioning and exploratory secondary inference from existing outputs. It does not alter the inconclusive primary RR comparison, establish global priority or add training runs.
