param([string]$Manifest)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = 1
$items = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
foreach ($item in $items) {
  if (-not (Test-Path -LiteralPath $item.path) -or (Get-Item -LiteralPath $item.path).Length -lt 100) {
    $speaker.Rate = if ($null -ne $item.rate) { [int]$item.rate } else { 1 }
    $speaker.SetOutputToWaveFile($item.path)
    $speaker.Speak($item.text)
    $speaker.SetOutputToNull()
  }
}
$speaker.Dispose()
