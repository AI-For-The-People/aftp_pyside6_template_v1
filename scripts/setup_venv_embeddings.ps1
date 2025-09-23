$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_venv_common.ps1") -Name "embeddings" -Pip @("sentence-transformers","faiss-cpu")
