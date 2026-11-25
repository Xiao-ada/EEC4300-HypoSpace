# Trained adapter checkpoints

These are actual LoRA-only weights from the matched final experiment, not the original model weights. All tensors are LoRA A/B matrices. The frozen base is the revision and SHA256 in model.local_mlx.lock.json. Use the corresponding adapter_config.json with MLX LM 0.32.2. Full scores and limitations are in the root README.

The adapters derive from Qwen/Qwen2.5-1.5B-Instruct through the pinned mlx-community four-bit conversion. They are provided under Apache 2.0; see LICENSE. Base weights are not redistributed. Project source has its separate root MIT license.

Run scripts/restore_adapters.py in a fresh checkout to place these weights into the private evaluation directory. That helper verifies manifest.json before copying.
