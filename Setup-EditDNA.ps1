$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
  if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'Install FFmpeg and add ffmpeg and ffprobe to PATH first.' }
  if (-not (Test-Path '.venv311\Scripts\python.exe')) { py -3.11 -m venv .venv311 }
  & '.\.venv311\Scripts\python' -m pip install -r requirements-lock.txt
  if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
  Push-Location web
  try { npm ci; if ($LASTEXITCODE) { throw 'Web dependency installation failed.' } } finally { Pop-Location }
  & '.\.venv311\Scripts\python' scripts/restore_demo.py
  Write-Host 'Setup complete. Run .\Start-EditDNA.ps1.'
} finally { Pop-Location }
