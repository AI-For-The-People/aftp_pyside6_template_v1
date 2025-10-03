#!/usr/bin/env bash
set -euo pipefail

# --- Resolve OS-specific paths (mirror app/core/paths.py) ---
os="$(uname -s)"
if [[ "$os" == "Darwin" ]]; then
  CFG="$HOME/Library/Preferences/AFTP"
  DAT="$HOME/Library/Application Support/AFTP"
else
  if [[ "$os" == "Linux" ]]; then
    CFG="${XDG_CONFIG_HOME:-$HOME/.config}/AFTP"
    DAT="$HOME/.local/share/AFTP"
  else
    # WSL or unknown UNIX -> use Linux-style defaults
    CFG="${XDG_CONFIG_HOME:-$HOME/.config}/AFTP"
    DAT="$HOME/.local/share/AFTP"
  fi
fi

SETTINGS="$CFG/settings.json"
VENVSDIR="$DAT/venvs"
LOGDIR="$DAT/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/selftest_$(date +%Y%m%d_%H%M%S).log"

say() { echo -e "$@" | tee -a "$LOG"; }

say "=== AFTP Self-Test ==="
say "Config dir : $CFG"
say "Data dir   : $DAT"
say "Settings   : $SETTINGS"
say "Venvs dir  : $VENVSDIR"
say "Log        : $LOG"
say

# 1) Check settings.json
if [[ ! -f "$SETTINGS" ]]; then
  say "[WARN] settings.json not found. The app will create it on first run."
else
  say "[OK] Found settings.json"
  # Pretty-print a few keys
  jq -r '{
    theme: .theme,
    ollama: { host: .ollama.host, port: .ollama.port, models_dir: .ollama.models_dir, binary: .ollama.binary },
    paths: .paths,
    gpu: .gpu.preference
  }' "$SETTINGS" 2>/dev/null | tee -a "$LOG" || say "[INFO] (jq not installed; skipping pretty-print)"
fi
say

# 2) Ensure core directories exist
for d in "$VENVSDIR" "$DAT/data/hf_cache" "$DAT/conversations" "$DAT/plugins" "$DAT/presets" "$DAT/licenses"; do
  if [[ ! -d "$d" ]]; then
    mkdir -p "$d"
    say "[OK] Created $d"
  else
    say "[OK] Exists $d"
  fi
done
say

# 3) Venv sanity checks (use app logic via python if available)
PYBIN="$(command -v python3 || true)"
if [[ -z "$PYBIN" ]]; then
  say "[WARN] python3 not found in PATH; skipping import checks."
else
  say "[INFO] Using python: $PYBIN"
  "$PYBIN" - <<'PY' 2>&1 | tee -a "$LOG"
from pathlib import Path
import json, os, sys, importlib

print("== Python:", sys.version)
# Attempt to load AFTP helpers
try:
    sys.path.insert(0, str(Path('.').resolve()))
    from app.core.venv_tools import EXPECTED, _pybin, is_created, details
    print("== EXPECTED runtimes:", ", ".join(EXPECTED.keys()))
    for name in EXPECTED.keys():
        ok = is_created(name)
        print(f"[VENVS] {name}: {'present' if ok else 'missing'}")
        if ok:
            info = details(name)
            # summarize module status
            misses = [m for m,v in info.items() if isinstance(v, dict) and not v.get('ok', True)]
            if misses:
                print(f"   - missing imports: {', '.join(misses)}")
            else:
                print("   - imports OK")
except Exception as e:
    print("[WARN] could not import app.core.venv_tools:", e)
PY
fi
echo | tee -a "$LOG"

# 4) Ollama quick check (env + http ping if possible)
OLLAMA_HOST_ENV="${OLLAMA_HOST:-}"
if [[ -n "$OLLAMA_HOST_ENV" ]]; then
  say "[INFO] OLLAMA_HOST env is set: $OLLAMA_HOST_ENV"
fi
if command -v curl >/dev/null 2>&1; then
  HOST="${OLLAMA_HOST_ENV#http://}"; HOST="${HOST#https://}"
  [[ -z "$HOST" ]] && HOST="127.0.0.1:11434"
  say "[INFO] Probing Ollama at http://$HOST/api/tags …"
  if curl -fsS --max-time 1 "http://$HOST/api/tags" >/dev/null; then
    say "[OK] Ollama responded."
  else
    say "[INFO] Ollama not responding (this is fine if you haven’t started it)."
  fi
else
  say "[INFO] curl not found; skipping Ollama HTTP probe."
fi

say
say "=== Self-test complete ==="
say "Log saved to: $LOG"
