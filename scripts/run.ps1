$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\core"

if (-Not (Test-Path "$venv\Scripts\python.exe")) {
    Write-Host "[AFTP] Core venv missing — creating..."
    & powershell -ExecutionPolicy Bypass -File "$proj\scripts\setup_venv_core.ps1"
}

# Run directly without dropping user into venv
& "$venv\Scripts\python.exe" -m app
