#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LOG="logs/run_$(date +%Y%m%d_%H%M%S).log"
echo "[AFTP] Launching Hub; logging to $LOG"
export PYTHONFAULTHANDLER=1
# keep terminal alive and tee output
( python3 -m app || true ) 2>&1 | tee -a "$LOG"
ec=$?
echo
echo "[AFTP] Exit code: $ec (see $LOG)"
echo -n "Press ENTER to close… "
read -r _
exit $ec
