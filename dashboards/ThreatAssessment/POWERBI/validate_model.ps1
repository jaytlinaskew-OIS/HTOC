$taskBin = 'C:\Program Files\Microsoft Power BI Desktop\bin'
[System.Reflection.Assembly]::LoadFrom((Join-Path $taskBin 'Microsoft.PowerBI.Tabular.dll')) | Out-Null
[System.Reflection.Assembly]::LoadFrom((Join-Path $taskBin 'Microsoft.PowerBI.Tabular.Json.dll')) | Out-Null
try {
 $taskModelText = Get-Content -LiteralPath '\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\UnreportedIW.SemanticModel\model.bim' -Raw
 $taskModel = [Microsoft.AnalysisServices.Tabular.JsonSerializer]::DeserializeDatabase($taskModelText)
 $taskModel.Model.Tables | Select-Object Name,@{Name='Columns';Expression={$_.Columns.Count}},@{Name='Measures';Expression={$_.Measures.Count}}
} catch { $taskEx = $_.Exception; while($null -ne $taskEx) { Write-Output $taskEx.Message; $taskEx=$taskEx.InnerException }; exit 1 }
