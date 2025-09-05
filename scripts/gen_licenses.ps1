$root = Split-Path -Parent $PSScriptRoot
$newLicDir = Join-Path $root "licenses"
New-Item -ItemType Directory -Force -Path $newLicDir | Out-Null
$venvs = Get-ChildItem -Directory (Join-Path $root "venvs")
foreach ($v in $venvs) {
  $name = $v.Name
  Write-Host "[AFTP] Generating third-party licenses for venv: $name"
  $py = Join-Path $v.FullName "Scripts\python.exe"
  $null = & $py -m pip install --upgrade pip-licenses 2>$null
  $md = Join-Path $newLicDir "third_party_${name}.md"
  try {
    & $py -m piplicenses --format=markdown --with-authors --with-urls --with-license-file > $md
  } catch {
    Write-Host "[warn] pip-licenses failed for $name"
  }
}
Write-Host "[AFTP] Done. See .\licenses\third_party_*.md"
