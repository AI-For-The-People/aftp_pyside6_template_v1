param([string]$Python = "python")
$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\indexer"

Write-Host "[AFTP] Creating venv: $venv"
& $Python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# --- packages ---
& "$venv\Scripts\python.exe" -m pip install trafilatura beautifulsoup4 lxml

Write-Host "[AFTP] Installed into venv 'indexer'."
