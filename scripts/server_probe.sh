#!/usr/bin/env bash
set -eu
uname -srm
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo 'No nvidia-smi on this host'
fi
if command -v python3 >/dev/null 2>&1; then
  python3 -c 'import sys; print(sys.version)'
fi
if command -v vllm >/dev/null 2>&1; then
  vllm --version
else
  echo 'vLLM is not on PATH'
fi
