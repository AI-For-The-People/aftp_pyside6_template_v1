#!/usr/bin/env bash
set -u
proj_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$proj_root" || exit 1

# Prefer the project's core venv if present
if [[ -f "venvs/core/bin/activate" ]]; then
  source "venvs/core/bin/activate"
  VENV_ACTIVE=1
else
  VENV_ACTIVE=0
fi

export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
export QT_FATAL_WARNINGS=0
# If you ever want more Qt logs: export QT_LOGGING_RULES="*.debug=true"

ts="$(date +%Y%m%d_%H%M%S)"
log="logs/run_${ts}.log"
mkdir -p logs

echo "[AFTP] Writing combined output to $log"
# stdbuf keeps output line-buffered so you see live logs
stdbuf -oL -eL python3 -X faulthandler -m app 2>&1 | tee -a "$log"
status=${PIPESTATUS[0]}

# Always leave your shell clean
if [[ $VENV_ACTIVE -eq 1 ]]; then
  deactivate || true
fi

echo "[AFTP] Exit code: $status (see $log)"
exit $status
