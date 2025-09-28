param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string[]]$Pip = @(),
  [string]$PythonSpec = "-3.11"
)
$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null

# AFTP base dir
if ($IsWindows) {
  $base = Join-Path $env:APPDATA "AFTP"
} elseif ($IsMacOS) {
  $base = Join-Path (Join-Path $env:HOME "Library/Application Support") "AFTP"
} else {
  $base = Join-Path (Join-Path $env:HOME ".local/share") "AFTP"
}
$venvRoot = Join-Path $base "venvs"
$dataRoot = Join-Path $base "data"
New-Item -Force -ItemType Directory -Path $venvRoot | Out-Null
New-Item -Force -ItemType Directory -Path $dataRoot | Out-Null

$venv = Join-Path $venvRoot $Name
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Host "[AFTP] Creating venv '$Name' at $venv…" -ForegroundColor Yellow
  $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($pyLauncher) {
    & py $PythonSpec -m venv $venv
    if ($LASTEXITCODE -ne 0) { & py -3 -m venv $venv }
  } else {
    & python -m venv $venv
  }
}
if (-not (Test-Path $python)) {
  Write-Error "[AFTP] Failed to create venv at $venv"
  exit 1
}

& $python -m pip install --upgrade pip setuptools wheel
if ($Pip.Count -gt 0) { & $python -m pip install @Pip }

Write-Host "[AFTP] Installed into venv '$Name'." -ForegroundColor Green
