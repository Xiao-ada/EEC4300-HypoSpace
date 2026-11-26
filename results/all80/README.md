# COVE experiment evidence

- `test/summary.json`: final macro VR/NR/RR for both N=K and N=16 protocols.
- `test/episodes.json`: all 1,404 test method/task/seed/protocol episodes.
- `test/evidence.jsonl.gz`: all 17,685 test outputs, including invalid outputs and baseline replay.
- `validation/`: separate validation scores and 1,296 raw outputs.
- `protocol.json`, `evaluation_protocol_*.json`, `selection.json`: frozen training/evaluation choices, source hashes and pre-test primary selection.
- `executors/`: 179-parameter JSON weights and logs for three independent initializations.
- `bank.json`: the fixed 33-class, training-derived inventory, aliases and AST representatives.
- `lm_scores/`: actual complete-answer teacher-forced LLM scores, with prompt, adapter hash and cost.
- `iid_extras.jsonl`: 42 new genuine IID generations; older prefixes are linked through the retained final/v5 public evidence.
- `verification.json`: CPU replay of all raw outputs and independent ranking reconstruction.
- `catalog_score_verification.json`: three on-device numerical checks of cached versus full scoring.
- `costs.json`, `paired_differences.json`, `scope_audit.json`: additional compute, task-level descriptive intervals, and inventory limitations.
- `executor_generalization_filtered.json`: reproducible 1,024-program auxiliary depth/variable probe, with every program and label. `executor_generalization.json` is an earlier unfiltered pilot and is not evidence that all its programs were novel or deeper than training.
- `metrics.png` / `.pdf`: standalone two-protocol figure.

Scores belong to a finite-catalog structured system. COVE-only and exact-symbolic controls match the LLM-coupled method, so the LLM's incremental final-metric contribution is not established. N=K and N=16 must remain separate. See the [complete method](../../docs/COVE_METHOD.md) and [result report](../../docs/ALL80_RESULTS_EN.md).
