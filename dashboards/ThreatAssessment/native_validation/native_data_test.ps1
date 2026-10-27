$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll') | Out-Null
$taskPortFile=Get-ChildItem -LiteralPath 'C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces' -Filter msmdsrv.port.txt -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskPort=([IO.File]::ReadAllText($taskPortFile.FullName)).Replace([string][char]0,'').Trim()
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server
$taskServer.Connect('Data Source=localhost:'+$taskPort)
$taskID='CodexValidation_'+[Guid]::NewGuid().ToString('N')
$taskStream=[IO.File]::OpenRead('\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\native_validation\current.abf')
$taskConnection=$null
try {
 $taskServer.ImageLoad($taskID,$taskID,$taskStream)
 $taskConnection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection
 $taskConnection.ConnectionString='Data Source=localhost:'+$taskPort+';Initial Catalog='+$taskID
 $taskConnection.Open()
 $taskCommand=$taskConnection.CreateCommand()
 $taskCommand.CommandText='EVALUATE ROW("Current Indicators", COUNTROWS(''Unreported I&W''), "Reported Indicators", COUNTROWS(''Reported I&W (5 days)''), "PRISM", [Highest PRISM])'
 $taskReader=$taskCommand.ExecuteReader()
 while($taskReader.Read()){for($i=0;$i -lt $taskReader.FieldCount;$i++){Write-Output ($taskReader.GetName($i)+'='+$taskReader.GetValue($i))}}
 $taskReader.Close()
 Write-Output 'Native model load and DAX data read PASSED.'
} finally {
 if($null -ne $taskConnection){$taskConnection.Close()}
 $taskStream.Dispose();$taskServer.Refresh();$taskDB=$taskServer.Databases.FindByName($taskID)
 if($null -ne $taskDB){$taskDB.Drop()};$taskServer.Disconnect()
}
