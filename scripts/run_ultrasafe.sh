#!/usr/bin/env bash
set -euo pipefail
# Force conservative Qt behavior
export QT_QPA_PLATFORM=xcb
export QT_STYLE_OVERRIDE=Fusion
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_ENABLE_HIGHDPI_SCALING=0
# Run in core venv if it exists
if [[ -f "venvs/core/bin/activate" ]]; then
  source venvs/core/bin/activate
fi
python3 -m app || {
  echo
  echo "[AFTP] Python exited with an error. See logs in ~/.local/share/AFTP/logs/ if enabled."
  exit 1
}
