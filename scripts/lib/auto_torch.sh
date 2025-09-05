#!/usr/bin/env bash
set -euo pipefail
_aftp_has_cmd() { command -v "$1" >/dev/null 2>&1; }
_aftp_detect_cuda() {
  if _aftp_has_cmd nvidia-smi; then
    if _aftp_has_cmd nvcc; then
      local cver; cver=$(nvcc --version 2>/dev/null | sed -n 's/.*release \([0-9][0-9]*\.[0-9]\).*/\1/p')
      echo "cuda:$cver"; return
    fi
    echo "cuda:auto"; return
  fi
  echo "none"
}
_aftp_detect_rocm() { { [[ -d "/opt/rocm" ]] || _aftp_has_cmd rocminfo; } && echo "rocm" || echo "none"; }
_aftp_try_install() { python -m pip install --upgrade --extra-index-url "$1" torch torchvision torchaudio && return 0 || return 1; }
_aftp_install_cpu() { python -m pip install --upgrade --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio; export AFTP_TORCH_FLAVOR="cpu"; }
_aftp_install_cuda() {
  for idx in https://download.pytorch.org/whl/cu124 https://download.pytorch.org/whl/cu121 https://download.pytorch.org/whl/cu118; do
    _aftp_try_install "$idx" && { export AFTP_TORCH_FLAVOR="$(basename "$idx")"; return 0; }
  done; return 1
}
_aftp_install_rocm() {
  for idx in https://download.pytorch.org/whl/rocm6.0 https://download.pytorch.org/whl/rocm5.6; do
    _aftp_try_install "$idx" && { export AFTP_TORCH_FLAVOR="$(basename "$idx")"; return 0; }
  done; return 1
}
aftp_auto_install_torch() {
  echo "[AFTP] Auto Torch: probing system…"
  local cuda="$(_aftp_detect_cuda)" rocm="$(_aftp_detect_rocm)"
  if [[ "$cuda" == cuda:* ]]; then
    echo "[AFTP] CUDA detected → trying CUDA wheels"
    _aftp_install_cuda || { echo "[AFTP] CUDA wheels failed → CPU fallback"; _aftp_install_cpu; }
  elif [[ "$rocm" == "rocm" ]]; then
    echo "[AFTP] ROCm detected → trying ROCm wheels"
    _aftp_install_rocm || { echo "[AFTP] ROCm wheels failed → CPU fallback"; _aftp_install_cpu; }
  else
    echo "[AFTP] No GPU stack detected → CPU wheels"
    _aftp_install_cpu
  fi
  if [[ "${AFTP_TORCH_FLAVOR:-cpu}" == cu* ]]; then
    echo "[AFTP] (optional) installing bitsandbytes…"
    python -m pip install --upgrade bitsandbytes || true
  fi
  python - <<'PY'
import torch
print("torch", torch.__version__, "cuda?", torch.cuda.is_available())
if torch.cuda.is_available(): print("device:", torch.cuda.get_device_name(0))
PY
}
