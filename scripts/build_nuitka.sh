#!/usr/bin/env bash
set -euo pipefail
# Build a standalone executable using Nuitka.
# Prereqs: python -m pip install nuitka ordered-set zstandard
#          (On Linux: sudo apt-get install patchelf)
# Recommended to run inside the 'core' venv.

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj="$(cd "$here/.." && pwd)"
cd "$proj"

: "${PYTHON:=python3}"
$PYTHON -m pip install --upgrade nuitka ordered-set zstandard

# Nuitka plugin for PySide6 auto-includes Qt plugins.
CMD=(
  "$PYTHON" -m nuitka
  --onefile
  --enable-plugin=pyside6
  --include-data-dir=app=app
  --company-name="AI For The People"
  --product-name="AFTP Template"
  --output-filename="aftp_template"
  app/main.py
)
echo "[AFTP] Running: ${CMD[*]}"
"${CMD[@]}"
echo "[AFTP] Built ./aftp_template"
