#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
shopt -s nullglob
for s in scripts/setup_venv_*.sh; do
  echo "==> $s"
  bash "$s"
done
echo "==> Rescanning runtime registry"
bash scripts/update_registry.sh || true
echo "[AFTP] All venvs attempted and registry updated."
