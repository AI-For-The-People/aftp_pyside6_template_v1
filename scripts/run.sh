#!/usr/bin/env bash
set -euo pipefail

case "$(uname -s)" in
  Darwin) base="$HOME/Library/Application Support/AFTP" ;;
  Linux)  base="$HOME/.local/share/AFTP" ;;
  *)      base="$HOME/.local/share/AFTP" ;;
esac
venv="$base/venvs/core"
py="$venv/bin/python3"

if [[ ! -x "$py" ]]; then
  "$(dirname "$0")/setup_venv_core.sh"
fi
if [[ ! -x "$py" ]]; then
  echo "[AFTP] Core venv still missing at $venv" >&2; exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
exec "$py" -m app
