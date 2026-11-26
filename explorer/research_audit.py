"""Model-only free-generation runner. Does not read solution sets or a catalog."""
from __future__ import annotations

import hashlib
import json
import random
import time

from .coverage_lora import LORA, MODEL, model_load
from .prefix_cache import build_prefix, fresh_prefix
from .tasks import write_json
from .upstream import ROOT

OUT = ROOT / 'results/research_audit_v7'
RUN = ROOT / 'runs/research_audit_v7'


def load_public_contract():
    protocol = json.loads((OUT / 'protocol.json').read_text())
    # Only public observations/rules/prompts are read. The separate scoring file
    # is not opened here, even for choosing how many outputs to produce.
    path = OUT / 'public_tasks.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol['data_sha256']['public_tasks.json']
    tasks = json.loads(path.read_text())
    assert all(set(t) == {'id', 'observations', 'cohort', 'metadata', 'prompt'} for t in tasks)
    assert protocol['budget'] == 16 and protocol['generation']['candidate_catalog'] is False
    for name, expected in protocol['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    return protocol, tasks


def run():
    import mlx.core as mx
    from mlx.utils import tree_flatten
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler
    from mlx_lm.tuner.utils import linear_to_lora_layers

    protocol, tasks = load_public_contract()
    assert hashlib.sha256((MODEL / 'model.safetensors').read_bytes()).hexdigest() == protocol['base_model']['weights_sha256']
    model, tok = model_load()
    model.freeze()
    linear_to_lora_layers(model, 8, LORA)
    model.eval()
    weights = {'base_iid': {n: mx.zeros_like(v) for n, v in tree_flatten(model.trainable_parameters())}}
    for method, expected in protocol['adapter_sha256'].items():
        p = ROOT / 'artifacts/adapters' / method.removesuffix('_iid') / 'adapters.safetensors'
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
        weights[method] = mx.load(str(p))
    RUN.mkdir(parents=True, exist_ok=True)
    raw = RUN / 'raw.jsonl'
    records = [json.loads(s) for s in raw.read_text().splitlines()] if raw.exists() else []
    fingerprint = hashlib.sha256((OUT / 'protocol.json').read_bytes()).hexdigest()
    done = {}
    for r in records:
        assert r['protocol_sha256'] == fingerprint
        assert r['error'] is None, 'Failed attempts retained; do not silently replace them'
        key = (r['task_id'], r['method'], r['seed'], r['step'])
        assert key not in done
        done[key] = r
    inflight = RUN / 'inflight.json'
    assert not inflight.exists(), 'Unfinished attempt marker retained; investigate before any resume'
    start = time.monotonic()
    cache_log = RUN / 'prefix_prefills.jsonl'
    with raw.open('a') as f:
        for index, task in enumerate(tasks):
            order = list(protocol['methods'])
            random.Random('audit-order:' + task['id']).shuffle(order)
            for method in order:
                if all((task['id'], method, s, j) in done for s in protocol['inference_seeds'] for j in range(16)):
                    continue
                model.load_weights(list(weights[method].items()), strict=False)
                mx.eval(model.parameters())
                ids = tok.apply_chat_template([{'role': 'user', 'content': task['prompt']}], add_generation_prompt=True, tokenize=True)
                tic = time.monotonic()
                prefix = build_prefix(model, ids)
                with cache_log.open('a') as cf:
                    cf.write(json.dumps({'task_id': task['id'], 'method': method, 'tokens': len(ids) - 1,
                                         'seconds': time.monotonic() - tic}) + '\n')
                for seed in protocol['inference_seeds']:
                    for step in range(protocol['budget']):
                        key = (task['id'], method, seed, step)
                        if key in done:
                            continue
                        value = int.from_bytes(hashlib.sha256(f'{seed}:{step}:{task["id"]}:research-audit-v7'.encode()).digest()[:8], 'big')
                        request_seed = random.Random(value).getrandbits(31)
                        row = {'protocol_sha256': fingerprint, 'cohort': task['cohort'], 'task_id': task['id'],
                               'method': method, 'seed': seed, 'step': step, 'budget': protocol['budget'],
                               'request_seed': request_seed, 'prompt': task['prompt']}
                        write_json(inflight, row)
                        mx.random.seed(request_seed)
                        tic = time.monotonic()
                        parts, last, error = [], None, None
                        try:
                            for last in stream_generate(model, tok, [ids[-1]], max_tokens=128,
                                                        sampler=make_sampler(temp=1., top_p=1., top_k=0, min_p=0.),
                                                        prompt_cache=fresh_prefix(prefix)):
                                parts.append(last.text)
                        except Exception as exc:
                            error = type(exc).__name__
                        row.update(raw_response=''.join(parts), error=error, seconds=time.monotonic() - tic,
                                   usage={'prompt_tokens': len(ids), 'completion_tokens': last.generation_tokens if last else 0,
                                          'total_tokens': len(ids) + (last.generation_tokens if last else 0)})
                        f.write(json.dumps(row, ensure_ascii=False) + '\n')
                        f.flush()
                        inflight.unlink()
                        done[key] = row
                        if error:
                            raise RuntimeError(f'Attempt failed and retained: {error}')
            print(f'Completed task {index+1}/{len(tasks)}; {len(done)}/{protocol["expected_calls"]} new free generations; elapsed {time.monotonic()-start:.1f}s', flush=True)
    assert len(done) == protocol['expected_calls']
    write_json(RUN / 'completion.json', {'calls': len(done), 'seconds_this_invocation': time.monotonic() - start,
                                        'all_outputs_retained': True, 'no_inference_reference_access': True})


if __name__ == '__main__':
    run()
