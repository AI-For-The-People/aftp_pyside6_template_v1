$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj
Get-ChildItem "$proj\scripts\setup_venv_*.ps1" | ForEach-Object {
  Write-Host "==> $($_.FullName)"
  & powershell -ExecutionPolicy Bypass -File $_.FullName
}
Write-Host "==> Rescanning runtime registry"
& powershell -ExecutionPolicy Bypass -File "$proj\scripts\update_registry.ps1"
Write-Host "[AFTP] All venvs attempted and registry updated."
