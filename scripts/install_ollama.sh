#!/usr/bin/env bash
set -euo pipefail
echo "[AFTP] Installing Ollama (Linux/macOS)…"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
elif command -v wget >/dev/null 2>&1; then
  wget -qO- https://ollama.com/install.sh | sh
else
  echo "[AFTP] Need curl or wget to fetch the installer."; exit 1
fi
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl enable ollama || true
  sudo systemctl start ollama || true
fi
echo "[AFTP] Done. If server isn't running, try: 'ollama serve'"
