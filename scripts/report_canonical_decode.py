"""CPU re-scoring and complete reporting for the isolated v2 decoding study."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer.canonical_decode import grammar_support
from explorer.coverage_lora import dataset
from explorer.decode_experiment import METHODS, OUT, RUN, SEEDS, initialize
from explorer.experiment import assess, read_rows
from explorer.tasks import write_json
from explorer.upstream import evaluator


def export_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def paired(records, target, control, ids):
    differences = {}
    for metric in ["VR", "NR", "RR"]:
        values = []
        for tid in ids:
            def mean(method):
                return np.mean([r[metric] for r in records if r['method'] == method and r['task'] == tid])
            values.append(float(mean(target) - mean(control)))
        boot = np.random.default_rng(4300).choice(values, (10000, len(values)), replace=True).mean(axis=1)
        differences[metric] = {"difference": float(np.mean(values)),
                               "task_bootstrap_95_interval": np.quantile(boot, [.025, .975]).tolist(),
                               "paired_tasks": len(values)}
    return differences


def aggregate(split):
    d, support, cfg = initialize()
    ev = evaluator(d['metadata'])
    tasks = {t['id']: t for t in d['tasks']}
    ids, seeds = d['splits'][split], SEEDS[split]
    signature = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    evidence, curves, episodes, manifests = [], [], [], {}
    pool_answers = {h['answer']: h['key'] for h in support}
    for method in METHODS:
        for tid in ids:
            refs = set(tasks[tid]['reference_keys'])
            for seed in seeds:
                p = RUN / f'{split}_{method}_{tid}_{seed}.jsonl'
                rows = read_rows(p)
                assert len(rows) == 16, (p.name, len(rows))
                manifests[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
                history, seen, recovered, strings = [], set(), set(), set()
                valid, seconds, tokens = 0, 0., 0
                for i, r in enumerate(rows):
                    contract = r['contract']
                    assert contract == {'fingerprint': signature, 'split': split, 'task_id': tid,
                                        'method': method, 'seed': seed, 'budget': 16}
                    assert r['step'] == i and r['error'] is None
                    assert set(r['task']) == {'id', 'observations'}
                    assert r['task']['observations'] == tasks[tid]['observations']
                    h = assess(ev, d['metadata'], r['task'], r['raw_response'], history)
                    for k in ['expression', 'key', 'in_space', 'valid', 'new', 'feedback']:
                        assert h[k] == r['outcome'][k], (p.name, i, k)
                    assert pool_answers[r['raw_response']] == h['key']
                    if method.endswith('class_wor'):
                        assert h['key'] not in seen
                        assert r['decoder']['blocked_classes'] == i
                    elif method.endswith('string_wor'):
                        assert r['raw_response'] not in strings
                        assert r['decoder']['blocked_strings'] == i
                    else:
                        assert r['decoder']['blocked_classes'] == 0 and r['decoder']['blocked_strings'] == 0
                    strings.add(r['raw_response'])
                    seen.add(h['key'])
                    if h['valid']:
                        valid += 1
                        recovered.add(h['key'])
                    seconds += r['seconds']
                    tokens += r['usage']['total_tokens']
                    n = i + 1
                    curve = {'method': method, 'task': tid, 'seed': seed, 'queries': n,
                             'VR': valid/n, 'NR': len(seen)/n, 'RR': len(recovered & refs)/len(refs),
                             'recovered': len(recovered & refs), 'reference_size': len(refs),
                             'outside_reference': len(recovered - refs), 'seconds': seconds, 'tokens': tokens}
                    curves.append(curve)
                    if n == 16:
                        episodes.append(curve)
                    evidence.append(r)
                    history.append(h)
    for m in ['base_iid', 'balanced_sft_iid', 'canonical_coverage_iid', 'string_coverage_iid']:
        with (ROOT / 'results/final' / split / 'episodes.csv').open() as f:
            for r in csv.DictReader(f):
                if r['method'] != m:
                    continue
                episodes.append({k: (r[k] if k in ['method', 'task'] else int(r[k]) if k in ['seed', 'queries', 'reference_size', 'recovered', 'outside_reference'] else float(r[k])) for k in curves[0]})
    all_methods = METHODS + ['base_iid', 'balanced_sft_iid', 'canonical_coverage_iid', 'string_coverage_iid']
    metrics = {m: {k: float(np.mean([r[k] for r in episodes if r['method'] == m]))
                   for k in ['VR', 'NR', 'RR', 'seconds', 'tokens', 'outside_reference']} for m in all_methods}
    comparisons = {control: paired(episodes, 'cc_class_wor', control, ids)
                   for control in all_methods if control != 'cc_class_wor'}
    budget = {str(n): {m: {k: float(np.mean([r[k] for r in curves if r['method'] == m and r['queries'] == n]))
                          for k in ['VR', 'NR', 'RR']} for m in METHODS} for n in [1, 2, 4, 8, 10, 16]}
    directory = OUT / split
    directory.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(directory / 'evidence.jsonl.gz'), mode='wb', mtime=0) as f:
        for r in evidence:
            f.write((json.dumps(r, ensure_ascii=False) + '\n').encode())
    export_csv(directory / 'episodes.csv', episodes)
    export_csv(directory / 'curves.csv', curves)
    write_json(directory / 'raw_manifest.json', manifests)
    result = {'split': split, 'tasks': len(ids), 'seeds': seeds, 'queries_per_episode': 16,
              'new_model_calls': sum(not r['contract']['method'].startswith('uniform') for r in evidence),
              'new_uniform_draws': sum(r['contract']['method'].startswith('uniform') for r in evidence),
              'rescored_outputs': len(evidence), 'metrics': metrics, 'budget_metrics': budget,
              'cc_class_wor_vs': comparisons,
              'uncertainty_note': 'Task-paired bootstrap, averaging inference seeds within tasks; exploratory follow-up. Multiple comparisons and one training seed limit claims.',
              'verification': 'Every new raw output rescored with unchanged v1 evaluator; token/string/class exclusion invariants checked. V1 baseline rows reused without regeneration.'}
    write_json(directory / 'summary.json', result)
    write_json(directory / 'verification.json', {'pass': True, 'raw_outputs_rescored': len(evidence),
                                                'methods': METHODS, 'excluded_failed_attempts_in_formal_run': 0})
    return result


def feasibility():
    d = dataset()
    support = grammar_support(d['metadata'])
    ev = evaluator(d['metadata'])
    keys = {h['key'] for h in support}
    tasks = {t['id']: t for t in d['tasks']}
    details = []
    for tid in d['splits']['test']:
        task = tasks[tid]
        refs = set(task['reference_keys'])
        legal = {h['key'] for h in support if assess(ev, d['metadata'], task, h['answer'], [])['valid']}
        assert legal <= refs
        details.append({'task': tid, 'reference_size': len(refs), 'support_valid_classes': len(legal),
                        'RR_ceiling_at_16': min(16, len(legal))/len(refs),
                        'NR_ceiling_if_VR_is_1': min(16, len(legal))/16,
                        'NR_ceiling_if_VR_is_at_least_0_9': min(1, len(legal)/16 + .1)})
    result = {'budget': 16, 'support_classes': len(keys),
              'scope': 'Exact finite grammar used by v2; all support-valid classes are reference classes. Not a universal theorem about arbitrary unseen strings or other benchmark settings.',
              'mean_RR_ceiling_at_16': float(np.mean([r['RR_ceiling_at_16'] for r in details])),
              'macro_NR_upper_bound_at_macro_VR_0_9': min(1, np.mean([r['support_valid_classes'] for r in details])/16 + .1),
              'inequality': 'NR <= min(1, K_valid_support / N + 1 - VR): distinct valid <= K_valid_support; distinct invalid <= number invalid. Average the uncapped inequality to constrain macro metrics.',
              'details': details}
    write_json(OUT / 'score_feasibility.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['validation', 'test', 'feasibility'])
    args = parser.parse_args()
    result = feasibility() if args.split == 'feasibility' else aggregate(args.split)
    print(json.dumps({k: v for k, v in result.items() if k in ['split', 'metrics', 'new_model_calls', 'new_uniform_draws', 'mean_RR_ceiling_at_16', 'macro_NR_upper_bound_at_macro_VR_0_9']}, indent=2))


if __name__ == '__main__':
    main()
