$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_venv_common.ps1") -Name "tts" -Pip @("pyttsx3")
