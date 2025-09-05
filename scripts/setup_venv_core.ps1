$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\core"
$py = "python"
Write-Host "[AFTP] Creating venv at $venv"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade PySide6 requests
Write-Host "Activate:`n  .\venvs\core\Scripts\Activate.ps1"
