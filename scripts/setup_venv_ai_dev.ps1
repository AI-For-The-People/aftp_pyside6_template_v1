param([string]$Python = "python")
$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\ai_dev"

Write-Host "[AFTP] Creating venv: $venv"
& $Python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# CPU wheels by default; switch to CUDA/ROCm per your GPU later
& "$venv\Scripts\python.exe" -m pip install torch transformers datasets accelerate peft trl

Write-Host "[AFTP] Installed into venv 'ai_dev'."
