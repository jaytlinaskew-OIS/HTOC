param([ValidateSet('Start','Pause')][string]$Action='Start')
$ErrorActionPreference='Stop'
$taskApp=$PSScriptRoot
$taskName='HTOC I&W Dashboard - Update Data'
$taskPause=Join-Path $taskApp 'managed-paused.flag'
if($Action -eq 'Start'){
 Remove-Item -LiteralPath $taskPause -ErrorAction SilentlyContinue
 Enable-ScheduledTask -TaskName $taskName | Out-Null
 Start-ScheduledTask -TaskName $taskName
} else {
 'Paused by user' | Set-Content -LiteralPath $taskPause -Encoding UTF8
 Disable-ScheduledTask -TaskName $taskName | Out-Null
 $config=Get-Content -LiteralPath (Join-Path $taskApp 'managed-config.json') -Raw | ConvertFrom-Json
 & (Join-Path $taskApp 'display_window.ps1') -Action Stop -DisplayFile $config.display_file -ProcessState $config.process_state | Out-Null
}
