$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
$taskPortFile=Get-ChildItem -LiteralPath 'C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces' -Filter msmdsrv.port.txt -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskPort=([IO.File]::ReadAllText($taskPortFile.FullName)).Replace([string][char]0,'').Trim()
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server
$taskServer.Connect('Data Source=localhost:'+$taskPort)
$taskOriginalIDs=@($taskServer.Databases | ForEach-Object ID)
foreach($taskCase in @('blank_control','current')) {
 $taskID='CodexValidation_'+[Guid]::NewGuid().ToString('N')
 $taskStream=[IO.File]::OpenRead('\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\native_validation\'+$taskCase+'.abf')
 try {
  $taskServer.ImageLoad($taskID,$taskID,$taskStream)
  $taskServer.Refresh()
  $taskDB=$taskServer.Databases.FindByName($taskID)
  Write-Output ($taskCase+': NATIVE LOAD PASSED; tables='+$taskDB.Model.Tables.Count)
 } catch {
  Write-Output ($taskCase+': NATIVE LOAD FAILED')
  $taskEx=$_.Exception;while($null -ne $taskEx){Write-Output $taskEx.Message;$taskEx=$taskEx.InnerException}
 } finally {
  $taskStream.Dispose();$taskServer.Refresh();$taskDB=$taskServer.Databases.FindByName($taskID)
  if($null -ne $taskDB){if($taskOriginalIDs -contains $taskDB.ID){throw 'Refusing to remove an original database'};$taskDB.Drop()}
 }
}
$taskServer.Disconnect()
