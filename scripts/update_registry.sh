#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - <<'PY'
from pathlib import Path
from app.core.venv_tools import EXPECTED
from app.core.runtime_registry import rescan_and_update
reg = rescan_and_update(EXPECTED, Path(".").resolve())
print("Runtime registry updated.")
PY
