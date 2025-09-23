param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string[]]$Pip = @(),
  [string]$PythonSpec = "-3.11"  # prefer 3.11 for wheel availability
)

$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ("venvs\" + $Name)
$python = Join-Path $venv "Scripts\python.exe"

# Create venv if needed (use py launcher if present)
if (-not (Test-Path $python)) {
  New-Item -Force -ItemType Directory -Path (Split-Path $venv) | Out-Null
  $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($pyLauncher) {
    Write-Host "[AFTP] Creating venv '$Name' with 'py $PythonSpec'…" -ForegroundColor Yellow
    & py $PythonSpec -m venv $venv
    if ($LASTEXITCODE -ne 0) {
      Write-Host "[AFTP] Fallback to 'py -3'…" -ForegroundColor Yellow
      & py -3 -m venv $venv
    }
  } else {
    Write-Host "[AFTP] Creating venv '$Name' with system python…" -ForegroundColor Yellow
    & python -m venv $venv
  }
}

if (-not (Test-Path $python)) {
  Write-Error "[AFTP] Failed to create venv at $venv"
  exit 1
}

# Upgrade basics
& $python -m pip install --upgrade pip setuptools wheel

if ($Pip.Count -gt 0) {
  Write-Host "[AFTP] Installing packages for '$Name'…" -ForegroundColor Yellow
  & $python -m pip install @Pip
}

Write-Host "[AFTP] Installed into venv '$Name'." -ForegroundColor Green
