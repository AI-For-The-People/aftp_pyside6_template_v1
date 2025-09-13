#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/image"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
"$venv/bin/python" -m pip -qU torch diffusers transformers accelerate safetensors
echo "[AFTP] image (CPU) ready."
