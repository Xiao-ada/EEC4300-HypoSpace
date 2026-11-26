"""Actual-model check that cached and uncached seeded decoding match."""
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mlx.core as mx
from mlx_lm import stream_generate
from mlx_lm.sample_utils import make_sampler
from mlx_lm.tuner.utils import linear_to_lora_layers
from explorer.canonical_decode import SupportTrie,TrieLogitsProcessor,grammar_support,completion_tokens
from explorer.coverage_lora import LORA,RUN as V1,dataset,model_load
from explorer.prefix_cache import build_prefix,fresh_prefix
from explorer.prompt_archive import recorded_prompt
from explorer.tasks import write_json

d=dataset();model,tok=model_load();model.freeze();linear_to_lora_layers(model,8,LORA)
model.load_weights(list(mx.load(str(V1/'adapters/canonical_coverage/adapters.safetensors')).items()),strict=False);model.eval()
support=completion_tokens(tok,grammar_support(d['metadata']))
checks=[]
for tid in d['splits']['validation'][:2]:
 prompt=recorded_prompt('validation',tid,101)
 ids=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,tokenize=True)
 start=time.monotonic();prefix=build_prefix(model,ids);build_seconds=time.monotonic()-start
 old_states=[tuple(mx.array(v) for v in c.state) for c in prefix]
 old_offsets=[c.offset for c in prefix]
 for masked in [False,True]:
  results=[];times=[]
  for cached in [False,True]:
   processor=TrieLogitsProcessor(SupportTrie(support),1 if cached else len(ids))
   kwargs={'prompt_cache':fresh_prefix(prefix)} if cached else {}
   start=time.monotonic();mx.random.seed(4305)
   text=[];tokens=[]
   for r in stream_generate(model,tok,[ids[-1]] if cached else ids,max_tokens=128,
                            sampler=make_sampler(temp=1.,top_p=1.,top_k=0,min_p=0.),
                            logits_processors=[processor] if masked else [],**kwargs):
    text.append(r.text);tokens.append(r.token)
   times.append(time.monotonic()-start);results.append((''.join(text),tokens))
  assert results[0]==results[1],(tid,masked)
  assert [c.offset for c in prefix]==old_offsets
  for c,old in zip(prefix,old_states):
   assert all(mx.all(a==b).item() for a,b in zip(c.state,old))
  checks.append({'task':tid,'grammar_masked':masked,'same_text_and_tokens':True,
                 'shared_cache_unchanged':True,'uncached_seconds':times[0],
                 'cached_seconds_excluding_build':times[1],'cache_build_seconds':build_seconds})
out={'pass':True,'checks':checks,'purpose':'Runtime-only implementation equivalence, not a method score','random_seed':4305}
write_json(ROOT/'results/canonical_preference_v5/prefix_cache_verification.json',out)
print(json.dumps(out,indent=2))
