$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\tts"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade pyttsx3
try { & "$venv\Scripts\python.exe" -m pip install --upgrade TTS } catch {}
Write-Host "Activate:`n  .\venvs\tts\Scripts\Activate.ps1"
