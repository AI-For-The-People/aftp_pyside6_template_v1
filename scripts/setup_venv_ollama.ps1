$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\ollama"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade ollama requests
Write-Host "Activate:`n  .\venvs\ollama\Scripts\Activate.ps1"
