#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

venv="$here/venvs/core"
if [ ! -x "$venv/bin/python3" ]; then
  echo "[AFTP] Core venv missing — creating..."
  bash scripts/setup_venv_core.sh
fi

# Run without leaving you “inside” the venv
"$venv/bin/python3" -m app
