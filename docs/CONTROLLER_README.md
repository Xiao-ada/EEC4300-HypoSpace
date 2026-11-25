> Archived controller prototype. Run the commands below from the repository root. The current LoRA design is in PROPOSAL_ZH.md; this prototype does not train LLM adapters.

# Learning to Explore HypoSpace

EEC4300 course project candidate: a learned controller selects structural guidance for a frozen language model, optimizing the chance of discovering another valid, canonically distinct Boolean hypothesis.

**Current status: implementation, protocol checks, and 256 real local-model training calls completed. Controller training and held-out evaluation are paused for method review; no performance improvement is claimed.** See [the Chinese proposal](CONTROLLER_PILOT_ZH.md) for the decision-ready method and [the experiment protocol](CONTROLLER_PROTOCOL.md) for the exact scope.

## Method

For each observation set, the controller observes the revealed constraints, elapsed budget, canonical structure statistics, previous success/duplication rates, and recent failures. It selects one operation: ordinary generation, a root-operator constraint, a complexity direction, repair of an invalid candidate, or mutation of a valid candidate.

Two regularized logistic predictors estimate validity and novelty conditional on validity. Their product estimates the probability that an operation will discover a new valid hypothesis. Training uses automatically verified trajectories on training observation sets. Test-time parameters are frozen; the state evolves as answers arrive. No test reference set is shown to the controller or LLM.

This is a proposed task-specific combination, not a claim that learned routing, bandits, or coverage rewards are globally new.

## Quick start

Python 3.12 is the tested environment. The controller and evaluator need only NumPy and SymPy; GPU inference is a separate service. Use a project environment, not an existing system environment.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m explorer fetch
.venv/bin/python -m explorer prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m explorer smoke
```

`fetch` downloads checksum-pinned upstream files into ignored `.cache/upstream`. No upstream source is redistributed in this repository. `smoke` uses an intentionally privileged synthetic fixture and writes only to ignored `.cache/synthetic_smoke`; those outputs are not LLM evidence and cannot be used as real-model checkpoints.

## Real experiments

Choose a provider or local GPU endpoint, model, and resource/cost limit first. Copy `.env.example` to a local `.env` and fill it in. A local vLLM service can use `http://127.0.0.1:8000/v1`; remote providers require HTTPS and a key. Do not commit `.env`.

```bash
.venv/bin/python -m explorer preflight
.venv/bin/python -m explorer collect --limit-tasks 2
# Inspect the first 32 calls, latency, responses, and api_ledger.json.
# Resume the same run directory after accepting the runtime/cost estimate.
.venv/bin/python -m explorer collect
.venv/bin/python -m explorer train
.venv/bin/python -m explorer evaluate
.venv/bin/python -m explorer summarize
```

The default run directory is `runs/pilot`. Completed steps are resumed rather than regenerated. Use the same run directory for the whole experiment: the persistent ledger counts attempted HTTP requests, including failed requests, across collection and evaluation. No automatic retries or uncounted repair calls are made. If a provider omits usage accounting, further requests stop rather than assuming zero token cost. Token reservations for failed requests remain conservative estimates; this is not provider billing reconciliation.

Default screening size: 16 training tasks × 16 calls = 256 training calls; 6 held-out tasks × 2 repetitions × 5 methods × 16 calls = 960 evaluation calls. Total 1,216 calls, with a 1,400-call stop limit in this run directory. Optional validation collection uses another 96 calls. This is a pilot for selecting a group project, not a full benchmark evaluation.

The five methods are memory baseline, fixed structural rotation, random operation selection, learned selection, and learned selection without history features. The fixed baseline is **not** the paper's oracle-allocated stratified decoder.

## Outputs and publication

- Raw prompts, responses, usage, outcomes, and checkpoints: ignored `runs/pilot/`.
- Data consistency audit and split IDs: `results/data_audit.json`.
- Real aggregate metrics, paired intervals, curves CSV, and SVG: `results/pilot/`, only after real evaluation.
- [Server instructions](SERVER.md), [publication steps](PUBLICATION.md), and [group comparison template](../results/group_comparison_template.csv).

```bash
.venv/bin/python scripts/audit_upload.py
```

The course requires a public GitHub repository and a ten-minute group video in which every member presents. An empty private [project remote](https://github.com/Xiao-ada/EEC4300-HypoSpace) is connected and authenticated. Project source has not been pushed; public release follows method review and the course submission requirement. The institutional manual, account credentials, private network addresses, and course source documents are deliberately absent.

## Benchmark compatibility

We reuse unchanged ASTs of the pinned upstream prompt, parser, canonicalizer, and validator methods. The runner has an explicit fail-closed parse/space gate and counts every generation attempt. It therefore is a controlled reimplementation, not an exact reproduction of the paper's reported scores. The current upstream generator/validator consistency issue and all relevant differences are documented in [PROTOCOL.md](CONTROLLER_PROTOCOL.md).

## References

- Chen et al. [HypoSpace, ICML 2026](https://proceedings.mlr.press/v306/chen26bz.html).
- [Official source](https://github.com/CTT-Pavilion/_HypoSpace), pinned in `upstream.lock.json`.
- [DAK-UCB](https://arxiv.org/abs/2603.23140), related diversity-aware learned routing.
- [GAPO, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1649/), related group-aware training.

The team should choose the license and fill author contributions before final publication. Upstream licensing must be checked before redistributing any upstream source; this starter instead fetches verified copies locally.
