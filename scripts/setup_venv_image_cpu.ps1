$ErrorActionPreference = "Stop"
# CPU defaults; for CUDA/ROCm, make platform-specific scripts later
. (Join-Path $PSScriptRoot "_venv_common.ps1") -Name "image" -Pip @("diffusers","torch","accelerate","safetensors","Pillow")
