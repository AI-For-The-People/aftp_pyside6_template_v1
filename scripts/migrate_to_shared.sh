#!/usr/bin/env bash
set -euo pipefail
echo "[AFTP] Migrating per-app settings to shared settings.json (if any)…"
conf="${XDG_CONFIG_HOME:-$HOME/.config}/AFTP/settings.json"
mkdir -p "$(dirname "$conf")"
if [[ -f "./app/core/OLD_SETTINGS.json" ]] && [[ ! -f "$conf" ]]; then
  cp -v "./app/core/OLD_SETTINGS.json" "$conf"
  echo "[AFTP] Copied legacy settings to $conf"
fi
echo "[AFTP] Done."
