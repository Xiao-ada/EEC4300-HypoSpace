"""Post-hoc, train-only gradient probe of immutable v1 checkpoints.

No optimizer, sampling, validation answers, or test answers are used.
The probe diagnoses the training objective; it cannot establish test gains.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten, tree_map
from mlx_lm.tuner.trainer import grad_checkpoint
from mlx_lm.tuner.utils import linear_to_lora_layers

from explorer.coverage_lora import LORA, RUN, batch, coverage_value, model_load

OUT = ROOT / "results/diagnostics/v1_gradient_probe"
CHECKPOINTS = ["warmup", "balanced_sft", "canonical_coverage"]


def components(model, ids, mask, ratio):
    logits = model(ids[:, :-1])
    ce = nn.losses.cross_entropy(logits, ids[:, 1:], reduction="none").astype(mx.float32) * mask
    nll = ce.sum(axis=1)
    anchor = (nll / mask.sum(axis=1)).mean()
    reward = coverage_value(-nll, ratio, "canonical_coverage")
    return anchor, reward, -nll


def geometry(a, b):
    aa = dict(tree_flatten(a))
    bb = dict(tree_flatten(b))
    assert aa.keys() == bb.keys()
    a2 = sum(mx.sum(v.astype(mx.float32) ** 2) for v in aa.values())
    b2 = sum(mx.sum(v.astype(mx.float32) ** 2) for v in bb.values())
    dot = sum(mx.sum(v.astype(mx.float32) * bb[n].astype(mx.float32)) for n, v in aa.items())
    na = float(mx.sqrt(a2).item())
    nb = float(mx.sqrt(b2).item())
    return {"sft_grad_norm": na, "negative_coverage_grad_norm": nb,
            "norm_ratio_coverage_to_sft": nb / na if na else None,
            "loss_gradient_cosine": float(dot.item()) / (na * nb) if na and nb else None}


def describe(rows, field):
    import numpy as np
    values = [r[field] for r in rows if r[field] is not None]
    return {"mean": float(np.mean(values)), "median": float(np.median(values)),
            "min": float(np.min(values)), "max": float(np.max(values))}


def main():
    if OUT.exists():
        raise SystemExit("Probe already exists; retain the post-hoc record rather than overwrite it")
    data = json.loads((RUN / "training_data.json").read_text())
    by_task = {}
    for group in data["groups"]:
        by_task.setdefault(group["task_id"], []).append(group)
    rng = random.Random(4301)
    selected = [rng.choice(sorted(by_task[tid], key=lambda g: g["key"])) for tid in sorted(by_task)]
    assert len(selected) == 16
    paths = {name: RUN / "adapters" / name / "adapters.safetensors" for name in CHECKPOINTS}
    hashes = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in paths.items()}
    OUT.mkdir(parents=True)
    protocol = {"status": "post-hoc mechanism diagnosis, not an effectiveness test",
                "data": "one seeded class per training observation set; no validation/test labels",
                "selection_seed": 4301, "checkpoints": hashes, "lambda": 1,
                "selected": [{"task_id": g["task_id"], "key": g["key"]} for g in selected],
                "cosine_definition": "cos(gradient of SFT, gradient of negative coverage); positive reinforces",
                "batch_definition": "four consecutive selected class groups averaged, matching v1 accumulation size"}
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    model, _ = model_load()
    model.freeze()
    linear_to_lora_layers(model, 8, LORA)
    grad_checkpoint(model.layers[0])
    model.train()  # v1 dropout is zero; no state or optimizer updates.
    sft_fn = nn.value_and_grad(model, lambda m, *args: components(m, *args)[0])
    cov_fn = nn.value_and_grad(model, lambda m, *args: -components(m, *args)[1])
    all_rows = []
    batches = []
    tic = time.monotonic()
    for name, path in paths.items():
        model.load_weights(list(mx.load(str(path)).items()), strict=False)
        mx.eval(model.parameters())
        accum_sft = accum_cov = None
        for index, group in enumerate(selected):
            args = batch(group)
            sft_value, sft_grad = sft_fn(model, *args)
            cov_value, cov_grad = cov_fn(model, *args)
            mx.eval(sft_value, cov_value, sft_grad, cov_grad)
            _, _, logp = components(model, *args)
            probs = mx.exp(logp).tolist()
            row = {"checkpoint": name, "task_id": group["task_id"], "key": group["key"],
                   "sft_loss": float(sft_value.item()), "scaled_coverage_reward": -float(cov_value.item()),
                   "alias_complete_sequence_probabilities": probs, "class_alias_mass": sum(probs),
                   **geometry(sft_grad, cov_grad)}
            all_rows.append(row)
            with (OUT / "classes.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            if accum_sft is None:
                accum_sft, accum_cov = sft_grad, cov_grad
            else:
                accum_sft = tree_map(lambda a, b: a + b, accum_sft, sft_grad)
                accum_cov = tree_map(lambda a, b: a + b, accum_cov, cov_grad)
            mx.eval(accum_sft, accum_cov)
            if (index + 1) % 4 == 0:
                accum_sft = tree_map(lambda x: x / 4, accum_sft)
                accum_cov = tree_map(lambda x: x / 4, accum_cov)
                batches.append({"checkpoint": name, "batch_index": index // 4,
                                **geometry(accum_sft, accum_cov)})
                accum_sft = accum_cov = None
                print(f"Probe {name}: {index + 1}/16 train classes", flush=True)
    assert all(hashlib.sha256(paths[n].read_bytes()).hexdigest() == h for n, h in hashes.items())
    fields = ["sft_loss", "scaled_coverage_reward", "class_alias_mass", "norm_ratio_coverage_to_sft", "loss_gradient_cosine"]
    summary = {"status": protocol["status"], "training_classes": len(selected), "seconds": time.monotonic() - tic,
               "checkpoints_unchanged": True, "additional_generation_calls": 0,
               "class_summaries": {n: {field: describe([r for r in all_rows if r["checkpoint"] == n], field) for field in fields} for n in CHECKPOINTS},
               "batch_summaries": {n: {field: describe([r for r in batches if r["checkpoint"] == n], field) for field in ["norm_ratio_coverage_to_sft", "loss_gradient_cosine"]} for n in CHECKPOINTS},
               "batches": batches}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["batch_summaries"], indent=2), flush=True)


if __name__ == "__main__":
    main()
