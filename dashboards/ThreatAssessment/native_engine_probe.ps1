$ErrorActionPreference = 'Stop'
$taskBin='C:\Program Files\Microsoft Power BI Desktop\bin'
[Reflection.Assembly]::LoadFrom((Join-Path $taskBin 'Microsoft.PowerBI.Tabular.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $taskBin 'Microsoft.PowerBI.Tabular.Json.dll')) | Out-Null
$taskPortFile=Get-ChildItem -LiteralPath 'C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces' -Filter msmdsrv.port.txt -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskPort=([IO.File]::ReadAllText($taskPortFile.FullName)).Replace([string][char]0,'').Trim()
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server
$taskServer.Connect('Data Source=localhost:'+$taskPort)
Write-Output ('Native engine connected. Existing databases: '+$taskServer.Databases.Count)
$taskServer.GetType().GetMethods() | Where-Object Name -eq 'ImageLoad' | ForEach-Object { $_.ToString() }
$taskServer.Disconnect()
