> Archived controller prototype. The current method plan is in PROPOSAL_ZH.md and PROTOCOL.md.

# Experimental protocol

## Scope and split

The pilot uses the pinned HypoSpace Boolean hypothesis language, extended operator set {AND, OR, NOT}, depth 2, and the upstream mechanistic canonicalizer. Enumerated truth tables create all nonempty observation sets with one to three observed input pairs; only sets with at least four compatible reference hypotheses are eligible. The observation set ID is derived from its content. We sample 16 train, 6 validation, and 6 test observation sets with split seed 4300 before any LLM calls. Unused eligible tasks remain unused. This is a controlled pilot subset, not the paper's original sample selection.

The canonical expression universe contains 34 hypotheses in the tested environment, and 48 observation sets meet the criterion. Shared expressions across different constraints are possible. The split establishes generalization to held-out constraints, not disjoint expression families. `public_task` removes references before constructing prompts and predictor inputs.

## Validator compatibility and audit

Unchanged upstream AST methods implement the prompt, parser, canonical key, in-space check, and observation validator. The module loader avoids unrelated SciPy/provider dependencies without rewriting those method bodies. All downloaded files are checksum verified against the pinned commit.

There are upstream generator/validator inconsistencies involving NOR recognition/depth. The serialized reference expression NOT (x OR y) is rejected under the extended setting. The full setting has more disagreements and is not the default. The audit counts rejected serialized reference expressions, not provably unreachable equivalence classes. The reference set is retained unchanged.

Our runner limits incoming text to allowed task tokens before passing it to SymPy, and requires successful parsing and `_in_space` before applying the upstream observation validity method. This extra fail-closed gate differs from the monolithic upstream runner and is explicitly applied to every method. We report our controlled protocol, not numerical replication of the paper. Reference membership is only used after generation in RR calculation. A valid generated key missing from the reference is exposed as a diagnostic, not silently added to the denominator.

## Metrics and budgets

- VR: valid proposals / counted generation attempts, including malformed outputs and provider failures in the attempt denominator.
- NR: canonically unique in-space proposals / counted attempts, without requiring observational validity.
- RR: distinct valid generated reference keys / enumerated compatible reference keys.
- Each completion, repair, or mutation costs one generation attempt. No free rejection sampling, hidden retry, or programmatic answer enumeration is allowed in real mode.
- Keep identical model, temperature, output limit, task split, and per-task generation budget across methods. All methods retain the upstream full prior-answer prompt. Baseline-specific added instruction tokens are separately accounted.
- Training generation cost is recorded separately from inference cost. Report both; controller training is not free.

Fixed rotation is a practical structural heuristic, not oracle stratification. Random action selection is the essential control for the operation library. The no-history ablation removes predictor history features but retains the LLM history prompt and availability mask. Checkpoints contain training IDs, backend/model provenance, and experiment fingerprints. Synthetic fixtures cannot evaluate real models.

The endpoint adapter expects a text chat completion, token usage, temperature, and max_tokens support. It does not silently switch protocols or remove unsupported parameters. A model requiring a different interface or thinking budget must be adapted before collecting comparable trajectories.

## Reporting and interpretation

Report all preregistered test tasks and methods, including zero/negative improvements. The plot shows mean RR versus attempts; the table includes VR, NR, RR, sample counts, and completion status. Repetitions are averaged within task before paired bootstrap uncertainty; hypotheses are not treated as independent experimental units. The small test size supports screening only.

Do not claim a theoretical coverage bound has been broken: an adaptive sampler changes the fixed-distribution setting. Do not call feature balance true hypothesis-space coverage. The learned score estimates immediate discovery probability and does not guarantee globally optimal allocation.

## Reproducibility

Keep dependency lock, upstream lock, config, data audit, split IDs, model identity/version, full provider settings, controller checkpoints, raw trajectories and call ledger. Raw logs stay outside the publication bundle until reviewed; aggregate results and required reproduction files can be deliberately exported. Prefixes of a 16-call trajectory provide the 8-call curve point without extra generation.
