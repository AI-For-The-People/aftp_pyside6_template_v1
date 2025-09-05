$proj = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $proj "venvs\embeddings"
$py = "python"
& $py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
& "$venv\Scripts\python.exe" -m pip install --upgrade sentence-transformers faiss-cpu numpy pandas
try { & "$venv\Scripts\python.exe" -m pip install --upgrade chromadb qdrant-client } catch {}
Write-Host "Activate:`n  .\venvs\embeddings\Scripts\Activate.ps1"
