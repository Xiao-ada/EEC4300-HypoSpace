"""Verify response-only projection on the actual quantized model and LoRA grads."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten
from mlx_lm.tuner.utils import linear_to_lora_layers
from mlx_lm.tuner.trainer import grad_checkpoint
from explorer.canonical_preference import RUN,OUT,loss_function
from explorer.coverage_lora import LORA,RUN as V1,model_load,batch
from explorer.tasks import write_json

data=json.loads((RUN/'training_data.json').read_text())
model,_=model_load();model.freeze();linear_to_lora_layers(model,8,LORA)
model.load_weights(list(mx.load(str(V1/'adapters/canonical_coverage/adapters.safetensors')).items()),strict=False)
grad_checkpoint(model.layers[0]);model.train()
g=data['groups'][0]
ids,mask,ratio=batch(g)
args=(ids,mask,ratio,mx.array(g['reference_margin']),g['aliases'][0]['prompt_length']-1)
times=[];results=[]
for response_only in [False,True]:
 start=time.monotonic()
 loss,grad=nn.value_and_grad(model,loss_function(True,response_only))(model,*args)
 mx.eval(loss,grad)
 times.append(time.monotonic()-start)
 results.append((float(loss.item()),dict(tree_flatten(grad))))
a,b=results
norm=mx.sqrt(sum(mx.sum(v*v) for v in a[1].values())).item()
diff=mx.sqrt(sum(mx.sum((a[1][n]-b[1][n])**2) for n in a[1])).item()
maximum=max(mx.max(mx.abs(a[1][n]-b[1][n])).item() for n in a[1])
record={'training_groups':1,'model':'actual frozen quantized Qwen2.5-1.5B with v1 canonical adapter',
        'optimizer_updates':0,'full_loss':a[0],'response_only_loss':b[0],
        'loss_absolute_difference':abs(a[0]-b[0]),'gradient_relative_l2_difference':diff/max(norm,1e-12),
        'gradient_max_absolute_difference':maximum,'full_seconds':times[0],'response_only_seconds':times[1],
        'note':'One-batch implementation check, not a new method result or a general speed benchmark. Float precision can change with quantized matrix shapes.'}
assert record['loss_absolute_difference']<1e-3 and record['gradient_relative_l2_difference']<.02
record['pass']=True
write_json(OUT/'response_projection_verification.json',record)
print(json.dumps(record,indent=2))
