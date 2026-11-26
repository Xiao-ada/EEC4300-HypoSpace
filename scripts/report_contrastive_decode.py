"""Retain the unsuccessful two-stream pilot, including all raw outcomes."""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer.coverage_lora import dataset
from explorer.contrastive_decode import OUT, RUN, protocol
from explorer.experiment import assess, read_rows
from explorer.tasks import write_json
from explorer.upstream import evaluator


def main():
    d, _, cfg = protocol()
    ev = evaluator(d['metadata'])
    tasks = {t['id']: t for t in d['tasks']}
    evidence, values = [], defaultdict(list)
    for tid in d['splits']['validation']:
        for scale in cfg['validation_scales']:
            method = f'cc_class_cfg{scale:g}'
            rows = read_rows(RUN / f'validation_{method}_{tid}_101.jsonl')
            assert len(rows) == 16
            history, seen, recovered = [], set(), set()
            valid = 0
            for r in rows:
                h = assess(ev, d['metadata'], r['task'], r['raw_response'], history)
                assert h == r['outcome'] and h['in_space'] and h['key'] not in seen
                assert not r['error'] and not r['prior_prompt'].split('Observations (input -> output):')[1].split('Prior expressions')[0].strip()
                seen.add(h['key'])
                if h['valid']:
                    recovered.add(h['key'])
                    valid += 1
                history.append(h)
                evidence.append(r)
            refs = set(tasks[tid]['reference_keys'])
            values[method].append({'VR': valid/16, 'NR': len(seen)/16, 'RR': len(recovered & refs)/len(refs)})
    metrics = {m: {k: sum(r[k] for r in rs)/len(rs) for k in ['VR', 'NR', 'RR']} for m, rs in values.items()}
    old = json.loads((ROOT/'results/final/validation/summary.json').read_text())['metrics']['canonical_coverage_iid']
    accepted = [m for m, row in metrics.items() if row['VR'] >= old['VR']-.02 and row['NR']>.8 and row['RR']>old['RR']]
    result = {'split': 'validation', 'outputs': len(evidence), 'metrics': metrics,
              'accepted_methods': accepted, 'selected': max(accepted, key=lambda m: metrics[m]['RR']) if accepted else None,
              'status': 'Not adopted: neither fixed guidance strength passes the validity guard' if not accepted else 'Validation-selected candidate',
              'limitation': 'Pilot prompt operator order follows the upstream unordered set and can differ from v1. This is exploratory, not a strict byte-identical-prompt comparison.',
              'ledger': json.loads((RUN/'generation_ledger.json').read_text())}
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(OUT/'evidence.jsonl.gz'), mode='wb', mtime=0) as f:
        for r in evidence:
            f.write((json.dumps(r, ensure_ascii=False)+'\n').encode())
    write_json(OUT/'summary.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
