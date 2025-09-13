#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/image"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
# CUDA wheels (adjust cu version if your system differs)
"$venv/bin/python" -m pip -qU torch --index-url https://download.pytorch.org/whl/cu121
"$venv/bin/python" -m pip -qU diffusers transformers accelerate safetensors
echo "[AFTP] image (CUDA) ready."
