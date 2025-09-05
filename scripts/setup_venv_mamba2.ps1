$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\mamba2"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
. "$PSScriptRoot\lib\AutoTorch.ps1"; AFTP-AutoInstall-Torch
& "$venv\Scripts\python.exe" -m pip install --upgrade mamba-ssm einops transformers safetensors
Write-Host "Activate:`n  .\venvs\mamba2\Scripts\Activate.ps1"
