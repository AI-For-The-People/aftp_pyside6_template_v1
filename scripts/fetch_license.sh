#!/usr/bin/env bash
set -euo pipefail
key="${1:-}"
if [ -z "$key" ]; then
  echo "Usage: scripts/fetch_license.sh <key>"
  echo "Known keys:"
  python3 - <<'PY'
from app.core.licenses import KNOWN_LICENSES
print("\\n".join(sorted(KNOWN_LICENSES.keys())))
PY
  exit 1
fi
python3 - <<PY
from app.core.licenses import fetch_and_cache_license
ok, msg = fetch_and_cache_license("$key")
print("OK:" if ok else "ERR:", msg)
PY
