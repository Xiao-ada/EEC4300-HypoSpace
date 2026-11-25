# Final held-out results

Real 4-bit Qwen2.5-1.5B-Instruct experiments on 26 held-out observation sets, three inference repetitions and 16 calls per episode. The three inference seeds do not represent three independent adapter-training runs. The single training seed is 4300.

| Method | VR | NR | RR |
|---|---:|---:|---:|
| Base IID | 15.30% | 35.90% | 13.67% |
| Balanced SFT | 30.61% | 68.51% | 36.86% |
| Canonical coverage LoRA | 33.73% | 64.34% | 37.76% |
| String coverage ablation | 37.82% | 59.54% | 37.61% |
| Base + history | 13.06% | 26.20% | 10.92% |

Canonical coverage minus base RR: +24.09 percentage points. Canonical coverage minus balanced SFT RR: +0.89 points; paired task-bootstrap 95% interval [-1.97, +3.72] points. The task-bootstrap interval includes zero; an additional benefit over matched SFT is uncertain.

All five methods, fixed data and matched adapter-training paths are retained. Shared warm-up is counted once in total project cost; each adapter has a 200-update path. Scoring keeps full reference denominators and exposes validator/generator mismatches. This is a small-model task-derived study, not replication of paper tables, cross-domain generalization or a matched comparison against the teammate DCHG screenshot.

See [method](METHOD.md), [machine-readable test report](../results/final/test/summary.json), [raw evidence](../results/final/test/evidence.jsonl.gz) and [root README](../README.md).
