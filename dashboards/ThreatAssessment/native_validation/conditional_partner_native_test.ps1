$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll') | Out-Null
foreach($taskCase in @(@{Name='Multiple';Workspace='AnalysisServicesWorkspace_d02acc13-2a2a-43aa-b89e-9e8b23b0cf68';Count=8},@{Name='Single';Workspace='AnalysisServicesWorkspace_3bb4fe19-d061-4471-bd99-6cb8cb38050c';Count=1})){
 $taskPort=([IO.File]::ReadAllText(('C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces\'+$taskCase.Workspace+'\Data\msmdsrv.port.txt'))).Replace([string][char]0,'').Trim()
 $taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server;$taskServer.Connect('Data Source=localhost:'+$taskPort);$taskDB=$taskServer.Databases[0]
 $taskConn=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection;$taskConn.ConnectionString='Data Source=localhost:'+$taskPort+';Initial Catalog='+$taskDB.ID;$taskConn.Open()
 try{
  $taskCmd=$taskConn.CreateCommand();$taskCmd.CommandText='EVALUATE ROW("Count",[Unreported Indicators],"Block Area",[Partner Block Area],"Guidance",[Partner Panel Guidance],"Highest PRISM",[Highest PRISM])';$taskReader=$taskCmd.ExecuteReader();if(-not $taskReader.Read()){throw 'No native result'}
  $taskCount=[int]$taskReader.GetValue(0);$taskArea=$taskReader.GetValue(1);$taskGuidance=[string]$taskReader.GetValue(2);$taskPrism=$taskReader.GetValue(3);$taskReader.Close()
  if($taskCount -ne $taskCase.Count){throw 'Unexpected row count'}
  if($taskCase.Count -eq 1){if($null -ne $taskArea -and $taskArea -ne [DBNull]::Value){throw 'Single-record filter blocks must be blank'};if($taskGuidance -notmatch 'filtering is off'){throw 'Missing single-record guidance'};if($taskPrism -ne 572){throw 'Single-record PRISM incorrect'}}else{if($taskArea -ne 1){throw 'Multiple-record blocks missing'}}
  Write-Output ($taskCase.Name+': Indicators='+$taskCount+'; Block Area='+$taskArea+'; Highest PRISM='+$taskPrism);Write-Output $taskGuidance
  foreach($taskTable in @('Unreported I&W','Indicator Partners','Snapshot','Reported I&W (5 days)')){$taskCmd.CommandText='EVALUATE '''+$taskTable+'''';$taskReader=$taskCmd.ExecuteReader();while($taskReader.Read()){for($taskIndex=0;$taskIndex -lt $taskReader.FieldCount;$taskIndex++){$taskValue=$taskReader.GetValue($taskIndex)}};$taskReader.Close()}
 }finally{$taskConn.Close();$taskServer.Disconnect()}
}
Write-Output 'Both conditional cases passed native model and table-read tests.'

