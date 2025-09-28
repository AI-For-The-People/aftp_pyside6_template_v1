param([switch]$Debug)
$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null

if ($IsWindows) {
  $base = Join-Path $env:APPDATA "AFTP"
} elseif ($IsMacOS) {
  $base = Join-Path (Join-Path $env:HOME "Library/Application Support") "AFTP"
} else {
  $base = Join-Path (Join-Path $env:HOME ".local/share") "AFTP"
}

$venv = Join-Path (Join-Path $base "venvs") "core"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) { & (Join-Path $PSScriptRoot "setup_venv_core.ps1") }
if (-not (Test-Path $python)) { Write-Error "[AFTP] Core venv still missing."; exit 1 }

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  if ($Debug) {
    $logDir = Join-Path $root "logs"; New-Item -Force -ItemType Directory -Path $logDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $log = Join-Path $logDir "run_$stamp.log"
    & $python -m app *>&1 | Tee-Object -FilePath $log
  } else {
    & $python -m app
  }
} finally {
  Pop-Location
}
