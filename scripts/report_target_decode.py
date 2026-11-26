"""Publish BACE raw evidence, independently rescore it, and pair with v1."""
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
from explorer.coverage_lora import dataset
from explorer.experiment import assess, read_rows
from explorer.target_decode import METHODS, ORIGINAL, OUT, RUN, initialize, intervene
from explorer.tasks import write_json
from explorer.upstream import evaluator
from scripts.report_canonical_decode import export_csv, paired


def aggregate(split):
    d, support, cfg = initialize()
    ev = evaluator(d['metadata'])
    tasks = {t['id']: t for t in d['tasks']}
    ids, seeds = d['splits'][split], cfg['seeds'][split]
    signature = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    pool = {h['answer']: h['key'] for h in support}
    with gzip.open(ROOT / 'results/final' / split / 'evidence.jsonl.gz', 'rt') as f:
        original = {(r['contract']['method'], r['contract']['task_id'], r['contract']['seed'], r['step']): r
                    for r in (json.loads(l) for l in f)}
    evidence, curves, episodes, manifests = [], [], [], {}
    counts = defaultdict(int)
    for method in METHODS:
        prefix = method.split('_')[0]
        for tid in ids:
            refs = set(tasks[tid]['reference_keys'])
            for seed in seeds:
                p = RUN / f'{split}_{method}_{tid}_{seed}.jsonl'
                rows = read_rows(p)
                assert len(rows) == 16, (p.name, len(rows))
                manifests[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
                history, seen, recovered = [], set(), set()
                valid, seconds, tokens, active_count = 0, 0., 0, 0
                for i, r in enumerate(rows):
                    assert r['contract'] == {'fingerprint': signature, 'method': method, 'task_id': tid,
                                              'split': split, 'seed': seed, 'budget': 16}
                    assert r['step'] == i and r['error'] is None
                    assert set(r['task']) == {'id', 'observations'}
                    assert r['task']['observations'] == tasks[tid]['observations']
                    assert r['prompt'] == original[('canonical_coverage_iid', tid, seed, i)]['prompt']
                    h = assess(ev, d['metadata'], r['task'], r['raw_response'], history)
                    for k in ['expression', 'key', 'in_space', 'valid', 'new', 'feedback']:
                        assert h[k] == r['outcome'][k], (p.name, i, k)
                    active = intervene(len(seen), i)
                    assert r['decoder']['active'] == active
                    assert r['decoder']['distinct_before'] == len(seen)
                    if active:
                        active_count += 1
                        assert r['raw_response'] in pool
                        if method.endswith('_class'):
                            assert h['key'] not in seen
                    if r['replay']:
                        assert not active and active_count == 0
                        source = original[(ORIGINAL[prefix], tid, seed, i)]
                        for k in ['raw_response', 'prompt', 'request_seed', 'usage', 'seconds']:
                            assert r[k] == source[k]
                        counts['replayed_model_calls'] += 1
                        counts['replayed_model_tokens'] += r['usage']['total_tokens']
                    elif prefix != 'uniform':
                        counts['new_model_calls'] += 1
                        counts['new_model_tokens'] += r['usage']['total_tokens']
                    else:
                        counts['uniform_draws'] += 1
                    valid += int(h['valid'])
                    if h['in_space']:
                        seen.add(h['key'])
                    if h['valid']:
                        recovered.add(h['key'])
                    seconds += r['seconds']
                    tokens += r['usage']['total_tokens']
                    n = i + 1
                    curve = {'method': method, 'task': tid, 'seed': seed, 'queries': n,
                             'VR': valid/n, 'NR': len(seen)/n, 'RR': len(recovered & refs)/len(refs),
                             'recovered': len(recovered & refs), 'reference_size': len(refs),
                             'outside_reference': len(recovered - refs), 'seconds': seconds, 'tokens': tokens,
                             'intervention_calls': active_count}
                    curves.append(curve)
                    if n == 16:
                        if method.endswith('_class'):
                            assert len(seen) >= 13
                        episodes.append(curve)
                    evidence.append(r)
                    history.append(h)
    originals = ['base_iid', 'balanced_sft_iid', 'canonical_coverage_iid', 'string_coverage_iid']
    with (ROOT / 'results/final' / split / 'episodes.csv').open() as f:
        for r in csv.DictReader(f):
            if r['method'] not in originals:
                continue
            row = {k: (r[k] if k in ['method', 'task'] else int(r[k]) if k in ['seed', 'queries', 'reference_size', 'recovered', 'outside_reference'] else float(r[k]))
                   for k in curves[0] if k != 'intervention_calls'}
            row['intervention_calls'] = 0
            episodes.append(row)
    methods = METHODS + originals
    metrics = {m: {k: float(np.mean([r[k] for r in episodes if r['method'] == m]))
                   for k in ['VR', 'NR', 'RR', 'seconds', 'tokens', 'outside_reference', 'intervention_calls']}
               for m in methods}
    differences = {m: paired(episodes, 'cc_target_class', m, ids) for m in methods if m != 'cc_target_class'}
    out = OUT / split
    out.mkdir(parents=True, exist_ok=True)
    export_csv(out / 'episodes.csv', episodes)
    export_csv(out / 'curves.csv', curves)
    write_json(out / 'raw_manifest.json', manifests)
    with gzip.GzipFile(filename=str(out / 'evidence.jsonl.gz'), mode='wb', mtime=0) as f:
        for r in evidence:
            f.write((json.dumps(r, ensure_ascii=False) + '\n').encode())
    improvement = {k: metrics['cc_target_class'][k] - metrics['canonical_coverage_iid'][k] for k in ['VR', 'NR', 'RR']}
    result = {'split': split, 'tasks': len(ids), 'seeds': seeds, 'queries_per_episode': 16,
              'metrics': metrics, 'counts': dict(counts), 'raw_outputs_rescored': len(evidence),
              'cc_target_class_vs': differences, 'change_from_original_canonical': improvement,
              'validity_guard_passed': improvement['VR'] >= -.02,
              'good_score_guides': {'VR': .9, 'NR': .8, 'RR': .8},
              'good_score_guides_met': {k: metrics['cc_target_class'][k] > v for k, v in {'VR': .9, 'NR': .8, 'RR': .8}.items()},
              'inference_note': 'Same prompts, checkpoints, sampler, seeds, scoring and 16 counted attempts as v1. Reused IID prefixes are counted in logical calls/tokens/time; no hidden rejected draws.',
              'uncertainty_note': 'Exploratory follow-up on previously reported test observations. One training seed. Task bootstrap averages three inference seeds; intervals are not multiplicity-adjusted.'}
    write_json(out / 'summary.json', result)
    write_json(out / 'verification.json', {'pass': True, 'raw_outputs_rescored': len(evidence),
                                         'same_prompt_replay_and_scoring_checked': True,
                                         'reference_labels_in_proposal': False, 'counts': dict(counts)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['validation', 'test'])
    args = parser.parse_args()
    result = aggregate(args.split)
    print(json.dumps({k: result[k] for k in ['split', 'metrics', 'counts', 'validity_guard_passed']}, indent=2))


if __name__ == '__main__':
    main()
