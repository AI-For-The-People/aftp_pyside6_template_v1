#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/ai_dev"
py="${PYTHON:-python3}"

echo "[AFTP] Creating venv: $venv"
"$py" -m venv "$venv"
"$venv/bin/python" -m pip install --upgrade pip setuptools wheel

# CPU wheels by default; switch to CUDA/ROCm per your GPU later
"$venv/bin/python" -m pip install torch transformers datasets accelerate peft trl

echo "[AFTP] Installed into venv 'ai_dev'."
