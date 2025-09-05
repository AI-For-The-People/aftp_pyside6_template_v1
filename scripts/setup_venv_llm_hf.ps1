$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\llm_hf"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade transformers accelerate safetensors
try { & "$venv\Scripts\python.exe" -m pip install --upgrade bitsandbytes optimum } catch {}
Write-Host "Activate:`n  .\venvs\llm_hf\Scripts\Activate.ps1"
