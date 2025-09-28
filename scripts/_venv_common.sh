#!/usr/bin/env bash
set -euo pipefail

name="${1:?venv name required}"
shift || true
pip_pkgs=("$@")

case "$(uname -s)" in
  Darwin) base="$HOME/Library/Application Support/AFTP" ;;
  Linux)  base="$HOME/.local/share/AFTP" ;;
  *)      base="$HOME/.local/share/AFTP" ;;
esac

venv_root="$base/venvs"
data_root="$base/data"
mkdir -p "$venv_root" "$data_root"

venv="$venv_root/$name"
pybin="$venv/bin/python3"

if [[ ! -x "$pybin" ]]; then
  echo "[AFTP] Creating venv '$name' at $venv..."
  python3 -m venv "$venv"
fi
if [[ ! -x "$pybin" ]]; then
  echo "[AFTP] Failed to create venv at $venv" >&2
  exit 1
fi

"$pybin" -m pip install --upgrade pip setuptools wheel
if [[ ${#pip_pkgs[@]} -gt 0 ]]; then
  "$pybin" -m pip install "${pip_pkgs[@]}"
fi

echo "[AFTP] Installed into venv '$name'."
