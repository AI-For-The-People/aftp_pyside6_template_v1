$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\stt"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade openai-whisper ffmpeg-python
Write-Host "Requires system ffmpeg (winget install Gyan.FFmpeg)."
Write-Host "Activate:`n  .\venvs\stt\Scripts\Activate.ps1"
