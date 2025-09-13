#!/usr/bin/env bash
# Echo one of: cuda | rocm | intel | cpu
if command -v nvidia-smi >/dev/null 2>&1; then echo cuda; exit 0; fi
if command -v rocminfo   >/dev/null 2>&1; then echo rocm; exit 0; fi
# crude Intel hint: oneAPI env or OpenVINO tools
if env | grep -qiE 'ONEAPI|ZE_'; then echo intel; exit 0; fi
if command -v mo >/dev/null 2>&1 || command -v benchmark_app >/dev/null 2>&1; then echo intel; exit 0; fi
echo cpu
