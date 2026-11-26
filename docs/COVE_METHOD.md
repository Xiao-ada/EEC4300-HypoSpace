# COVE: Compositional Observation-Verified Execution

COVE is a small learned executor combined with canonical-class selection for a frozen language model. The project tests whether learning observation consistency can improve valid hypothesis coverage more effectively than the existing coverage-adapted LLM alone. The method name is a local project label, not a claim of a globally new neural-module architecture.

## Setting and scope

We retain the original task-derived HypoSpace Boolean study: variables x/y, AND/OR/NOT, depth 2, 48 observation tasks split into 16 training / 6 validation / 26 test tasks. This is not a reproduction of the paper's complete dataset, models or domains. Test observation tasks were already used in the earlier project; this is an exploratory follow-up, not a newly untouched confirmation set.

HypoSpace scores structural/mechanistic classes, not only complete truth-table equivalence. We keep that distinction: algebraic absorption or De Morgan transformations are not added to the official class equivalence. The inventory contains 33 classes covered by the original training targets, each with two fixed represented answer aliases. The full official reference universe has 34 classes; its problematic remaining class is not removed from any recovery denominator.

The inventory is the union of training classes, combined with the public task syntax to choose a small AST representative. It is the same inventory for every task; it is not built from a test task's compatible solution set. Learning may reuse structures encountered during training, so this evaluation supports generalization to observation conditions, not unseen structural families.

## 1. Learn a compositional executor

For an expression tree h and Boolean input a, define the predicted output p_theta(h,a) recursively. Variable leaves use the given input bits. Internal AND/OR nodes apply separate shared 2→16→1 MLPs; NOT uses a shared 1→16→1 MLP. Hidden activations are tanh, with sigmoid at each operator's output. AND/OR average the logits of the two argument orders to encode commutativity.

The architecture supplies tree composition, operator identities, variable input mapping and commutativity. It does **not** supply numeric AND/OR/NOT truth tables to the learned forward pass. There are 179 trainable parameters. Native MLX and portable NumPy implementations agree within 1.8e-6 on the stored catalog predictions.

Let c_th indicate that catalog class h belongs to training task t's compatible reference set. Training uses 260 observed input/output labels from compatible training hypotheses, and 16×33=528 task/class compatibility labels, all from the original training split. For O_t the observed examples, define

```text
match_theta(h, a, y) = p_theta(h,a)^y * (1-p_theta(h,a))^(1-y)
v_theta(t,h) = product_{(a,y) in O_t} match_theta(h,a,y)

L = mean_positive_observed_examples BCE(y, p_theta(h,a))
    + 0.25 * mean_training_task_class_pairs BCE(c_th, v_theta(t,h))
```

All three initializations (4306 primary, 4307/4308 replications) use 2,000 full-batch Adam updates, learning rate 0.01. The primary seed, compatibility coefficient 0.25 and inference coefficient 10 are fixed before validation, with no test-based checkpoint selection. Validation/test labels and the auxiliary generalization probe never enter gradients.

Training logs, weights and frozen protocol are in `results/all80/executors/`, `executor_training_summary.json` and `protocol.json`. The first run took 18.71 seconds including compilation; the other runs took about 9.3 seconds each. These times exclude the earlier LoRA training and candidate scoring.

## 2. Score the fixed catalog with the frozen LLM

The foundation model is the pinned 4-bit Qwen2.5-1.5B-Instruct and the previously selected coverage-continuation adapter. The adapter is unchanged in this follow-up. For each class h, sum the probabilities of its two represented complete answer strings, including EOS:

```text
q_phi(h | O) = sum_{s in the two fixed aliases of h} P_phi(s | O)
```

This is represented alias mass, not the full probability of every possible wording of the class. Candidate sequences are scored by teacher forcing. A shared prompt prefix and batches of eight reduce repeated work. Each task costs 66 complete-sequence evaluations in 9 candidate batches plus one prefix prefill. Three spot checks against full unbatched teacher forcing differ by less than 0.008 log probability; minor quantized GEMM shape differences are retained and disclosed.

This stage does not validate the candidates against observations or inspect test reference membership. Frozen adapter SHA256 is `3a50c5fa491aca041fbda7499de53700b4dac6841be7bae090147be823d818ac`.

## 3. Observation-conditioned energy reweighting

For a public task's given observations only:

```text
ell_theta(h; O) = sum_{(a,y) in O} log match_theta(h,a,y)
log_weight(h) = log q_phi(h | O) + 10 * ell_theta(h; O)
```

This is a product-of-experts / energy reweighting rule. It is **not** claimed to be an exact Bayesian posterior: the language-model factor is already conditioned on O. The coefficient sharpens differences between observation-compatible and incompatible catalog members. No exact operator execution, constraint solver, test membership labels or validator feedback is used by the COVE proposal.

For each class draw independent standard Gumbel noise g_h, sort `log_weight(h)+g_h`, and return the first N classes. This implements categorical sampling without replacement. Each class uses its fixed first alias when emitted. Unlike free autoregressive generation, the output is a selection from a finite catalog; that restriction is a substantive part of the method and must be stated when presenting the scores.

## 4. Two explicit budget protocols

The original project used N=16. The official README's Boolean example uses `--query-multiplier 1.0`; the pinned runner sets `N=max(1,int(K*query_multiplier))`, so the additional experiment uses N=K. Test K ranges from 5 to 20. The harness supplies K to **all** methods as a budget; no compatible class identities are supplied to the learned proposal.

