#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
: "${PYTHON:=python3}"
$PYTHON -m pip install -U nuitka orderedset zstandard || true
# Change "app/main_entry.py" to your real entry when ready
ENTRY="aftp_hub.py"
if [ ! -f "$ENTRY" ]; then
  # fallback: run the package
  ENTRY="-m app"
fi
$PYTHON -m nuitka $ENTRY \
  --onefile \
  --standalone \
  --enable-plugin=pyside6 \
  --nofollow-import-to=tkinter,pytest \
  --include-data-dir=app/assets=app/assets \
  --remove-output
echo "[AFTP] Nuitka build finished."
