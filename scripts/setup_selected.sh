#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
to_install=("$@")
if [[ ${#to_install[@]} -eq 0 ]]; then
  echo "Usage: scripts/setup_selected.sh <core|ollama|llm_hf|image|embeddings|indexer|ocr_vision|stt|tts|ai_dev> [...]"
  exit 1
fi
for n in "${to_install[@]}"; do
  case "$n" in
    core)        "$here/setup_venv_core.sh" ;;
    ollama)      "$here/setup_venv_ollama.sh" ;;
    llm_hf)      "$here/setup_venv_llm_hf.sh" ;;
    image)       "$here/setup_venv_image_cpu.sh" ;;  # CPU default
    embeddings)  "$here/setup_venv_embeddings.sh" ;;
    indexer)     "$here/setup_venv_indexer.sh" ;;
    ocr_vision)  "$here/setup_venv_ocr_vision.sh" ;;
    stt)         "$here/setup_venv_stt.sh" ;;
    tts)         "$here/setup_venv_tts.sh" ;;
    ai_dev)      "$here/setup_venv_ai_dev.sh" ;;
    *) echo "Unknown runtime: $n" >&2; exit 1 ;;
  esac
done
