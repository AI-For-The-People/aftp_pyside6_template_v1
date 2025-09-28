#!/usr/bin/env bash
set -euo pipefail
name="${1:?usage: scripts/doctor_venv.sh <venv_name>}"
case "$(uname -s)" in
  Darwin) base="$HOME/Library/Application Support/AFTP" ;;
  Linux)  base="$HOME/.local/share/AFTP" ;;
  *)      base="$HOME/.local/share/AFTP" ;;
esac
venv="$base/venvs/$name"
py="$venv/bin/python3"
if [[ ! -x "$py" ]]; then
  echo "[AFTP] $name: python not found at $py"
  exit 1
fi
echo "== $name python =="
"$py" -V
echo "== site =="
"$py" -c 'import sys, pprint; pprint.pp(sys.path)'
echo "== pip freeze (top 40) =="
"$py" -m pip freeze | head -n 40
echo "== import smoke =="
mods=("PySide6" "requests" "ollama" "transformers" "accelerate" "safetensors" "diffusers" "torch" "sentence_transformers" "faiss" "trafilatura" "bs4" "lxml" "pytesseract" "cv2" "PIL" "whisper" "pyttsx3")
for m in "${mods[@]}"; do
  "$py" -c "import importlib, sys; sys.exit(0 if importlib.util.find_spec('$m') else 1)" \
    && echo "OK  $m" || echo "MISS $m"
done
