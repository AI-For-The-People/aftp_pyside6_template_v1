$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\image"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
. "$PSScriptRoot\lib\AutoTorch.ps1"; AFTP-AutoInstall-Torch
& "$venv\Scripts\python.exe" -m pip install --upgrade diffusers transformers accelerate safetensors pillow
Write-Host "Activate:`n  .\venvs\image\Scripts\Activate.ps1"
