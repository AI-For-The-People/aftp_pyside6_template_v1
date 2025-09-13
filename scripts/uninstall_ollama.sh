#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/uninstall_ollama.sh [--purge-models] [--models-dir /path/to/models]
#
# Defaults:
#   models-dir: ~/.ollama
#
# Notes:
#   --purge-models will rm -rf the models directory.

PURGE_MODELS=0
MODELS_DIR="${HOME}/.ollama"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge-models) PURGE_MODELS=1; shift;;
    --models-dir) MODELS_DIR="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "[AFTP] Uninstalling Ollama…"

# 1) Stop HTTP check (best-effort)
if command -v curl >/dev/null 2>&1; then
  echo "  - Endpoint check:"; curl -sS http://127.0.0.1:11434/api/version || true
fi

# 2) Stop & disable systemd services
if command -v systemctl >/dev/null 2>&1; then
  echo "  - systemd (user) stop/disable"
  systemctl --user stop ollama 2>/dev/null || true
  systemctl --user disable ollama 2>/dev/null || true
  rm -f "${HOME}/.config/systemd/user/ollama.service" 2>/dev/null || true

  echo "  - systemd (system) stop/disable (may prompt for sudo)"
  sudo systemctl stop ollama 2>/dev/null || true
  sudo systemctl disable ollama 2>/dev/null || true
  sudo rm -f /etc/systemd/system/ollama.service 2>/dev/null || true
  systemctl --user daemon-reload 2>/dev/null || true
  sudo systemctl daemon-reload 2>/dev/null || true
fi

# 3) Homebrew (noop on Pop!_OS, but safe)
if command -v brew >/dev/null 2>&1; then
  echo "  - brew services stop ollama"
  brew services stop ollama 2>/dev/null || true
fi

# 4) Docker containers/images
if command -v docker >/dev/null 2>&1; then
  echo "  - docker: stop any ollama containers"
  docker stop ollama 2>/dev/null || true
  ids=$(docker ps -a --format '{{.ID}} {{.Image}}' | awk '/ollama\/ollama/ {print $1}')
  if [ -n "${ids:-}" ]; then
    docker stop $ids 2>/dev/null || true
    docker rm $ids 2>/dev/null || true
  fi
  # (Optional) remove image? Commented by default:
  # docker rmi ollama/ollama 2>/dev/null || true
fi

# 5) Kill stray processes on 11434
echo "  - killing processes named ollama / bound to :11434"
if command -v pkill >/dev/null 2>&1; then pkill -f 'ollama serve' 2>/dev/null || true; fi
if command -v pkill >/dev/null 2>&1; then pkill -x ollama 2>/dev/null || true; fi
if command -v killall >/dev/null 2>&1; then killall ollama 2>/dev/null || true; fi
if command -v lsof >/dev/null 2>&1; then lsof -ti tcp:11434 | xargs -r kill -9 2>/dev/null || true; fi
if command -v fuser >/dev/null 2>&1; then fuser -k 11434/tcp 2>/dev/null || true; fi

# 6) Remove binary
echo "  - removing binaries if present"
sudo rm -f /usr/local/bin/ollama 2>/dev/null || true
sudo rm -f /usr/bin/ollama 2>/dev/null || true

# 7) Purge models directory (optional)
if [ "$PURGE_MODELS" = "1" ]; then
  echo "  - PURGE models directory: ${MODELS_DIR}"
  rm -rf --one-file-system "${MODELS_DIR}" 2>/dev/null || true
else
  echo "  - Keeping models at: ${MODELS_DIR} (use --purge-models to delete)"
fi

# 8) Reset AFTP Hub config reference to models dir (best-effort)
#    We look for a config.json alongside the running app (two common spots)
for p in \
  "./app/data/config.json" \
  "${HOME}/.local/share/AFTP/data/config.json" \
  "${XDG_DATA_HOME:-${HOME}/.local/share}/AFTP/data/config.json"
do
  if [ -f "$p" ]; then
    echo "  - Resetting ollama_models_dir in: $p"
    python3 - "$p" <<'PY'
import json, sys
p = sys.argv[1]
with open(p, "r", encoding="utf-8") as f:
    try: cfg = json.load(f)
    except Exception: cfg = {}
cfg.pop("ollama_models_dir", None)
with open(p, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
print("[AFTP] config updated:", p)
PY
  fi
done

echo "[AFTP] Ollama uninstalled (to the extent possible)."
