$ErrorActionPreference = 'Stop'
$record = Join-Path $PSScriptRoot 'data\logs\processes.json'
function Stop-OwnedTree([int]$processId) {
  $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $processId" -ErrorAction SilentlyContinue)
  foreach ($child in $children) { Stop-OwnedTree -processId $child.ProcessId }
  $stopping = Get-Process -Id $processId -ErrorAction SilentlyContinue
  if ($stopping) {
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
    $null = $stopping.WaitForExit(5000)
  }
}
if (Test-Path -LiteralPath $record) {
  foreach ($entry in (Get-Content -LiteralPath $record -Raw | ConvertFrom-Json)) {
    $process = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $entry.started) { Stop-OwnedTree -processId $entry.id }
  }
  Remove-Item -LiteralPath $record
}
Write-Host 'Stopped the processes launched by Start-EditDNA.ps1.'
