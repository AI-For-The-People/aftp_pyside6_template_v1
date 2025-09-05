#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj_root="$(cd "$here/.." && pwd)"
venv_dir="$proj_root/venvs"; mkdir -p "$venv_dir"
name="core"; target="$venv_dir/$name"
python="${PYTHON:-python3}"
echo "[AFTP] Creating venv: $target"
$python -m venv "$target"
source "$target/bin/activate"
python -m pip install --upgrade pip wheel setuptools
python -m pip install --upgrade PySide6 requests
echo "[AFTP] Done. Activate with: source $target/bin/activate"
