#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
python3 - <<'PY'
from app.core.licenses import fetch_all_known_licenses
st = fetch_all_known_licenses()
for k,v in st.items():
    print(f"{k}: {v}")
print("Cached under ./licenses/")
PY
