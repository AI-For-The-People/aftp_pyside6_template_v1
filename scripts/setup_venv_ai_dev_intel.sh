#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/ai_dev"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
# Intel training support via IPEX is niche; we default to OpenVINO inference libs + CPU training.
"$venv/bin/python" -m pip -qU openvino openvino-dev optimum[openvino] transformers datasets accelerate peft trl
echo "[AFTP] ai_dev (Intel/OpenVINO/CPU-train) ready."
