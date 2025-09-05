$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\ocr_vision"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade pillow opencv-python-headless pytesseract
Write-Host "Requires system Tesseract installed (winget install UB-Mannheim.TesseractOCR)."
Write-Host "Activate:`n  .\venvs\ocr_vision\Scripts\Activate.ps1"
