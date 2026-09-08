$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv311\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run Setup-EditDNA.ps1 first.' }
$logRoot = Join-Path $projectRoot 'data\logs'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$processRecord = Join-Path $logRoot 'processes.json'
$processes = @()
if (Test-Path -LiteralPath $processRecord) {
  foreach ($entry in (Get-Content -LiteralPath $processRecord -Raw | ConvertFrom-Json)) {
    $existing = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if ($existing -and $existing.StartTime.ToUniversalTime().ToString('o') -eq $entry.started) { $processes += $entry }
  }
}
foreach ($service in @(@{Port=8765; Name='engine'; File=$pythonPath; Args='-m uvicorn service.main:app --host 127.0.0.1 --port 8765'; Dir=$projectRoot}, @{Port=3000; Name='web'; File=(Get-Command node).Source; Args='node_modules/vinext/dist/cli.js dev --host 127.0.0.1 --port 3000'; Dir=(Join-Path $projectRoot 'web')})) {
  if (-not (Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue)) {
    $process = Start-Process -FilePath $service.File -ArgumentList $service.Args -WorkingDirectory $service.Dir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot "$($service.Name).log") -RedirectStandardError (Join-Path $logRoot "$($service.Name).error.log")
    $processes += @{id=$process.Id; started=$process.StartTime.ToUniversalTime().ToString('o'); name=$service.Name}
  }
}
if ($processes.Count) { ConvertTo-Json -InputObject @($processes) | Set-Content $processRecord }
Write-Host 'EditDNA: http://localhost:3000'
Write-Host 'The local speech model downloads on first transcription. No API key is required.'