In either protocol, every output counts, including invalid ones. No hidden rejection sampling, repaired output replacement or denominator shrinkage occurs. The same common fail-closed parse/space gate is applied to every method, and the full original reference set remains the RR denominator. This common gate differs slightly from the upstream monolithic runner, so absolute numbers are not paper leaderboard results.

Why the budget matters: if every truly valid class belongs to the intended reference space, the unique valid count is at most K and the unique invalid count is at most N(1-VR). Therefore:

```text
NR <= K/N + 1 - VR
```

For the original test tasks, mean K=9.1923 and N=16. Macro VR≥80% implies macro NR≤77.45%. Thus all three 80% targets cannot be simultaneously attained under that fixed protocol inside the intended reference space. Upstream parser/enumerator artifacts are not used to evade this bound. N=K changes this constraint; it is an additional public benchmark setting, not a relabeling of the old results.

At N=K, with unique candidates and no valid out-of-reference hits, VR and RR are numerically equal. NR=100% is guaranteed by catalog selection without replacement. These three numbers are consequently related, rather than three independent demonstrations of model reasoning.

## Controls and attribution

We include base IID, frozen-adapted IID, the same LLM catalog scores without COVE, uniform catalog sampling, COVE without the LLM, and an exact symbolic solver control. The latter alone uses supplied exact operator rules. The same class ordering noise is shared across catalog controls.

The main module comparison is **COVE+LLM vs the identical LLM catalog sampler without COVE**: same catalog, scores, final budget and unique-class sampling. It isolates the benefit of learned consistency reweighting. COVE-only and exact-symbolic controls match COVE+LLM on final test metrics. Thus the learned execution module works in this setting, but an incremental contribution from the LLM factor is **not demonstrated**. There is no need to hide this simple explanation of the strong scores.

An auxiliary probe evaluates the frozen learned operators on 1,024 unique depth-3–6 programs using x/y/z, all semantically dependent on z. All eight assignments are checked. Variable-to-input mapping is supplied externally; the probe tests learned operator composition, not learned new variable identities. It is neither a three-variable HypoSpace LLM experiment nor an additional model selection set.

## Reproduction

For CPU-only verification, create the environment from `requirements-lock.txt`, then run:

```bash
.venv/bin/python scripts/verify_all80.py
.venv/bin/python scripts/probe_executor_generalization.py
```

The verifier independently reconstructs rankings from saved LLM scores, observed data and JSON executor weights, and re-scores all 18,981 public outputs. It checks baseline replay, new extra-call seeds, original code hashes, budget accounting, inventory/AST semantics and all summary metrics. It does not recompute every LLM forward pass.

For a fresh Apple Silicon clone, first follow the root README's pinned MLX environment/model preparation. Preserve the shipped outputs before recomputing; training intentionally refuses to overwrite completed evidence:

```bash
../runtime/mlx-env/bin/python -m explorer fetch
../runtime/mlx-env/bin/python -m explorer prepare
../runtime/mlx-env/bin/python scripts/restore_preference_adapters.py
# Move only the public all80 evidence; keep original final/v5 evidence for baseline replay.
mv results/all80 .cache/all80-published
../runtime/mlx-env/bin/python -m explorer.learned_executor
../runtime/mlx-env/bin/python -m explorer.catalog_scores validation
../runtime/mlx-env/bin/python -m explorer.all80_experiment validation
../runtime/mlx-env/bin/python -m explorer.catalog_scores test
../runtime/mlx-env/bin/python scripts/generate_adaptive_iid_extras.py
../runtime/mlx-env/bin/python -m explorer.all80_experiment test
../runtime/mlx-env/bin/python scripts/check_catalog_scores.py
../runtime/mlx-env/bin/python scripts/verify_all80.py
../runtime/mlx-env/bin/python scripts/probe_executor_generalization.py
../runtime/mlx-env/bin/python scripts/report_all80.py
```

These steps reuse the published immutable IID prefixes and generate 42 needed extra calls for larger N=K tasks. They reproduce this follow-up, not all earlier LoRA training. To regenerate the original prefixes as well, use the earlier full-reproduction instructions. Different hardware/library kernels need not reproduce floating-point logits or stochastic rankings bitwise.

## Research positioning

The project-specific design couples weakly supervised shared operator modules, official structural classes, represented-alias LLM masses and observation-energy sampling under a transparent budget. Neural modular composition and Gumbel sampling are established ideas; claiming global invention of them would be incorrect. The existing exact Boolean solver is already strong in this tiny formal domain, limiting the research necessity of the neural/LLM system despite high metrics. Scaling to richer domains, unknown operators or open-ended hypotheses remains untested.

It differs from the teammate's DCHG: there is no selected unobserved input, desired prediction disagreement or history-conditioned prompt generation. The learned consistency model uses the original given observations; the finite catalog and no-replacement rule provide structural coverage.

Primary references:

- [Chen et al., HypoSpace](https://proceedings.mlr.press/v306/chen26bz.html) and [official README](https://github.com/CTT-Pavilion/_HypoSpace/blob/main/README.md).
- [Andreas et al., Neural Module Networks, CVPR 2016](https://openaccess.thecvf.com/content_cvpr_2016/html/Andreas_Neural_Module_Networks_CVPR_2016_paper.html): shared learned modules assembled by structure.
- [Kool et al., Stochastic Beams and Gumbel-Top-k, ICML 2019](https://proceedings.mlr.press/v97/kool19a.html): sampling without replacement.
- [Pinned official budget implementation](https://github.com/CTT-Pavilion/_HypoSpace/blob/c69e9318577b34b5b896996571aefd4ba6053f58/boolean/boolean_benchmark.py#L713).
