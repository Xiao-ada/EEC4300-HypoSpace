"""CPU-only independent audit of all free-generation evidence and sampling plan."""
from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer import research_audit_data
from explorer.coverage_lora import dataset
from explorer.experiment import assess
from explorer.tasks import prepare, public_task, write_json
from explorer.upstream import evaluator

OUT = ROOT / 'results/research_audit_v7'


def main():
    if not (ROOT / '.cache/tasks.json').exists():
        prepare(json.loads((ROOT / 'config.json').read_text()))
    protocol = json.loads((OUT / 'protocol.json').read_text())
    fingerprint = hashlib.sha256((OUT / 'protocol.json').read_bytes()).hexdigest()
    for path, expected in protocol['source_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    for path, expected in protocol['data_sha256'].items():
        assert hashlib.sha256((OUT / path).read_bytes()).hexdigest() == expected, path
    old = json.loads((ROOT / 'results/final/source_manifest.json').read_text())['source_sha256']
    for path, expected in old.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    for method, expected in protocol['adapter_sha256'].items():
        path = ROOT / 'artifacts/adapters' / method.removesuffix('_iid') / 'adapters.safetensors'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, method
    # Regenerate the full observation pool and fixed-hash selection independently
    # of the model outputs. No model environment is required.
    with tempfile.TemporaryDirectory(prefix='hypospace-audit-selection-') as tmp:
        target = Path(tmp)
        with patch.object(research_audit_data, 'OUT', target), contextlib.redirect_stdout(io.StringIO()):
            research_audit_data.prepare()
        for name in ['public_tasks.json', 'scoring_references.json']:
            assert (target / name).read_bytes() == (OUT / name).read_bytes(), name
    tasks = {t['id']: t for t in json.loads((OUT / 'public_tasks.json').read_text())}
    refs = json.loads((OUT / 'scoring_references.json').read_text())['reference_keys']
    original_keys = {e['key'] for e in dataset()['universe']}
    with gzip.open(OUT / 'evidence.jsonl.gz', 'rt') as f:
        raw = [json.loads(s) for s in f]
    assert len(raw) == protocol['expected_calls'] == 4864
    groups = defaultdict(list)
    diagnostics = defaultdict(lambda: defaultdict(int))
    for r in raw:
        assert r['protocol_sha256'] == fingerprint
        assert r['error'] is None and r['budget'] == 16
        task = tasks[r['task_id']]
        assert r['cohort'] == task['cohort'] and r['prompt'] == task['prompt']
        assert set(task) == {'id', 'observations', 'cohort', 'metadata', 'prompt'}
        number = int.from_bytes(hashlib.sha256(f'{r["seed"]}:{r["step"]}:{r["task_id"]}:research-audit-v7'.encode()).digest()[:8], 'big')
        assert r['request_seed'] == random.Random(number).getrandbits(31)
        assert r['usage']['total_tokens'] == r['usage']['prompt_tokens'] + r['usage']['completion_tokens']
        assert 0 <= r['usage']['completion_tokens'] <= 128
        groups[(r['cohort'], r['method'], r['task_id'], r['seed'])].append(r)
    expected = {(t['cohort'], m, t['id'], s) for t in tasks.values() for m in protocol['methods'] for s in protocol['inference_seeds']}
    assert set(groups) == expected
    computed = defaultdict(list)
    computed_episodes = {}
    new_structure_records = []
    curve_values = defaultdict(list)
    for (cohort, method, tid, seed), rows in groups.items():
        assert len(rows) == 16
        task = tasks[tid]
        ev = evaluator(task['metadata'])
        history, seen, hits = [], set(), set()
        nv = 0
        key = cohort + '/' + method
        for step, r in enumerate(sorted(rows, key=lambda row: row['step'])):
            assert step == r['step']
            h = assess(ev, task['metadata'], public_task(task), r['raw_response'], history)
            assert h == r['outcome']
            if h['in_space']:
                seen.add(h['key'])
            if h['valid']:
                hits.add(h['key'])
                nv += 1
            if not h['in_space']:
                diagnostics[key]['parse_or_space_failures'] += 1
            elif not h['valid']:
                diagnostics[key]['observation_failures'] += 1
            elif h['key'] not in refs[tid]:
                diagnostics[key]['valid_outside_reference_attempts'] += 1
            else:
                diagnostics[key]['valid_in_reference_attempts'] += 1
            diagnostics[key]['attempts'] += 1
            history.append(h)
            scores = [nv / (step + 1), len(seen) / (step + 1), len(hits & set(refs[tid])) / len(refs[tid])]
            if step + 1 in [1, 2, 4, 8, 16]:
                for metric, value in zip(['VR', 'NR', 'RR'], scores):
                    curve_values[(cohort, str(step + 1), method, metric)].append(value)
        result = dict(zip(['VR', 'NR', 'RR'], scores))
        result['recovered'] = len(hits & set(refs[tid]))
        result['outside_reference'] = len(hits - set(refs[tid]))
        if cohort == 'fresh_3var':
            new_structure_records.append({'task_id': tid, 'method': method, 'seed': seed,
                          'recovered_old_structures': len(hits & set(refs[tid]) & original_keys),
                          'recovered_new_structures': len((hits & set(refs[tid])) - original_keys),
                          'task_requires_new_structure': not bool(set(refs[tid]) & original_keys)})
        computed[(cohort, method)].append(result)
        computed_episodes[(cohort, method, tid, seed)] = result
    summary = json.loads((OUT / 'summary.json').read_text())
    assert summary['calls'] == len(raw) and summary['episodes'] == len(groups)
    for (cohort, method), values in computed.items():
        for metric in ['VR', 'NR', 'RR', 'recovered', 'outside_reference']:
            expected = np.mean([r[metric] for r in values])
            assert abs(expected - summary['metrics'][cohort][method][metric]) < 1e-12
    for (cohort, budget, method, metric), values in curve_values.items():
        assert abs(np.mean(values) - summary['budget_metrics'][cohort][budget][method][metric]) < 1e-12
    for cohort, ids in protocol['task_ids'].items():
        draws = np.random.default_rng(4319).integers(0, len(ids), size=(10000, len(ids)))
        for control in ['base_iid', 'balanced_sft_iid', 'string_coverage_iid']:
            for metric in ['VR', 'NR', 'RR']:
                delta = np.array([np.mean([computed_episodes[(cohort, 'canonical_coverage_iid', tid, s)][metric]
                                           - computed_episodes[(cohort, control, tid, s)][metric]
                                           for s in protocol['inference_seeds']]) for tid in ids])
                item = summary['comparisons'][cohort][control][metric]
                np.testing.assert_allclose(delta.mean() * 100, item['difference_pp'], atol=1e-12, rtol=0)
                np.testing.assert_allclose(np.quantile(delta[draws].mean(axis=1) * 100, [.025, .975]),
                                           item['task_bootstrap_95_interval_pp'], atol=1e-12, rtol=0)
    costs = json.loads((OUT / 'costs.json').read_text())
    assert costs['actual_new_generation_calls'] == 4864 and costs['replayed_generation_calls'] == 0
    for key, usage_key in [('logical_prompt_tokens', 'prompt_tokens'), ('completion_tokens', 'completion_tokens')]:
        assert costs[key] == sum(r['usage'][usage_key] for r in raw)
    write_json(OUT / 'scoring_diagnostics.json', {'note': 'Post-hoc scoring artifact audit; does not change primary metric or denominator.',
                                                'by_cohort_and_method': {k: dict(v) for k, v in diagnostics.items()}})
    write_json(OUT / 'novel_structure_diagnostics.json', {
        'note': 'Post-hoc diagnostic, not the primary endpoint. Only one selected transfer task requires a structure absent from the original universe.',
        'mean_recovered_new_classes_per_episode': {m: float(np.mean([r['recovered_new_structures'] for r in new_structure_records if r['method'] == m])) for m in protocol['methods']},
        'episodes': new_structure_records})
    result = {'pass': True, 'outputs_rescored': len(raw), 'episodes': len(groups),
              'source_and_adapter_hashes_match': True, 'fresh_task_selection_reproduced': True,
              'all_metrics_and_intervals_recomputed': True, 'no_hidden_repair_or_replay': True,
              'scope': 'Saved-output CPU audit; does not recompute LLM inference or create independent training seeds.'}
    write_json(OUT / 'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
