# Optimization follow-up results

| Method | Validity | Uniqueness | Recovery |
|---|---:|---:|---:|
| Base IID | 15.30% | 35.90% | 13.67% |
| Balanced SFT | 30.61% | 68.51% | 36.86% |
| Coverage v1 | 33.73% | 64.34% | 37.76% |
| Coverage +80 / IID | 39.90% | 64.42% | 41.02% |
| Preference +80 / IID | 39.66% | 59.86% | 37.52% |
| Coverage +80 / BACE | 36.38% | 81.49% | 50.34% |
| Preference +80 / BACE | 36.22% | 81.25% | 48.96% |
| Uniform / BACE | 28.93% | 83.89% | 40.03% |


Validation-selected deployment: **Coverage +80 / BACE**. The added preference loss was not selected on validation. Test metrics do not change that selection.

Same 26 Boolean observation tasks, three inference seeds, and 16 counted attempts. These task observations were reported in v1; this is an exploratory follow-up, not an untouched confirmation set. The new preference and continuation arms each add 80 matched updates from the same v1 coverage checkpoint.

Preference+BACE versus matched continuation+BACE: validity difference -0.16 percentage points, task-bootstrap 95% interval [-2.16, +2.00]; recovery difference -1.38, interval [-5.18, +2.43]. One training seed; secondary intervals are not multiplicity-adjusted.

Uniqueness comes from a decoding guarantee, not proof of learned diversity. BACE keeps IID sampling until another duplicate would make 13 distinct structures unreachable at N=16. Class exclusions then block every represented alias. The observation-violating negative pairs target validity during training. Both components require their respective controls.

README guides (>90% validity, >80% uniqueness, >80% recovery) are setting-dependent diagnostic references, not course marks. The system's remaining gaps are disclosed above. Selection was frozen on validation before test; all arms are published.

See [full discussion](OPTIMIZATION_RESULTS_ZH.md), [training method](CANONICAL_PREFERENCE.md), [decoding method](BACE_METHOD.md), and [raw evidence](../results/canonical_preference_v5/test/evidence.jsonl.gz).
