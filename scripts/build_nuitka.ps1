$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj
python -m pip install -U nuitka orderedset zstandard
# Change "aftp_hub.py" to your real entry when ready
$ENTRY = "aftp_hub.py"
if (-Not (Test-Path $ENTRY)) { $ENTRY = "-m app" }
python -m nuitka $ENTRY `
  --onefile `
  --standalone `
  --enable-plugin=pyside6 `
  --nofollow-import-to=tkinter,pytest `
  --include-data-dir=app/assets=app/assets `
  --remove-output
Write-Host "[AFTP] Nuitka build finished."
