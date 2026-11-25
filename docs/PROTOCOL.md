# Executed experiment protocol

The matched LoRA experiment has completed. See [the method](METHOD.md), [English results](RESULTS_EN.md), [root README](../README.md) and [machine-readable final reports](../results/final/test/summary.json).

Frozen 16/6/26 observation split; 80 shared SFT updates plus three matched 120-update continuations; rank 8 q/v LoRA on the last eight blocks; 480 validation and 6240 test calls, temperature 1, 16 calls per episode, three test inference seeds. All formal methods use the same direct MLX backend. Earlier HTTP diagnostics are not formal baseline rows.

Full reference denominators and common fail-closed scoring are unchanged. Generator/validator mismatches are exposed. Task-bootstrap comparisons average repetitions within each task. Complexity and equal-valid-draw diagnostics are explicitly exploratory. No parameters, split or method selection changed after test generation began.

The original narrative is in PROTOCOL_PRE_RUN.md. The immutable plan JSON retains its pre-execution status; actual state is results/STATUS.json. Published evidence can be independently rescored with scripts/verify_results.py without a GPU or model inference.
