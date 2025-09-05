#!/usr/bin/env bash
set -euo pipefail
# Demo: compile a small compute module with Cython to speed up hotspots.
# This does NOT make a GUI exe; combine with Nuitka/PyInstaller for packaging.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj="$(cd "$here/.." && pwd)"
cd "$proj/app/ext"

: "${PYTHON:=python3}"
$PYTHON -m pip install --upgrade cython
$PYTHON setup.py build_ext --inplace
echo "[AFTP] Built Cython extension. Import with: from app.ext.fastops import dot_sum"
