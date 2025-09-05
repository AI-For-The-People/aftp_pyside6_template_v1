$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\indexer"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade beautifulsoup4 lxml readability-lxml trafilatura
# Windows needs -bin:
try { & "$venv\Scripts\python.exe" -m pip install --upgrade python-magic-bin } catch { & "$venv\Scripts\python.exe" -m pip install --upgrade python-magic }
& "$venv\Scripts\python.exe" -m pip install --upgrade tqdm typer xxhash
Write-Host "Activate:`n  .\venvs\indexer\Scripts\Activate.ps1"
