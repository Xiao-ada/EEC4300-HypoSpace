# GPU server execution

This guide describes the institutional PlatforMax workflow without publishing institutional addresses or credentials. The platform login and the SSH login for a created interactive task are different. Actual GPU type, VRAM, quota, queue state, network access, and cached models must be inspected on the live platform; manual screenshots are examples.

## Platform setup

1. Connect the operating computer to the institution network or its approved VPN. Confirm the platform login page opens.
2. Sign in with the assigned platform account. Inspect the user quota, available GPU types, and per-node remaining resources.
3. Create one interactive task using one GPU and a suitable existing PyTorch/CUDA image. Choose Terminal or Jupyter according to available image support. Task creation generates the task-specific connection address, port, and login details; do not assume the platform password is the container password.
4. Mount a private workspace. Keep the entire project, caches, logs, checkpoints, and model downloads under `/opt/data/private`. Other container paths can disappear when the task is released or restarted.
5. Run `bash scripts/server_probe.sh` inside the task. Inspect existing model caches before downloading weights or installing a new inference stack.

The supplied notice says one-GPU tasks are easier to schedule, idle tasks may be removed after 24 hours, and expired tasks are automatically deleted. Save reusable software environments as a private image when needed; private-volume data is stored separately from that image. Release resources after exporting results. These are operational constraints from the user's supplied notice, not requirements for the ML method.

## Project transfer

Use the local upload archive created by `scripts/package_source.py`, upload it to private data through the platform, and extract it there. It contains only the Git-publishable project source, not the virtual environment, source manuals, credentials, private logs, caches, or model weights.

If outbound GitHub access is unavailable, transfer the separate locally prepared upstream cache archive as well. It contains checksum-verified upstream files for private runtime use and must not be added to the public repository. Dependency wheels and model weights are separate large artifacts; do not assume the source archive includes them.

## Model serving

The experiment client can call an existing chat-completion endpoint on the GPU host. With a working vLLM environment and a model already chosen for the available GPU, the general local serving form is:

```bash
vllm serve /path/to/approved/chat-model --host 127.0.0.1 --port 8000
```

Use the server's returned model ID for `LLM_MODEL`; set `LLM_BASE_URL=http://127.0.0.1:8000/v1`. If running the client on the laptop, use a task-specific SSH tunnel so the laptop sees a localhost endpoint. A private local server may not require an API key; external endpoints must use HTTPS and the configured key. Model/chat-template compatibility and generation options must be checked before the main run.

The official reference for this endpoint is [vLLM serving documentation](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/). An inference stack, compatible CUDA environment, and weights are not installed by the project requirements. The controller alone does not require GPU training.

## Run order

Use the commands in the root README: prepare, preflight, collect two training tasks, inspect throughput, resume collection, train, evaluate, summarize. Keep the same run directory throughout. Set the model download cache to a directory on the persistent private volume if downloads are needed. Report queued time, setup time, and actual generation time separately.

## Apple Silicon fallback

The local screening configuration uses a pinned public 4-bit conversion of Qwen2.5-1.5B-Instruct with MLX. This is a real model experiment with a different model scale from the paper. Keep inference dependencies and weights outside the source repository:

```bash
python3.12 -m venv ../runtime/mlx-env
../runtime/mlx-env/bin/python -m pip install -r requirements-mlx-lock.txt
HF_HOME=../runtime/hf-cache ../runtime/mlx-env/bin/python scripts/local_mlx.py
```

The helper verifies the pinned weights' SHA256 and binds the server only to loopback. In the local ignored `.env`, set `LLM_BASE_URL=http://127.0.0.1:8080/v1`, `LLM_MODEL=default_model`, and leave `LLM_API_KEY` empty. The experiment configuration records the actual model name and revision despite that server alias. Do not enable remote tokenizer code.

In another terminal run the README's collection, training and evaluation commands with both `--config config.local_mlx.json` and `--run-dir runs/local_qwen15b`. Use these same arguments for all phases, including summarization. Keep `model.local_mlx.lock.json` and the runtime lock with exported results; weights and environments are not part of the public source archive.
