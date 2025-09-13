#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/image"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
# ROCm wheels (Linux only). Pick your ROCm torch index as per PyTorch docs; this is a common default:
"$venv/bin/python" -m pip -qU torch --index-url https://download.pytorch.org/whl/rocm6.1
"$venv/bin/python" -m pip -qU diffusers transformers accelerate safetensors
echo "[AFTP] image (ROCm) ready."
