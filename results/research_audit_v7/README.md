# Fixed-budget free-generation evidence

The protocol was committed before new model outputs in `f6ab465`. There is no score threshold or test-based checkpoint selection. The four arms are the base model and the original matched 200-update SFT, canonical-coverage and string-coverage checkpoints.

- `protocol.json`: immutable settings, primary comparison and source/model/data hashes.
- `public_tasks.json`: only observations, metadata, prompt and task/cohort IDs; the model runner's complete task input.
- `scoring_references.json`: full reference keys for the separate offline scorer; never read by the model runner.
- `evidence.jsonl.gz`: all 4,864 genuine new free-generation attempts and their later scores. No historical output replay.
- `episodes.json`: all 304 complete method/task/seed episodes.
- `summary.json`: every declared method in both cohorts, all metrics and paired differences; cohorts are not merged.
- `verification.json`: independent CPU score/ranking-plan and interval checks.
- `costs.json`: actual calls/tokens/times, with prompt cache work separated.
- `scoring_diagnostics.json`: invalid outputs and reference-external validity artifacts; no denominator changes.
- `reference_representation_audit.json`: upstream representative spelling mismatches, not a claim of class unreachability.
- `transfer_difficulty.json`: data-only audit; just one of the twelve selected transfer tasks strictly requires a structure absent from the old universe.
- `novel_structure_diagnostics.json`: post-hoc old/new structure-hit diagnostics, not a replacement primary endpoint.
- `metrics.*`, `coverage.*`: standalone metric and budget figures.

The 26 two-variable observation tasks were previously used; two new sampling seeds do not create a new untouched dataset or independent training runs. The twelve three-variable observation tasks were selected before model runs using fixed hashes and no performance filter. They are a limited variable-count transfer check, not comprehensive unseen-family generalization.

CPU verification: `python scripts/verify_research_audit.py`. Current [Chinese report](../../docs/RESEARCH_RESULTS_ZH.md) and [English report](../../docs/RESEARCH_RESULTS_EN.md) retain negative or inconclusive conclusions. Historical catalog-selection evidence stays in `results/all80/` and is not presented as unrestricted generation.
