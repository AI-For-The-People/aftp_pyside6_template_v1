#!/usr/bin/env bash
set -euo pipefail
# AI For The People — venv setup helper
# This script creates a local venv under ./venvs/<name> and installs packages.
# Edit freely. For CUDA Torch, pick the right index URL for your GPU/driver.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj_root="$(cd "$here/.." && pwd)"
venv_dir="$proj_root/venvs"
mkdir -p "$venv_dir"

echo "[AFTP] Venvs here:"
ls -1 "$venv_dir" || true

cat <<'EONOTES'
To activate a venv:
  source venvs/<name>/bin/activate   # Linux/macOS
  .\venvs\<name>\Scripts\Activate.ps1  # Windows PowerShell

Recommended order to create:
  ./scripts/setup_venv_core.sh
  ./scripts/setup_venv_ollama.sh
  ./scripts/setup_venv_llm_hf.sh
  ./scripts/setup_venv_image.sh
  ./scripts/setup_venv_embeddings.sh
  ./scripts/setup_venv_indexer.sh
  ./scripts/setup_venv_ocr_vision.sh
  ./scripts/setup_venv_stt.sh
  ./scripts/setup_venv_tts.sh

Edit any script to customize GPU/CPU packages, CUDA wheels, etc.
EONOTES
