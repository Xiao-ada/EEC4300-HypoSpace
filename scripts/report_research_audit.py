"""Score every frozen free-generation attempt; report all matched checkpoints."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer.experiment import assess
from explorer.tasks import public_task, write_json
from explorer.upstream import evaluator

OUT = ROOT / 'results/research_audit_v7'
RUN = ROOT / 'runs/research_audit_v7'


def report():
    protocol = json.loads((OUT / 'protocol.json').read_text())
    fingerprint = hashlib.sha256((OUT / 'protocol.json').read_bytes()).hexdigest()
    tasks = {t['id']: t for t in json.loads((OUT / 'public_tasks.json').read_text())}
    refs = json.loads((OUT / 'scoring_references.json').read_text())['reference_keys']
    raw = [json.loads(s) for s in (RUN / 'raw.jsonl').read_text().splitlines()]
    assert len(raw) == protocol['expected_calls']
    groups = defaultdict(list)
    for r in raw:
        assert r['protocol_sha256'] == fingerprint
        groups[(r['task_id'], r['method'], r['seed'])].append(r)
    expected = {(tid, m, s) for tid in tasks for m in protocol['methods'] for s in protocol['inference_seeds']}
    assert set(groups) == expected
    evidence, episodes, curves = [], [], []
    for (tid, method, seed), rows in groups.items():
        task = tasks[tid]
        ev = evaluator(task['metadata'])
        history, seen, valid_seen = [], set(), set()
        valid_count = 0
        for step, row in enumerate(sorted(rows, key=lambda r: r['step'])):
            assert row['step'] == step and row['budget'] == 16 and row['error'] is None
            h = assess(ev, task['metadata'], public_task(task), row['raw_response'], history)
            if h['in_space']:
                seen.add(h['key'])
            if h['valid']:
                valid_count += 1
                valid_seen.add(h['key'])
            history.append(h)
            evidence.append({**row, 'outcome': h})
            rec = {'cohort': task['cohort'], 'task_id': tid, 'method': method, 'seed': seed,
                   'queries': step + 1, 'VR': valid_count / (step + 1), 'NR': len(seen) / (step + 1),
                   'RR': len(valid_seen & set(refs[tid])) / len(refs[tid]),
                   'recovered': len(valid_seen & set(refs[tid])), 'reference_size': len(refs[tid]),
                   'outside_reference': len(valid_seen - set(refs[tid]))}
            if step + 1 in [1, 2, 4, 8, 16]:
                curves.append(rec)
            if step == 15:
                episodes.append(rec)
        assert len(rows) == 16
    metrics, comparisons, budget_metrics = {}, {}, {}
    for cohort, ids in protocol['task_ids'].items():
        def vector(method, key):
            return np.array([np.mean([r[key] for r in episodes if r['task_id'] == tid and r['method'] == method]) for tid in ids])
        metrics[cohort] = {m: {k: float(vector(m, k).mean()) for k in ['VR', 'NR', 'RR', 'recovered', 'outside_reference']} for m in protocol['methods']}
        index = np.random.default_rng(4319).integers(0, len(ids), size=(10000, len(ids)))
        comparisons[cohort] = {}
        for control in ['base_iid', 'balanced_sft_iid', 'string_coverage_iid']:
            comparisons[cohort][control] = {}
            for key in ['VR', 'NR', 'RR']:
                delta = vector('canonical_coverage_iid', key) - vector(control, key)
                comparisons[cohort][control][key] = {'difference_pp': float(delta.mean() * 100),
                            'task_bootstrap_95_interval_pp': np.quantile(delta[index].mean(axis=1) * 100, [.025, .975]).tolist()}
        budget_metrics[cohort] = {str(n): {m: {k: float(np.mean([r[k] for r in curves if r['cohort'] == cohort and r['queries'] == n and r['method'] == m]))
                                                    for k in ['VR', 'NR', 'RR']} for m in protocol['methods']} for n in [1, 2, 4, 8, 16]}
    with gzip.GzipFile(filename=str(OUT / 'evidence.jsonl.gz'), mode='wb', mtime=0) as f:
        for r in evidence:
            f.write((json.dumps(r, ensure_ascii=False) + '\n').encode())
    write_json(OUT / 'episodes.json', episodes)
    write_json(OUT / 'summary.json', {'metrics': metrics, 'comparisons': comparisons, 'budget_metrics': budget_metrics,
                'calls': len(raw), 'episodes': len(episodes), 'protocol_sha256': fingerprint,
                'primary': comparisons['known_2var']['balanced_sft_iid']['RR'],
                'limitations': ['Existing trained checkpoints, one training seed', 'Known two-variable observation tasks reused; fresh inference randomness only',
                                'Three-variable tasks newly selected from same formal rule family', 'Common fail-closed scorer differs from upstream monolithic runner',
                                'No score-threshold selection; every declared method reported; secondary intervals exploratory']})
    prefills = [json.loads(s) for s in (RUN / 'prefix_prefills.jsonl').read_text().splitlines()]
    write_json(OUT / 'costs.json', {'actual_new_generation_calls': len(raw), 'replayed_generation_calls': 0,
                'logical_prompt_tokens': sum(r['usage']['prompt_tokens'] for r in raw),
                'completion_tokens': sum(r['usage']['completion_tokens'] for r in raw),
                'generation_seconds': sum(r['seconds'] for r in raw), 'prefix_prefill_events': len(prefills),
                'physical_prefix_tokens': sum(r['tokens'] for r in prefills), 'prefix_prefill_seconds': sum(r['seconds'] for r in prefills),
                'candidate_scoring_calls': 0, 'repair_calls': 0, 'fixed_final_output_attempts_per_episode': 16,
                'note': 'Same output cap, sampler and prompt per task in all arms. All invalid/duplicate attempts counted. Completion lengths vary, so FLOPs are not exactly equal.'})
    print(json.dumps({'metrics': metrics, 'primary': comparisons['known_2var']['balanced_sft_iid']['RR'], 'calls': len(raw)}, indent=2))


if __name__ == '__main__':
    report()
