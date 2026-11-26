"""Freeze a free-generation audit; references are separate from model inputs."""
from __future__ import annotations

import hashlib
import itertools
import json
from datetime import datetime, timezone

from .coverage_lora import dataset
from .tasks import public_task, write_json
from .upstream import ROOT, evaluator, load

OUT = ROOT / 'results/research_audit_v7'
METHODS = ['base_iid', 'balanced_sft_iid', 'canonical_coverage_iid', 'string_coverage_iid']
SEEDS = [18617, 28657]
SOURCES = ['explorer/research_audit_data.py', 'explorer/research_audit.py',
           'scripts/report_research_audit.py', 'explorer/prefix_cache.py', 'explorer/experiment.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt(metadata, observations):
    module, _ = load()
    ev = evaluator(metadata)
    # Stable iteration order changes no allowed operators.
    ev.operators = sorted(metadata['operators'])
    text = ev.create_prompt([module.BooleanObservation(o['inputs'], o['output']) for o in observations], [])
    # Common upstream formatting defects, corrected identically for every arm.
    text = text.replace('- Use lowercase for variables: x, y',
                        '- Use lowercase for variables: ' + ', '.join(metadata['variables']))
    text = text.replace('            Expression: NOR(x, y)\n', '')
    return text


def prepare():
    protocol_path = OUT / 'protocol.json'
    if protocol_path.exists():
        p = json.loads(protocol_path.read_text())
        for name, expected in p['source_sha256'].items():
            assert digest(ROOT / name) == expected, name
        for name, expected in p['data_sha256'].items():
            assert digest(OUT / name) == expected, name
        print('Retained immutable prepared audit; source and data hashes match')
        return
    d = dataset()
    by_id = {t['id']: t for t in d['tasks']}
    public, references = [], {}
    for tid in d['splits']['test']:
        t = public_task(by_id[tid])
        public.append({**t, 'cohort': 'known_2var', 'metadata': d['metadata'],
                       'prompt': prompt(d['metadata'], t['observations'])})
        references[tid] = by_id[tid]['reference_keys']
    module, _ = load()
    meta = {**d['metadata'], 'variables': ['x', 'y', 'z']}
    expressions = module.BooleanDiscoveryGame.generate_all_expressions(
        meta['variables'], set(meta['operators']), meta['max_depth'], meta['mechanistic_opts'])
    bits = list(itertools.product([0, 1], repeat=3))
    universe = [{'key': str(e.mechanistic_key(**meta['mechanistic_opts'])),
                 'truth': [int(e.truth_table[b]) for b in bits]} for e in expressions]
    universe.sort(key=lambda e: e['key'])
    eligible = {}
    for n in [1, 2, 3]:
        pool = []
        for positions in itertools.combinations(range(8), n):
            for ys in itertools.product([0, 1], repeat=n):
                obs = [{'inputs': dict(zip(meta['variables'], bits[j])), 'output': y} for j, y in zip(positions, ys)]
                keys = [e['key'] for e in universe if all(e['truth'][j] == y for j, y in zip(positions, ys))]
                if len(keys) < 4:
                    continue
                signature = json.dumps(obs, sort_keys=True)
                tid = 'ood3_' + hashlib.sha256(signature.encode()).hexdigest()[:16]
                selection = hashlib.sha256(('research-audit-v7-20261127:' + signature).encode()).hexdigest()
                pool.append((selection, tid, obs, keys))
        eligible[str(n)] = len(pool)
        for _, tid, obs, keys in sorted(pool)[:4]:
            public.append({'id': tid, 'observations': obs, 'cohort': 'fresh_3var',
                           'metadata': meta, 'prompt': prompt(meta, obs)})
            references[tid] = keys
    assert len(public) == 38 and len(set(t['id'] for t in public)) == 38
    assert all(set(t) == {'id', 'observations', 'cohort', 'metadata', 'prompt'} for t in public)
    write_json(OUT / 'public_tasks.json', public)
    write_json(OUT / 'scoring_references.json', {'reference_keys': references, 'new_universe': universe,
               'new_metadata': meta, 'old_reference_universe_size': len(d['universe']),
               'selection': 'Four tasks per observation count 1/2/3, lowest fixed salted hashes among all eligible tasks. No model scores used.',
               'eligible_3var_counts': eligible})
    adapters = {m: digest(ROOT / 'artifacts/adapters' / m.removesuffix('_iid') / 'adapters.safetensors')
                for m in METHODS if m != 'base_iid'}
    protocol = {'frozen_utc': datetime.now(timezone.utc).isoformat(),
                'purpose': 'Measure learned free-generation performance and limits; no score threshold or method selection.',
                'methods': METHODS, 'inference_seeds': SEEDS, 'budget': 16,
                'primary_comparison': 'canonical_coverage_iid minus balanced_sft_iid, macro RR@16 on known_2var',
                'primary_status': 'Fresh sampling replication on already-used observation tasks; not a new untouched dataset.',
                'secondary_cohort': '12 fresh three-variable transfer tasks, selected before any model runs; no adaptation.',
                'task_ids': {c: [t['id'] for t in public if t['cohort'] == c] for c in ['known_2var', 'fresh_3var']},
                'expected_calls': len(public) * len(SEEDS) * len(METHODS) * 16,
                'generation': {'temperature': 1., 'top_p': 1., 'top_k': 0, 'min_p': 0., 'max_tokens': 128,
                               'decoder': 'unrestricted autoregressive stream_generate', 'prior_history': False,
                               'candidate_catalog': False, 'rejection_or_repair': False, 'uniqueness_target': None,
                               'reference_K_used_as_budget': False},
                'prompt_changes': ['Stable operator-list order', 'Remove NOR format example when NOR is not allowed',
                                   'Correct hard-coded variable-name formatting line for three variables'],
                'training': 'Original matched v1 checkpoints: same 80 SFT warmup + 120 branch updates, same training schedule; no new training or test-based checkpoint selection.',
                'training_seed_count': 1, 'adapter_sha256': adapters,
                'base_model': json.loads((ROOT / 'model.local_mlx.lock.json').read_text()),
                'scoring': 'Unchanged common fail-closed official parser/space/observation checks; full reference sets; all attempts retained.',
                'uncertainty': '10,000 paired task bootstrap resamples, seeds averaged within task. Secondary intervals exploratory; no output-level independence claim.',
                'source_sha256': {n: digest(ROOT / n) for n in SOURCES},
                'data_sha256': {n: digest(OUT / n) for n in ['public_tasks.json', 'scoring_references.json']},
                'old_test_scores_not_combined_with_new_scores': True,
                'model_runner_reads_scoring_references': False}
    write_json(protocol_path, protocol)
    print(json.dumps({k: protocol[k] for k in ['frozen_utc', 'task_ids', 'expected_calls']}, indent=2))


if __name__ == '__main__':
    prepare()
