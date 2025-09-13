#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/image"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
# OpenVINO route for inference on Intel CPU/iGPU
"$venv/bin/python" -m pip -qU openvino openvino-dev optimum[openvino] transformers safetensors
echo "[AFTP] image (Intel/OpenVINO) ready."
