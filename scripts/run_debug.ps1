$ErrorActionPreference = "Continue"
$proj = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $proj

# Try to activate the core venv
$venvPath = Join-Path $proj "venvs\core\Scripts\Activate.ps1"
if (Test-Path $venvPath) { . $venvPath }

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONFAULTHANDLER = "1"
$env:QT_FATAL_WARNINGS = "0"

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $proj "logs\run_$ts.log"
New-Item -ItemType Directory -Force -Path (Join-Path $proj "logs") | Out-Null

"[*] Logging to $log" | Tee-Object -FilePath $log
# Use -X faulthandler for extra backtraces on hard crashes
python -X faulthandler -m app 2>&1 | Tee-Object -FilePath $log -Append
$code = $LASTEXITCODE

# Try to deactivate if available (PowerShell venv)
if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }

"[*] Exit code: $code (see $log)" | Tee-Object -FilePath $log -Append
exit $code
