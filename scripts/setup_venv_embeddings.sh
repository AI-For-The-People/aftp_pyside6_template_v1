#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$here/venvs/embeddings"
py="${PYTHON:-python3}"

echo "[AFTP] Creating venv: $venv"
"$py" -m venv "$venv"
"$venv/bin/python" -m pip install --upgrade pip setuptools wheel

# --- packages ---
"$venv/bin/python" -m pip install sentence-transformers faiss-cpu

echo "[AFTP] Installed into venv 'embeddings'."
