$proj = Split-Path -Parent $PSScriptRoot
Push-Location $proj
python - <<'PY'
from pathlib import Path
from app.core.venv_tools import EXPECTED
from app.core.runtime_registry import rescan_and_update
reg = rescan_and_update(EXPECTED, Path(".").resolve())
print("Runtime registry updated.")
PY
Pop-Location
