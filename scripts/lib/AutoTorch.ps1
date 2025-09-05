function Test-HasCommand($cmd) { $null = Get-Command $cmd -ErrorAction SilentlyContinue; return $? }
function AFTP-Detect-CUDA {
  if (Test-HasCommand "nvidia-smi") { return "cuda:auto" }
  return "none"
}
function AFTP-TryInstall($idx) {
  & python -m pip install --upgrade --extra-index-url $idx torch torchvision torchaudio
  return $LASTEXITCODE -eq 0
}
function AFTP-Install-CPU { & python -m pip install --upgrade --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio; $env:AFTP_TORCH_FLAVOR="cpu" }
function AFTP-Install-CUDA {
  foreach ($idx in "https://download.pytorch.org/whl/cu124","https://download.pytorch.org/whl/cu121","https://download.pytorch.org/whl/cu118") {
    if (AFTP-TryInstall $idx) { $env:AFTP_TORCH_FLAVOR = Split-Path $idx -Leaf; return $true }
  }; return $false
}
function AFTP-AutoInstall-Torch {
  Write-Host "[AFTP] Auto Torch: probing system…"
  $cuda = AFTP-Detect-CUDA
  if ($cuda -like "cuda:*") {
    Write-Host "[AFTP] CUDA detected → trying CUDA wheels"
    if (-not (AFTP-Install-CUDA)) { Write-Host "[AFTP] CUDA wheels failed → CPU fallback"; AFTP-Install-CPU }
  } else {
    Write-Host "[AFTP] No CUDA detected → CPU wheels"
    AFTP-Install-CPU
  }
  if ($env:AFTP_TORCH_FLAVOR -like "cu*") { try { & python -m pip install --upgrade bitsandbytes } catch {} }
  & python - <<'PY'
import torch
print("torch", torch.__version__, "cuda?", torch.cuda.is_available())
if torch.cuda.is_available(): print("device:", torch.cuda.get_device_name(0))
PY
}
