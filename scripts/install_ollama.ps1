Write-Host "[AFTP] Installing Ollama (Windows)…"
$wingetOK = $false
try {
  winget --version | Out-Null
  $wingetOK = $true
} catch {}
if ($wingetOK) {
  try {
    winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    Write-Host "[AFTP] winget install attempted. If it didn't start, run Ollama from Start Menu."
    exit
  } catch {
    Write-Host "[AFTP] winget install failed, opening download page…"
  }
}
Start-Process "https://ollama.com/download"
