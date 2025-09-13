#!/usr/bin/env bash
set -euo pipefail; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/embeddings"; python3 -m venv "$venv"
"$venv/bin/python" -m pip -qU pip setuptools wheel
# Attempt CUDA FAISS (Linux). If this fails for your arch, stay with faiss-cpu.
"$venv/bin/python" -m pip -qU sentence-transformers faiss-gpu || \
"$venv/bin/python" -m pip -qU sentence-transformers faiss-cpu
echo "[AFTP] embeddings (CUDA or CPU fallback) ready."
