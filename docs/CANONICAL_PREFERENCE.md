# Canonical-group preference continuation

This experiment addresses the main failure of the decoding-only pilots: a syntactically correct, non-repeated hypothesis can still violate the supplied observations. It adds supervised negative evidence to the existing coverage adapter, with a matched continuation control. No validation or test labels are used in training.

## Construction

For each of the 143 usable training observation/class pairs in v1, keep its two verified positive spellings. Enumerate the same grammar-only candidate pool, and select a negative expression that violates **exactly one** of that training task's observations. Minimize the difference in complete-answer token length, then maximize textual similarity to the positive. Add one redundant outer-parenthesis spelling of the same negative class. All four answers are revalidated; the positive and negative classes are distinct.

The prepared data use all 16 original training observation sets. The mean absolute token-length difference is 0.706 tokens and the maximum is 6; length matching is approximate, not exact for every pair. The frozen v1 coverage adapter supplies a reference margin for every pair.

## Loss

Let A+ and A- be the two finite alias sets of the positive and negative structural classes. Define

    q_theta(+ | O) = sum_{y in A+} p_theta(y | O)
    q_theta(- | O) = sum_{y in A-} p_theta(y | O)
    m_theta = log q_theta(+) - log q_theta(-).

Complete sequence probabilities include EOS, with the prompt excluded. The added preference term is

    L_pref = softplus(-beta * (m_theta - m_reference)),  beta = 0.5.

This adapts [Direct Preference Optimization](https://arxiv.org/abs/2305.18290) to finite, validated canonical alias groups. It is not claimed to be the first preference-training method or exact DPO over every possible expression spelling. Group mass makes the preference term invariant to redistributing a fixed probability mass among the represented aliases. The per-token SFT anchor itself does not have that invariance.

The two arms share the objective

    L_control = positive balanced SFT - C16(positive canonical mass)
    L_method  = L_control + L_pref.

The original coverage term and its coefficient are unchanged. A negative is used only for training a conditional proposal; it never becomes an additional synthetic observation at test time.

## Matched training

Both arms start from the same immutable v1 Canonical Coverage LoRA checkpoint. Each receives 80 new updates, learning rate 5e-5, Adam initialized identically, four group microbatches per update, and four response sequences per group. The positive/negative tensors and sampling schedule are identical; the loss term is the only intended difference. Token counts and measured runtime are published, rather than asserting identical FLOPs.

The quantized base stays frozen and the same 311,296 LoRA parameters are updated. Each final path contains the original 200 updates followed by these 80. The matched final study adds 160 updates. A separate resource-only probe completed 14 updates before both arms were restarted; those extra updates and its interrupted partial pass are disclosed separately and do not belong to either final checkpoint path.

Only response positions need a vocabulary projection because prompt and padding positions carry no loss. The backbone still processes the complete prompt, including gradients through attention to it. This equivalent implementation was checked on a small complete Qwen model and on the actual quantized checkpoint: the actual one-batch loss difference was 5.96e-8 and the measured LoRA-gradient difference was zero. This is a numerical implementation check, not a performance improvement result. The original prepared reference margins are retained; the preparation function was unchanged.

## Evaluation and attribution

Evaluate both final checkpoints with IID sampling and with [BACE](BACE_METHOD.md), plus a no-LLM uniform BACE control. BACE supplies the uniqueness guarantee; preference training must be assessed through validity and recovery under the same decoding policy. A high BACE uniqueness score alone cannot support a claim that preference training improved the model.

All methods keep 16 counted proposals, the full reference denominator, failed outputs and duplicates. Original v1 IID baselines are reported separately. Comparing the new method only with the older model would confound additional training with the new loss; the matched continuation is the key control.

Before evaluating the new checkpoints, the follow-up analysis specifies the primary comparison as preference versus matched coverage continuation **under the same BACE policy**, with validity as the primary new outcome and recovery/uniqueness as secondary outcomes. This tests the added loss's intended effect. It does not replace v1's original recovery outcome. All comparisons and intervals remain exploratory because the benchmark's v1 test observation sets were previously inspected.

Final checkpoints and hyperparameters are fixed before validation. The validation adoption rule requires uniqueness >80%, recovery above v1 coverage, and at most 2 percentage points of validity loss. All outcomes are retained if this rule fails. Any follow-up on the existing 26 v1 test observation sets is labelled exploratory, with three inference seeds and one training seed.

The comparison isolates the added grouped preference objective with this negative-construction procedure. It does not separately isolate group aggregation versus ordinary string DPO, or one-violation negatives versus arbitrary negatives. Those stronger novelty claims require further controls.

Related work also includes [GraphDPO](https://arxiv.org/abs/2605.08037), which handles preference graphs and equivalence layers induced by tied preference signals. Grouping and aggregating preference responses are therefore not themselves a global novelty claim. Here the represented groups are spellings of one official mechanistic hypothesis, and the labels come from one-observation violations. The project evaluates this task-specific construction and its added effect over a matched continuation; it does not claim to introduce structured preference optimization generally. GraphDPO was checked during the follow-up literature audit, after this implementation was written.

## Reproduce

After restoring the v1 canonical adapter and training targets using the existing repository setup:

```sh
../runtime/mlx-env/bin/python -m explorer.canonical_preference prepare
../runtime/mlx-env/bin/python -m explorer.canonical_preference train
../runtime/mlx-env/bin/python -m explorer.preference_experiment validation
.venv/bin/python scripts/report_preference.py validation
```

Use the published protocol and selection record before deciding whether to run the follow-up test. The experiment refuses to overwrite an existing prepared dataset or started training run. Reproducing in another checkout also requires the existing model lock, pinned upstream code, task cache and v1 restore steps; the runtime paths above describe this workspace's layout.
