#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj_root="$(cd "$here/.." && pwd)"
venv_dir="$proj_root/venvs"; mkdir -p "$venv_dir"
name="tts"; target="$venv_dir/$name"; python="${PYTHON:-python3}"
$python -m venv "$target"; source "$target/bin/activate"
python -m pip install --upgrade pip wheel setuptools
python -m pip install --upgrade pyttsx3
python -m pip install --upgrade TTS || true
