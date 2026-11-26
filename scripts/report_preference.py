"""Rescore all new adapter outputs, verify prefix reuse, publish matched results."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from explorer.canonical_preference import OUT
from explorer.coverage_lora import dataset
from explorer.experiment import assess,read_rows
from explorer.preference_experiment import METHODS,RUN,config
from explorer.target_decode import intervene
from explorer.tasks import write_json
from explorer.upstream import evaluator
from scripts.report_canonical_decode import export_csv,paired


def aggregate(split):
    cfg,d=config(),dataset()
    signature=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    ev=evaluator(d['metadata'])
    tasks={t['id']:t for t in d['tasks']}
    ids,seeds=d['splits'][split],cfg['seeds'][split]
    original_prompt={}
    with gzip.open(ROOT/'results/final'/split/'evidence.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line)
            original_prompt[(r['contract']['task_id'],r['contract']['seed'])]=r['prompt']
    evidence,episodes,curves,hashes=[],[],[],{}
    counts=defaultdict(int)
    for method in METHODS:
        bace=method.endswith('_bace')
        uniform=method=='uniform_bace'
        arm=method.removesuffix('_iid').removesuffix('_bace')
        for tid in ids:
            refs=set(tasks[tid]['reference_keys'])
            for seed in seeds:
                p=RUN/f'{split}_{method}_{tid}_{seed}.jsonl'
                rows=read_rows(p)
                assert len(rows)==16,(p.name,len(rows))
                hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
                source=read_rows(RUN/f'{split}_{arm}_iid_{tid}_{seed}.jsonl') if bace and not uniform else []
                history,seen,valid_seen=[],set(),set()
                nv,seconds,tokens,interventions=0,0.,0,0
                for i,r in enumerate(rows):
                    assert r['contract']=={'fingerprint':signature,'split':split,'task_id':tid,'method':method,'seed':seed,'budget':16}
                    assert r['step']==i and r['error'] is None
                    assert set(r['task'])=={'id','observations'}
                    assert r['task']['observations']==tasks[tid]['observations']
                    assert r['prompt']==original_prompt[(tid,seed)]
                    active=bace and intervene(len(seen),i)
                    assert r['decoder']['active']==active
                    h=assess(ev,d['metadata'],r['task'],r['raw_response'],history)
                    for k in ['expression','key','in_space','valid','new','feedback']:
                        assert r['outcome'][k]==h[k],(p.name,i,k)
                    if active:
                        assert h['in_space'] and h['key'] not in seen
                        interventions+=1
                    if r['replay']:
                        assert bace and not active and interventions==0
                        for k in ['raw_response','prompt','usage','seconds','request_seed']:
                            assert r[k]==source[i][k]
                        counts['replayed_model_calls']+=1
                        counts['replayed_model_tokens']+=r['usage']['total_tokens']
                    elif uniform:
                        counts['uniform_draws']+=1
                    else:
                        counts['new_model_calls']+=1
                        counts['new_model_tokens']+=r['usage']['total_tokens']
                    if h['in_space']:seen.add(h['key'])
                    if h['valid']:
                        valid_seen.add(h['key']);nv+=1
                    seconds+=r['seconds'];tokens+=r['usage']['total_tokens']
                    n=i+1
                    item={'method':method,'task':tid,'seed':seed,'queries':n,'VR':nv/n,'NR':len(seen)/n,
                          'RR':len(valid_seen&refs)/len(refs),'reference_size':len(refs),'recovered':len(valid_seen&refs),
                          'outside_reference':len(valid_seen-refs),'seconds':seconds,'tokens':tokens,'intervention_calls':interventions}
                    curves.append(item)
                    if n==16:
                        if bace:assert len(seen)>=13
                        episodes.append(item)
                    evidence.append(r);history.append(h)
    originals=['base_iid','balanced_sft_iid','canonical_coverage_iid','string_coverage_iid']
    with (ROOT/'results/final'/split/'episodes.csv').open() as f:
        for r in csv.DictReader(f):
            if r['method'] not in originals:continue
            item={k:(r[k] if k in ['method','task'] else int(r[k]) if k in ['seed','queries','reference_size','recovered','outside_reference'] else float(r[k])) for k in curves[0] if k!='intervention_calls'}
            item['intervention_calls']=0
            episodes.append(item)
    methods=METHODS+originals
    metrics={m:{k:float(np.mean([r[k] for r in episodes if r['method']==m]))
                for k in ['VR','NR','RR','seconds','tokens','outside_reference','intervention_calls']} for m in methods}
    comparisons={target:{control:paired(episodes,target,control,ids) for control in methods if control!=target}
                 for target in ['canonical_preference_iid','canonical_preference_bace']}
    old=metrics['canonical_coverage_iid']
    eligible=[m for m in METHODS if m!='uniform_bace' and metrics[m]['NR']>.8 and metrics[m]['VR']>=old['VR']-.02 and metrics[m]['RR']>old['RR']]
    selected=max(eligible,key=lambda m:metrics[m]['RR']) if eligible else None
    if split=='test':
        # Test data never select which method is recommended.
        selected=json.loads((OUT/'selection.json').read_text())['selected_method']
    out=OUT/split;out.mkdir(parents=True,exist_ok=True)
    export_csv(out/'episodes.csv',episodes);export_csv(out/'curves.csv',curves)
    write_json(out/'raw_manifest.json',hashes)
    with gzip.GzipFile(filename=str(out/'evidence.jsonl.gz'),mode='wb',mtime=0) as f:
        for r in evidence:f.write((json.dumps(r,ensure_ascii=False)+'\n').encode())
    result={'split':split,'tasks':len(ids),'seeds':seeds,'attempts_per_episode':16,'metrics':metrics,
            'comparisons':comparisons,'counts':dict(counts),'raw_outputs_rescored':len(evidence),
            'eligible_on_this_split_under_numeric_rule':eligible,'selected_under_rule':selected,
            'reference_guides':{'VR':.90,'NR':.80,'RR':.80},
            'reference_guides_met_by_preference_bace':{k:metrics['canonical_preference_bace'][k]>v for k,v in {'VR':.9,'NR':.8,'RR':.8}.items()},
            'limits':'Exploratory follow-up on v1 test observations; fixed final updates; one training seed; task bootstrap intervals not multiplicity-adjusted. A selection rule is evaluated on validation, never used to hide other test arms.'}
    write_json(out/'summary.json',result)
    write_json(out/'verification.json',{'pass':True,'raw_outputs_rescored':len(evidence),'all_scoring_and_prefix_replay_checks_passed':True,'counts':dict(counts)})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('split',choices=['validation','test'])
    result=aggregate(parser.parse_args().split)
    print(json.dumps({k:result[k] for k in ['split','metrics','counts','selected_under_rule']},indent=2))
