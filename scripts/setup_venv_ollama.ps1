param([string]$Python = "python")
$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\ollama"

Write-Host "[AFTP] Creating venv: $venv"
& $Python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# --- packages ---
& "$venv\Scripts\python.exe" -m pip install ollama requests

Write-Host "[AFTP] Installed into venv 'ollama'."
