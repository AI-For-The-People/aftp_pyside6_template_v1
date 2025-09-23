param([switch]$Debug)

$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null

# Resolve repo root from this script’s location
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root "venvs\core"
$python = Join-Path $venv "Scripts\python.exe"

# Create core venv if missing
if (-not (Test-Path $python)) {
  Write-Host "[AFTP] Core venv missing; creating…" -ForegroundColor Yellow
  & (Join-Path $PSScriptRoot "setup_venv_core.ps1")
}

if (-not (Test-Path $python)) {
  Write-Error "[AFTP] Core venv still missing after setup. See scripts\setup_venv_core.ps1 output."
  exit 1
}

# Optional: help Qt pick the right integration
$env:QT_QPA_PLATFORM = "windows:darkmode=2"

Push-Location $root
try {
  if ($Debug) {
    $logDir = Join-Path $root "logs"
    New-Item -Force -ItemType Directory -Path $logDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $log = Join-Path $logDir "run_$stamp.log"
    Write-Host "[AFTP] Logging to $log"
    & $python -m app *>&1 | Tee-Object -FilePath $log
  } else {
    & $python -m app
  }
} finally {
  Pop-Location
}
