\
# Build with Nuitka on Windows (PowerShell)
# Prereqs: pip install nuitka ordered-set zstandard; install Visual Studio Build Tools; install patchelf (not on Windows).
$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj
$py = "python"
& $py -m pip install --upgrade nuitka ordered-set zstandard
& $py -m nuitka --onefile --enable-plugin=pyside6 --include-data-dir=app=app --company-name "AI For The People" --product-name "AFTP Template" --output-filename "aftp_template.exe" app/main.py
Write-Host "[AFTP] Built aftp_template.exe"
