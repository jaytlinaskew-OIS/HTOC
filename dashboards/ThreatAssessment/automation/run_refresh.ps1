$ErrorActionPreference = 'Continue'
'Task started: ' + (Get-Date).ToString('o') | Set-Content -LiteralPath 'C:\Users\jaskew\AppData\Local\HTOC\IWDashboard\task-output.log' -Encoding utf8
& 'C:\Users\jaskew\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\automation\refresh_dashboard.py' 2>&1 | Out-File -LiteralPath 'C:\Users\jaskew\AppData\Local\HTOC\IWDashboard\task-output.log' -Encoding utf8 -Append
$taskExit = $LASTEXITCODE
exit $taskExit
