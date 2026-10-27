$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll') | Out-Null
$taskPort=([IO.File]::ReadAllText('C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces\AnalysisServicesWorkspace_28da8e91-bb31-4e4f-8c0a-7e1da29363d9\Data\msmdsrv.port.txt')).Replace([string][char]0,'').Trim()
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server
$taskServer.Connect('Data Source=localhost:'+$taskPort)
foreach($taskDB in $taskServer.Databases){
 Write-Output ('Database='+$taskDB.Name)
 $taskConn=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection
 $taskConn.ConnectionString='Data Source=localhost:'+$taskPort+';Initial Catalog='+$taskDB.ID
 $taskConn.Open()
 foreach($taskQuery in @('EVALUATE ROW("Current Indicators",COUNTROWS(''Unreported I&W''),"Reported Indicators",COUNTROWS(''Reported I&W (5 days)''),"PRISM",[Highest PRISM])','EVALUATE ''Unreported I&W''','EVALUATE ''Reported I&W (5 days)''','EVALUATE ''Snapshot''')){
  $taskCmd=$taskConn.CreateCommand();$taskCmd.CommandText=$taskQuery;$taskReader=$taskCmd.ExecuteReader();$taskRows=0
  while($taskReader.Read()){$taskRows++;for($taskIndex=0;$taskIndex -lt $taskReader.FieldCount;$taskIndex++){$taskValue=$taskReader.GetValue($taskIndex);if($taskQuery.StartsWith('EVALUATE ROW')){Write-Output ($taskReader.GetName($taskIndex)+'='+$taskValue)}}}
  $taskReader.Close();Write-Output ('Native query passed; rows='+$taskRows)
 }
 $taskConn.Close()
}
$taskServer.Disconnect()

