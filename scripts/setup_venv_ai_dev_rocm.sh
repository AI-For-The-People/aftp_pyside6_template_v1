#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/ai_dev"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
"$venv/bin/python" -m pip -qU torch --index-url https://download.pytorch.org/whl/rocm6.1
"$venv/bin/python" -m pip -qU transformers datasets accelerate peft trl
echo "[AFTP] ai_dev (ROCm) ready."
