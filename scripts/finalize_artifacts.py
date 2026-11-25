"""Export reviewed small checkpoints and immutable run metadata for publication."""
from pathlib import Path
import gzip,hashlib,json,shutil
import mlx.core as mx
ROOT=Path(__file__).resolve().parents[1];run=ROOT/'runs/final_v1';out=ROOT/'results/final';dest=ROOT/'artifacts/adapters'
for name in ['balanced_sft','canonical_coverage','string_coverage']:
 src=run/'adapters'/name
 weights=mx.load(str(src/'adapters.safetensors'))
 assert weights and all(n.endswith(('lora_a','lora_b')) for n in weights)
 dst=dest/name;dst.mkdir(parents=True,exist_ok=True)
 for f in ['adapters.safetensors','adapter_config.json']:shutil.copyfile(src/f,dst/f)
manifest={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file() and p.name!='manifest.json'}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name in ['model_manifest.json','timing_probe.json','split_overlap_audit.json']:shutil.copyfile(run/name,out/name)
with gzip.GzipFile(filename=str(out/'training_targets.json.gz'),mode='wb',mtime=0) as f:f.write((run/'training_data.json').read_bytes())
(dest/'README.md').write_text('''# Trained adapter checkpoints\n\nThese are actual LoRA-only weights from the matched final experiment, not the original model weights. All tensors are LoRA A/B matrices. The frozen base is the revision and SHA256 in model.local_mlx.lock.json. Use the corresponding adapter_config.json with MLX LM 0.32.2. Full scores and limitations are in the root README.\n\nThe adapters derive from Qwen/Qwen2.5-1.5B-Instruct through the pinned mlx-community four-bit conversion. They are provided under Apache 2.0; see LICENSE. Base weights are not redistributed. Project source has its separate root MIT license.\n\nRun scripts/restore_adapters.py in a fresh checkout to place these weights into the private evaluation directory. That helper verifies manifest.json before copying.\n''')
# Include the newly written attribution in the final manifest.
manifest={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file() and p.name!='manifest.json'}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Exported three verified adapters, manifests and compressed training targets')
