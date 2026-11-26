# Matched continuation adapters

Both adapters start from the released v1 canonical-coverage checkpoint and add 80 fixed updates. The base is still the exact four-bit model in `model.local_mlx.lock.json`; these files contain only the 311,296 trainable LoRA parameters.

- `coverage_continuation`: retains the original coverage/SFT objective.
- `canonical_preference`: adds canonical-group DPO with one-observation-violating training negatives.

The preference term was **not selected** on validation. The validation-selected deployment is `coverage_continuation` with BACE. The second checkpoint is provided for complete comparison and reproducibility, not presented as the winning method.

`manifest.json` includes hashes and the exact training summary. After the existing model setup, run:

```sh
.venv/bin/python scripts/restore_preference_adapters.py
../runtime/mlx-env/bin/python -m explorer.preference_experiment validation
```

The public prompt-only snapshots supply the same wording used in v1. New evaluation files are stored under the ignored `runs/canonical_preference_v5/evaluation` directory. Do not mix outputs from a different checkpoint or protocol into that run; the fingerprint checks reject mismatches. Restoring published adapters does not require retraining.

See [method](../../docs/CANONICAL_PREFERENCE.md), [decoding](../../docs/BACE_METHOD.md), and [results](../../docs/OPTIMIZATION_RESULTS_ZH.md).
